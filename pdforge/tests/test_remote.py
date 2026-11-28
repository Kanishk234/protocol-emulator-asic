from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from pdforge.core.ledger import Ledger
from pdforge.core.evidence import sha
from pdforge.benchmarks.replay import proposal
from pdforge.adapters.github import GitHubValidation,dispatch,resume,validate_result

class RemoteTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.l=Ledger(self.root/'ledger.sqlite');self.l.configure();self.addCleanup(self.l.db.close)
        self.p=proposal();self.p['stage']='static';self.p['cost'].update(remote_minutes=5,wall_s=300,spend_usd=.1)
        self.eid=self.l.reserve(self.p,'github');self.posts=0;self.runs=[]
        self.bridge=GitHubValidation(self.transport)
    def transport(self,method,path,data=None):
        if '/commits/' in path:return {'sha':'a'*40}
        if method=='POST':self.posts+=1;return None
        if '/workflows/' in path:return {'workflow_runs':self.runs}
        return self.runs[0]
    def run_receipt(self,conclusion='success'):
        row=self.l.rows()[0]
        return dict(id=123,head_sha='a'*40,head_branch='autonomous-pd',status='completed',
                    conclusion=conclusion,workflow_id=1,run_attempt=1,path='.github/workflows/repo-audit.yaml',
                    display_title='PDForge '+row['fingerprint'])
    def test_authorization_required(self):
        with self.assertRaises(PermissionError):dispatch(self.l,self.eid,'autonomous-pd','a'*40,bridge=self.bridge)
        self.assertEqual(self.posts,0)
    def test_unknown_submission_resumes_without_double_dispatch(self):
        dispatch(self.l,self.eid,'autonomous-pd','a'*40,authorized=True,bridge=self.bridge)
        self.assertEqual(resume(self.l,self.eid,self.bridge)['state'],'submitting')
        self.runs=[self.run_receipt()]
        resume(self.l,self.eid,self.bridge)
        self.assertEqual(self.l.rows()[0]['state'],'running');self.assertEqual(self.posts,1)
        with self.assertRaises(ValueError):dispatch(self.l,self.eid,'autonomous-pd','a'*40,authorized=True,bridge=self.bridge)
    def test_owned_cancel_only(self):
        self.runs=[self.run_receipt()]
        plan=self.bridge.plan('autonomous-pd','a'*40,self.l.rows()[0]['fingerprint'])
        self.runs[0]['head_branch']='friend'
        with self.assertRaises(ValueError):self.bridge.cancel('123',plan)
        self.assertEqual(self.posts,0)
    def test_forbidden_branch_and_revision(self):
        for b in ('main','efpga','friend/x','pdforge/../main'):
            with self.assertRaises(ValueError):self.bridge.plan(b,'a'*40,'b'*64)
        with self.assertRaises(ValueError):dispatch(self.l,self.eid,'autonomous-pd','c'*40,authorized=True,bridge=self.bridge)
        self.assertEqual(self.posts,0)
        self.assertEqual(self.l.rows()[0]['state'],'submitting')
    def test_ambiguous_discovery(self):
        self.runs=[self.run_receipt(),self.run_receipt()]
        with self.assertRaises(ValueError):self.bridge.discover(self.bridge.plan('autonomous-pd','a'*40,self.l.rows()[0]['fingerprint']))
    def test_remote_failure(self):
        self.runs=[self.run_receipt('failure')]
        dispatch(self.l,self.eid,'autonomous-pd','a'*40,authorized=True,bridge=self.bridge)
        resume(self.l,self.eid,self.bridge)
        self.assertEqual(self.l.rows()[0]['state'],'failed')
    def test_artifact_identity_and_completion(self):
        self.runs=[self.run_receipt()]
        dispatch(self.l,self.eid,'autonomous-pd','a'*40,authorized=True,bridge=self.bridge)
        resume(self.l,self.eid,self.bridge)
        for name in ['tests.txt','benchmark.json']:(self.root/name).write_text('fixture')
        r=dict(revision='a'*40,run_id='123',attempt='1',token=self.l.rows()[0]['fingerprint'],tests_passed=True,
               tests_run=30,test_failures=0,test_errors=0,physical_qualified=False,
               files={name:sha(self.root/name) for name in ['tests.txt','benchmark.json']})
        (self.root/'result.json').write_text(json.dumps(r))
        self.assertFalse(validate_result(self.l,self.eid,self.root)['physical_qualified'])
        self.assertEqual(self.l.rows()[0]['state'],'completed')
