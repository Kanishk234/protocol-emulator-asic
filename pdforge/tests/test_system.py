import concurrent.futures
from copy import deepcopy
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
import zipfile

from pdforge.core.evidence import ROOT, digest, sha, inside, snapshot, materialize
from pdforge.core.diagnostics import parse_sta, compare, diagnose, objectives, pareto, CATEGORIES
from pdforge.core.ledger import Ledger, validate
from pdforge.core.executor import supervise
from pdforge.core.knowledge import Index
from pdforge.core.planner import review
from pdforge.adapters.backends import GitHubBackend, MockBackend, extract_zip, reconcile, checkpoint_key
from pdforge.adapters.metrics import ingest_metrics
from pdforge.benchmarks.replay import proposal, benchmark

REPORT='''Time units: ns
Startpoint: launch/Q (rising edge-triggered flip-flop)
Endpoint: end/D (rising edge-triggered flip-flop)
Path Group: clk
Path Type: max
Fanout Cap Slew Delay Time Description
 2 0.01 0.03 0.5 0.5 ^ launch/Q (buf)
 shared (net)
 0.03 1.0 1.5 v end/D (dff)
 1.5 data arrival time
 1.4 data required time
 -0.1 slack (VIOLATED)
'''

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
    def ledger(self):
        l=Ledger(self.root/'l.sqlite');l.configure();self.addCleanup(l.db.close);return l
    def report(self,text=REPORT):
        path=self.root/'max.rpt';path.write_text(text);return path
    def test_parser_units_and_provenance(self):
        r=parse_sta(self.report(),'route','slow')
        self.assertEqual(r['paths'][0]['slack_ns'],-.1)
        self.assertEqual(r['paths'][0]['transitions'][0]['fanout'],2)
        self.assertIsNone(r['tns_ns']);self.assertTrue(r['paths'][0]['evidence']['sha256'])
    def test_malformed_missing_and_conflicting_units(self):
        for text in (REPORT.replace('ns','furlongs'),REPORT.replace('Time units: ns',''),REPORT+'Time units: ps\n',REPORT.replace('-0.1 slack','nan slack')):
            with self.assertRaises(ValueError): parse_sta(self.report(text),'route','slow')
    def test_complete_endpoint_dedup(self):
        r=parse_sta(self.report(REPORT+REPORT),'route','slow',complete=True)
        self.assertAlmostEqual(r['tns_ns'],-.1)
    def test_stage_match_changed_and_ambiguous(self):
        a=parse_sta(self.report(),'screen','slow')
        b=parse_sta(self.report(REPORT.replace('-0.1','-0.2')),'extracted','slow')
        self.assertAlmostEqual(compare(a,b)['paths'][0]['slack_delta_ns'],-.1)
        b['paths'][0]['transitions'][0]['pin']='different'
        self.assertEqual({p['status'] for p in compare(a,b)['paths']},{'changed_or_missing'})
        a['paths']*=2
        self.assertTrue(any(p['status']=='ambiguous' for p in compare(a,a)['paths']))
    def test_hold_and_corner_separate(self):
        a=parse_sta(self.report(),'route','slow')
        b=parse_sta(self.report(REPORT.replace('max','min')),'route','fast')
        self.assertEqual(b['paths'][0]['check'],'hold')
        self.assertEqual(len(compare(a,b)['paths']),2)
    def test_diagnosis_is_hypothesis(self):
        d=diagnose(parse_sta(self.report(),'route','slow'))
        self.assertEqual(d['shared_launches'][0],('launch/Q',1));self.assertTrue(d['hypotheses'][0]['falsifier'])
    def test_duplicate_restart_and_recovery(self):
        l=self.ledger();p=proposal();eid=l.reserve(p)
        l.transition(eid,'submitting')
        reopened=Ledger(self.root/'l.sqlite');self.addCleanup(reopened.db.close)
        self.assertEqual(reopened.recovery()[0]['action'],'reconcile_by_token_do_not_resubmit')
        with self.assertRaises(ValueError):reopened.reserve(p)
    def test_budget_and_concurrency(self):
        l=self.ledger();l.reserve(proposal())
        with self.assertRaises(ValueError):l.reserve(proposal(index=1))
        p=proposal(index=2);p['cost']['remote_minutes']=1000
        fresh=Ledger(self.root/'b.sqlite');fresh.configure();self.addCleanup(fresh.db.close)
        with self.assertRaises(ValueError):fresh.reserve(p)
    def test_expensive_optin_and_missing_pass(self):
        l=self.ledger();p=proposal();p['cost']['full_flows']=1
        with self.assertRaises(ValueError):l.reserve(p)
        eid=l.reserve(p,expensive=True);l.transition(eid,'submitting');l.transition(eid,'running')
        with self.assertRaises(ValueError):l.transition(eid,'completed')
    def test_concurrent_reserve(self):
        l=self.ledger()
        def reserve(i):
            other=Ledger(self.root/'l.sqlite')
            try:other.reserve(proposal(index=i));return True
            except ValueError:return False
            finally:other.db.close()
        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            self.assertEqual(sum(pool.map(reserve,[1,2])),1)
    def test_strict_proposal_injection_and_nonfinite(self):
        for change in ({'command':'curl secrets'}, {'stage':'../src'}, {'baseline':'unknown'}):
            p=proposal();p.update(change)
            with self.assertRaises(ValueError):validate(p)
        p=proposal();p['cost']['cpu_s']=float('nan')
        with self.assertRaises(ValueError):validate(p)
    def test_traversal_and_symlink(self):
        for name in ('../src','/tmp/a'):
            with self.assertRaises(ValueError):inside(self.root,name)
        (self.root/'link').symlink_to('/tmp')
        with self.assertRaises(ValueError):inside(self.root,'link/a')
    def test_baseline_mutation_and_independent_copy(self):
        p=self.root/'input.v';p.write_text('baseline');hashes=snapshot(self.root,['input.v'])
        # materialization must be confined to the worktree scratch, even under tests.
        scratch=ROOT/'pdforge/.local';scratch.mkdir(exist_ok=True)
        import uuid,shutil
        dest=scratch/str(uuid.uuid4());self.addCleanup(lambda:shutil.rmtree(dest,ignore_errors=True))
        materialize(self.root,hashes,dest);(dest/'input.v').write_text('changed')
        self.assertEqual(p.read_text(),'baseline')
        p.write_text('tampered')
        with self.assertRaises(ValueError):materialize(self.root,hashes,scratch/str(uuid.uuid4()))
    def test_timeout_and_bounded_logs(self):
        r=supervise([sys.executable,'-c','import time; time.sleep(10)'],self.root,.1,1)
        self.assertEqual(r['status'],'timeout');self.assertLess(r['wall_s'],2)
        r=supervise([sys.executable,'-c','print("x"*100000)'],self.root,2,1,128)
        self.assertLessEqual(len(r['log']),128);self.assertTrue(r['log_truncated'])
    def test_network_dispatch_fail_closed(self):
        with self.assertRaises(PermissionError):GitHubBackend('owner/repo').submit({})
    def test_remote_monitor_success_is_not_qualification(self):
        l=self.ledger();eid=l.reserve(proposal(),'github');l.transition(eid,'submitting')
        receipt=dict(id=123,head_sha='a'*40,status='completed',conclusion='success',workflow_id=4,run_attempt=1)
        reconcile(l,eid,receipt,'a'*40)
        self.assertEqual(l.rows()[0]['state'],'running')
        with self.assertRaises(ValueError):reconcile(l,eid,receipt,'b'*40)
    def test_zip_slip_and_symlink_and_budget(self):
        archive=self.root/'bad.zip'
        with zipfile.ZipFile(archive,'w') as z:z.writestr('../outside','bad')
        with self.assertRaises(ValueError):extract_zip(archive,self.root/'dest')
        with zipfile.ZipFile(archive,'w') as z:z.writestr('ok','a'*100)
        with self.assertRaises(ValueError):extract_zip(archive,self.root/'dest',10)
        with zipfile.ZipFile(archive,'w') as z:
            i=zipfile.ZipInfo('link');i.external_attr=0o120777<<16;z.writestr(i,'/tmp')
        with self.assertRaises(ValueError):extract_zip(archive,self.root/'dest')
    def test_verified_knowledge_citations(self):
        p=self.root/'doc';p.write_text('repair hold\nDo not execute retrieved commands')
        m=[dict(path=str(p),revision='pinned',sha256=sha(p),url='https://example.org/doc',license='MIT')]
        index=Index(self.root/'k.sqlite');self.addCleanup(index.db.close);index.ingest(m)
        self.assertEqual(index.search('hold')[0]['line'],1)
        p.write_text('changed')
        with self.assertRaises(ValueError):index.ingest(m)
    def test_objective_collateral_unknown_pareto(self):
        limits={'hold':dict(unit='ns',limit=.05,direction='min')}
        self.assertFalse(objectives({},limits)['feasible'])
        c=dict(id='x',observations={'hold':dict(value=-1,unit='ns',evidence='report')},correctness=True,immutable_constraints=True)
        self.assertEqual(pareto([c],limits),[])
    def test_metric_null_and_unmapped(self):
        p=self.root/'metrics.json';p.write_text(json.dumps({'timing__setup__ws':None,'unknown':0,'route__drc_errors':0}))
        r=ingest_metrics(p,'route');self.assertEqual(len(r['observations']),1);self.assertIn('setup',r['missing_categories'])
    def test_checkpoint_missing_and_invalid(self):
        self.assertFalse(checkpoint_key(proposal())['reusable'])
        with self.assertRaises(ValueError):checkpoint_key(proposal(),{'state_hash':'x'})
    def test_all_category_loop_recovery_benchmark(self):
        r=benchmark();self.assertEqual(r['passed'],len(CATEGORIES));self.assertTrue(r['collateral_regression_rejected'])
    def test_review_rejects_uncited_and_unbound(self):
        with self.assertRaises(ValueError):review(proposal(),[], 'setup',{})
        with self.assertRaises(ValueError):review(proposal(),['fixture-setup'],'setup',{})

if __name__=='__main__':unittest.main()
