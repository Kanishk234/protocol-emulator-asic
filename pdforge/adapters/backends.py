"""Backend-independent asynchronous contracts. No live dispatch in this release."""
import json
from pathlib import Path
import re
import subprocess
import zipfile
from pdforge.core.evidence import digest, inside, sha, pins, finite

class MockBackend:
    def __init__(self, receipts=None): self.receipts = receipts or {}
    def plan(self, experiment):
        return {'backend':'mock','token':experiment['fingerprint'],'network':False}
    def submit(self, experiment): return 'mock-'+experiment['fingerprint']
    def poll(self, remote_id):
        return self.receipts.get(remote_id, {'status':'in_progress'})

class GitHubBackend:
    def __init__(self, repository, workflow='status-merge-screen.yaml'):
        if not re.fullmatch(r'[\w.-]+/[\w.-]+', repository): raise ValueError('Invalid repository')
        if workflow not in ('status-merge-screen.yaml','gds.yaml'): raise ValueError('Unreviewed workflow')
        self.repository, self.workflow = repository, workflow
    def plan(self, experiment):
        return {'backend':'github','repository':self.repository,'workflow':self.workflow,
                'token':experiment['fingerprint'], 'dispatch_enabled':False,
                'required': ['explicit resource authorization','published exact source revision',
                             'workflow correlation token support or independent run ID receipt'],
                'artifact_contract': ['trial_inputs.json','engine.json','screen_result.json',
                                      'final/metrics.json','corner reports'],
                'warning':'Existing workflow cannot guarantee exactly-once dispatch; never blindly retry'}
    def submit(self, experiment):
        raise PermissionError('Live dispatch disabled; implement reviewed authorization/correlation bridge first')
    def poll(self, remote_id):
        if not str(remote_id).isdigit(): raise ValueError('Invalid run ID')
        # Read-only API, no shell, no dispatch, no artifact upload.
        cmd = ['gh','api',f'repos/{self.repository}/actions/runs/{remote_id}']
        return normalize_github(json.loads(subprocess.check_output(cmd, text=True, timeout=30)))

class CloudBackend:
    def plan(self, experiment):
        return {'backend':'cloud','token':experiment['fingerprint'],'dispatch_enabled':False,
                'required':['provider adapter','idempotency key','immutable image','isolated inputs','resource authorization']}
    def submit(self, experiment): raise PermissionError('Provider not configured')
    def poll(self, remote_id): raise ValueError('Cloud provider unavailable; supply offline receipt')

class NativeBackend:
    def plan(self, experiment):
        return {'backend':'native','dispatch_enabled':False,
                'required':['pinned EDA toolchain','filesystem and network sandbox','reviewed command allowlist'],
                'checkpoint_key':checkpoint_key(json.loads(experiment['proposal']))}
    def submit(self, experiment): raise PermissionError('Native execution not qualified')
    def poll(self, remote_id): raise ValueError('Native execution unavailable')

def normalize_github(receipt):
    required = ('id','head_sha','status','conclusion','workflow_id','run_attempt')
    if any(k not in receipt for k in required): raise ValueError('Incomplete GitHub receipt')
    if receipt['status'] not in ('queued','in_progress','completed','waiting','requested','pending'):
        raise ValueError('Unknown run status')
    return {'remote_id':str(receipt['id']),'revision':receipt['head_sha'],
            'status':receipt['status'],'conclusion':receipt['conclusion'],
            'attempt':receipt['run_attempt'],'workflow_id':receipt['workflow_id'],
            'evidence':digest(receipt), 'physical_qualified':False}

def reconcile(ledger, eid, receipt, expected_revision):
    r = normalize_github(receipt)
    row = next(x for x in ledger.rows() if x['id']==eid)
    if r['revision'] != expected_revision or not re.fullmatch(r'[0-9a-f]{40}',expected_revision):
        raise ValueError('Remote source revision mismatch')
    if row['remote_id'] and row['remote_id'] != r['remote_id']: raise ValueError('Wrong run')
    if row['state']=='submitting': ledger.transition(eid,'running',remote_id=r['remote_id'])
    if r['status']=='completed':
        # Even GitHub success is incomplete until exact artifact provenance and checks are validated.
        if r['conclusion']=='success':
            ledger.event(eid,'awaiting-artifact-validation',r)
        else:
            ledger.transition(eid,'failed',result={'status':'fail','receipt':r})
    return r

def extract_zip(archive, destination, max_bytes=1_000_000_000):
    dest = Path(destination)
    if dest.exists(): raise ValueError('Artifact destination must be new')
    with zipfile.ZipFile(archive) as z:
        entries = z.infolist()
        names = [i.filename for i in entries]
        if len(names)!=len(set(names)) or sum(i.file_size for i in entries)>max_bytes:
            raise ValueError('Duplicate or oversized archive')
        for i in entries:
            inside(dest, i.filename.rstrip('/'))
            if (i.external_attr>>16)&0o170000 == 0o120000: raise ValueError('Archive symlink')
        dest.mkdir(parents=True)
        for i in entries:
            target = inside(dest,i.filename.rstrip('/'))
            if i.is_dir(): target.mkdir(parents=True,exist_ok=True)
            else:
                target.parent.mkdir(parents=True,exist_ok=True)
                with z.open(i) as source, target.open('xb') as out:
                    remaining = max_bytes
                    while chunk := source.read(min(1024*1024, remaining+1)):
                        remaining -= len(chunk)
                        if remaining < 0: raise ValueError('Decompressed byte limit')
                        out.write(chunk)
    return {'archive_sha256':sha(archive),'files':{n:sha(inside(dest,n)) for n in names if not n.endswith('/')}}

def checkpoint_key(proposal, upstream=None):
    if upstream is None: return {'reusable':False,'reason':'Missing upstream state/tool/SDC/corner manifest'}
    required = {'input_hash','config_hash','tool_hash','pdk_hash','sdc_hash','corners','seed','state_hash','stage'}
    if set(upstream)!=required: raise ValueError('Incomplete checkpoint dependencies')
    return {'key':digest(upstream),'reusable':False,'reason':'Clean/resumed equivalence must be validated'}

def verify_bundle(root, expected_inputs):
    root = Path(root)
    trial = json.loads((root/'trial_inputs.json').read_text())
    engine = json.loads((root/'engine.json').read_text())
    pin = pins()
    for key, expected in {'tools':pin['TOOLS'],'pdk':pin['PDK'],'image_digest':pin['IMAGE_DIGEST'],
                          'openroad':pin['OPENROAD'],'librelane':'3.1.0.dev4'}.items():
        if engine.get(key)!=expected: raise ValueError('Engine mismatch: '+key)
    if not expected_inputs or trial.get('candidate_inputs') != expected_inputs:
        raise ValueError('Candidate provenance mismatch')
    for name, expected in expected_inputs.items():
        if sha(inside(root,name))!=expected: raise ValueError('Changed artifact input: '+name)
    return {'provenance_valid':True,'physical_qualified':False,
            'evidence':{'trial':sha(root/'trial_inputs.json'),'engine':sha(root/'engine.json')},
            'remaining':['functional/formal evidence','all-corner stage checks','official qualification']}
