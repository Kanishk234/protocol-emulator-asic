"""Reviewed GitHub Actions bridge: PDForge validation only, token-correlated runs.
No production GDS dispatch, branch publishing, remote settings or arbitrary workflows.
"""
import json
from pathlib import Path
import re
import subprocess
from pdforge.core.evidence import digest, sha
from pdforge.adapters.backends import normalize_github, extract_zip

REPOSITORY='Kanishk234/protocol-emulator-asic'
WORKFLOW='repo-audit.yaml'

class GitHubValidation:
    def __init__(self, transport=None): self.transport=transport or self._gh
    @staticmethod
    def _gh(method, endpoint, data=None):
        args=['gh','api','--method',method,endpoint]
        if data is not None:args+=['--input','-']
        p=subprocess.run(args,input=json.dumps(data) if data is not None else None,
                         text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
        if p.returncode:raise OSError(p.stderr.strip())
        return json.loads(p.stdout) if p.stdout.strip() else None
    def plan(self, branch, revision, token):
        if branch!='autonomous-pd' and not re.fullmatch(r'pdforge/[A-Za-z0-9._-]+',branch):
            raise ValueError('Unauthorized branch')
        if not re.fullmatch('[0-9a-f]{40}',revision) or not re.fullmatch('[0-9a-f]{64}',token):
            raise ValueError('Invalid revision or experiment token')
        return {'repository':REPOSITORY,'workflow':WORKFLOW,'branch':branch,'revision':revision,
                'token':token,'run_name':'PDForge '+token,'full_flows':0,
                'job_timeout_minutes':5,'concurrency':1,'official_signoff':False}
    def dispatch(self, plan):
        # Bind branch head just before submission. Discover by SHA again after submission.
        head=self.transport('GET',f'repos/{REPOSITORY}/commits/{plan["branch"]}')
        if head['sha']!=plan['revision']:raise ValueError('Published branch moved')
        self.transport('POST',f'repos/{REPOSITORY}/actions/workflows/{WORKFLOW}/dispatches',
                       {'ref':plan['branch'],'inputs':{'pdforge_token':plan['token']}})
    def discover(self, plan):
        response=self.transport('GET',f'repos/{REPOSITORY}/actions/workflows/{WORKFLOW}/runs?branch={plan["branch"]}&event=workflow_dispatch&per_page=100')
        runs=[r for r in response['workflow_runs'] if r['display_title']==plan['run_name'] and r['head_sha']==plan['revision']]
        if len(runs)>1:raise ValueError('Ambiguous token; never dispatch again')
        return runs[0] if runs else None
    def poll(self, run_id, plan):
        if not str(run_id).isdigit():raise ValueError('Invalid run ID')
        r=self.transport('GET',f'repos/{REPOSITORY}/actions/runs/{run_id}')
        if r['head_branch']!=plan['branch'] or r['head_sha']!=plan['revision'] or r['display_title']!=plan['run_name']:
            raise ValueError('Remote ownership mismatch')
        if r.get('path') != '.github/workflows/'+WORKFLOW:raise ValueError('Workflow mismatch')
        return r
    def artifacts(self, run_id):
        if not str(run_id).isdigit():raise ValueError('Invalid run ID')
        return self.transport('GET',f'repos/{REPOSITORY}/actions/runs/{run_id}/artifacts')['artifacts']
    def cancel(self, run_id, plan):
        self.poll(run_id,plan) # Fail closed unless exact owned run.
        self.transport('POST',f'repos/{REPOSITORY}/actions/runs/{run_id}/cancel')


def dispatch(ledger, eid, branch, revision, *, authorized=False, bridge=None):
    if not authorized:raise PermissionError('Explicit remote resource authorization required')
    row=next(r for r in ledger.rows() if r['id']==eid)
    if row['backend']!='github' or row['state']!='queued':raise ValueError('Not dispatchable; use resume to reconcile')
    p=json.loads(row['proposal'])
    if p['stage']!='static' or p['cost']['remote_minutes']<5 or p['cost']['wall_s']<300 or p['cost']['spend_usd']<.1 or p['cost']['full_flows']:
        raise ValueError('Only budgeted inexpensive validation is enabled')
    bridge=bridge or GitHubValidation();plan=bridge.plan(branch,revision,row['fingerprint'])
    # Intent committed BEFORE POST. An uncertain response stays submitting forever until reconciled.
    ledger.prepare_dispatch(eid,plan)
    bridge.dispatch(plan)
    r=bridge.discover(plan)
    if r:ledger.transition(eid,'running',remote_id=str(r['id']))
    return plan

def resume(ledger,eid,bridge=None):
    bridge=bridge or GitHubValidation()
    row=next(r for r in ledger.rows() if r['id']==eid)
    event=ledger.db.execute("SELECT data FROM events WHERE experiment=? AND kind='dispatch-plan' ORDER BY seq DESC LIMIT 1",(eid,)).fetchone()
    if not event:raise ValueError('No dispatch plan')
    plan=json.loads(event[0])
    if row['state']=='submitting':
        r=bridge.discover(plan)
        if r:ledger.transition(eid,'running',remote_id=str(r['id']))
        else:return {'state':'submitting','action':'await correlation; do not resubmit'}
    elif row['state']=='running':r=bridge.poll(row['remote_id'],plan)
    else:return {'state':row['state']}
    norm=normalize_github(r);ledger.event(eid,'remote-poll',norm)
    if norm['status']=='completed' and norm['conclusion']!='success':
        ledger.transition(eid,'failed',result={'status':'fail','remote':norm})
    return {'state':norm['status'],'receipt':r,'artifact_validation_required':True}

def validate_result(ledger,eid,directory):
    row=next(r for r in ledger.rows() if r['id']==eid)
    event=ledger.db.execute("SELECT data FROM events WHERE experiment=? AND kind='dispatch-plan'",(eid,)).fetchone()
    if row['state']!='running' or not event:raise ValueError('Experiment not awaiting artifacts')
    poll=ledger.db.execute("SELECT data FROM events WHERE experiment=? AND kind='remote-poll' ORDER BY seq DESC LIMIT 1",(eid,)).fetchone()
    if not poll:raise ValueError('Missing terminal remote receipt')
    remote=json.loads(poll[0])
    if remote['status']!='completed' or remote['conclusion']!='success':raise ValueError('Remote validation not successful')
    plan=json.loads(event[0]);root=Path(directory)
    receipt=json.loads((root/'result.json').read_text())
    expected={'revision':plan['revision'],'run_id':row['remote_id'],'token':plan['token']}
    if any(str(receipt.get(k))!=str(v) for k,v in expected.items()):raise ValueError('Artifact identity mismatch')
    if receipt.get('attempt') != str(remote['attempt']):raise ValueError('Artifact attempt mismatch')
    if receipt.get('tests_passed') is not True or receipt.get('tests_run',0)<23 or receipt.get('test_failures')!=0 or receipt.get('test_errors')!=0:
        raise ValueError('Test evidence incomplete')
    if receipt.get('physical_qualified') is not False:raise ValueError('Validation cannot claim physical qualification')
    if set(receipt.get('files',{}))!={'tests.txt','benchmark.json'}:raise ValueError('Missing evidence files')
    for name,h in receipt['files'].items():
        from pdforge.core.evidence import inside
        if sha(inside(root,name))!=h:raise ValueError('Artifact hash mismatch')
    result={'status':'pass','scope':'PDForge infrastructure validation only','evidence':sha(root/'result.json'),
            'tests_run':receipt['tests_run'],'physical_qualified':False}
    ledger.transition(eid,'completed',result=result)
    return result

def download_artifact(metadata, destination, max_bytes=500_000_000):
    """Bounded authenticated read; bytes must match GitHub's artifact digest."""
    from pdforge.core.evidence import ROOT
    import os
    import signal
    artifact_id=metadata.get('id')
    if type(artifact_id) is not int or artifact_id<=0:raise ValueError('Invalid artifact ID')
    if metadata.get('expired') or metadata.get('size_in_bytes',max_bytes+1)>max_bytes:
        raise ValueError('Artifact expired or exceeds download budget')
    expected=metadata.get('digest','')
    if not re.fullmatch(r'sha256:[0-9a-f]{64}',expected):raise ValueError('Missing archive digest')
    dest=Path(destination).resolve()
    if not dest.is_relative_to(ROOT/'pdforge/.local') or dest.exists():raise ValueError('Unsafe/existing download destination')
    dest.parent.mkdir(parents=True,exist_ok=True)
    # Child file-size limit bounds a dishonest response, including any redirects.
    import resource
    def limits():resource.setrlimit(resource.RLIMIT_FSIZE,(max_bytes,max_bytes))
    with dest.open('xb') as out:
        p=subprocess.Popen(['gh','api',f'repos/{REPOSITORY}/actions/artifacts/{artifact_id}/zip'],
                           stdout=out,stderr=subprocess.PIPE,start_new_session=True,preexec_fn=limits)
        try:_,err=p.communicate(timeout=120)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid,signal.SIGKILL);p.communicate();raise ValueError('Artifact download timeout')
    if p.returncode:raise OSError(err.decode(errors='replace'))
    if sha(dest)!=expected.split(':',1)[1]:raise ValueError('Artifact digest mismatch')
    return {'path':str(dest),'sha256':sha(dest),'metadata':metadata}
