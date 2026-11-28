"""Transactional admission and recovery; reservations remain charged after failure."""
import contextlib
import json
import sqlite3
import time
import uuid
from .evidence import digest, finite

STAGES = ('static', 'functional', 'formal', 'synthesis', 'placement', 'cts', 'global_route', 'detailed_route', 'extracted')
REQUIRED = {'family', 'mechanism', 'expected_effect', 'falsifier', 'baseline', 'patch_hash',
            'checks', 'cost', 'stage', 'rollback', 'evidence', 'seed', 'config_hash', 'tool_hash'}

def validate(p):
    if set(p) != REQUIRED:
        raise ValueError('Proposal fields mismatch: ' + str(set(p) ^ REQUIRED))
    for key in REQUIRED - {'cost', 'checks', 'evidence', 'seed'}:
        if not isinstance(p[key], str) or not p[key].strip() or len(p[key]) > 4096:
            raise ValueError('Invalid proposal field: ' + key)
    for key in ('baseline','patch_hash','config_hash','tool_hash'):
        if len(p[key]) != 64 or any(c not in '0123456789abcdef' for c in p[key]):
            raise ValueError('Invalid content hash: ' + key)
    if p['stage'] not in STAGES or type(p['seed']) is not int:
        raise ValueError('Invalid stage or seed')
    if not isinstance(p['checks'], list) or not p['checks'] or not all(isinstance(x,str) and x for x in p['checks']):
        raise ValueError('Required checks missing')
    if not isinstance(p['evidence'], list) or not p['evidence'] or not all(isinstance(x,str) and x for x in p['evidence']):
        raise ValueError('Evidence IDs missing')
    if set(p['cost']) != {'wall_s', 'cpu_s', 'disk_bytes', 'remote_minutes', 'agent_tokens', 'full_flows', 'spend_usd'}:
        raise ValueError('Incomplete cost reservation')
    for v in p['cost'].values():
        if finite(v) < 0: raise ValueError('Negative budget')
    if p['cost']['wall_s'] <= 0 or p['cost']['cpu_s'] <= 0:
        raise ValueError('Positive time reservation required')
    return digest({k: p[k] for k in ('baseline','patch_hash','config_hash','tool_hash','seed','stage')})

class Ledger:
    def __init__(self, path):
        self.db = sqlite3.connect(path, timeout=20, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS policy(id INTEGER PRIMARY KEY CHECK(id=1), data TEXT, created REAL);
        CREATE TABLE IF NOT EXISTS experiments(id TEXT PRIMARY KEY, fingerprint TEXT UNIQUE,
          proposal TEXT, state TEXT, backend TEXT, remote_id TEXT, result TEXT, created REAL);
        CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY, experiment TEXT, kind TEXT, data TEXT, at REAL);
        CREATE TABLE IF NOT EXISTS resets(family TEXT PRIMARY KEY, evidence TEXT, reviewer TEXT, at REAL);
        ''')
    @contextlib.contextmanager
    def transaction(self):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            yield
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK')
            raise
    def configure(self, caps=None):
        caps = caps or dict(wall_s=43200, cpu_s=43200, disk_bytes=10_000_000_000,
                            remote_minutes=720, agent_tokens=100000, full_flows=2, spend_usd=5, concurrency=1)
        expected = {'wall_s','cpu_s','disk_bytes','remote_minutes','agent_tokens','full_flows','spend_usd','concurrency'}
        if set(caps) != expected or any(finite(v) <= 0 for v in caps.values()):
            raise ValueError('Invalid caps')
        with self.transaction():
            self.db.execute('INSERT OR IGNORE INTO policy VALUES(1,?,?)', (json.dumps(caps),time.time()))
            if json.loads(self.db.execute('SELECT data FROM policy').fetchone()[0]) != caps:
                raise ValueError('Campaign budget immutable; create a new campaign')
    def event(self, eid, kind, data):
        self.db.execute('INSERT INTO events(experiment,kind,data,at) VALUES(?,?,?,?)',
                        (eid, kind, json.dumps(data), time.time()))
    def rows(self):
        return [dict(r) for r in self.db.execute('SELECT * FROM experiments ORDER BY created')]
    def reserve(self, proposal, backend='mock', expensive=False):
        fingerprint = validate(proposal)
        if backend not in ('mock','github','cloud','native'):
            raise ValueError('Unknown backend')
        with self.transaction():
            policy = self.db.execute('SELECT * FROM policy').fetchone()
            if policy is None: raise ValueError('Configure campaign first')
            caps = json.loads(policy['data'])
            if time.time()-policy['created'] > caps['wall_s']:
                raise ValueError('Campaign elapsed budget exhausted')
            rows = self.rows()
            if any(r['fingerprint']==fingerprint for r in rows): raise ValueError('Duplicate fingerprint')
            if sum(r['state'] in ('queued','submitting','running') for r in rows) >= caps['concurrency']:
                raise ValueError('Concurrency exhausted')
            failures = []
            reset = self.db.execute('SELECT at FROM resets WHERE family=?',(proposal['family'],)).fetchone()
            for r in rows:
                p = json.loads(r['proposal'])
                if r['state'] in ('failed','abandoned') and p['family']==proposal['family'] and (not reset or r['created']>reset[0]):
                    failures.append(p)
            if len(failures)>=3: raise ValueError('Family blocked; independent review and explicit reset required')
            if sum(p['mechanism']==proposal['mechanism'] for p in failures)>=2:
                raise ValueError('Mechanism stagnated; re-diagnose with a different mechanism')
            if proposal['cost']['full_flows'] and not expensive:
                raise ValueError('Expensive experiment opt-in required')
            for k, v in proposal['cost'].items():
                used = sum(json.loads(r['proposal'])['cost'][k] for r in rows)
                if used + v > caps[k]: raise ValueError('Budget exhausted: '+k)
            eid = str(uuid.uuid4())
            self.db.execute('INSERT INTO experiments VALUES(?,?,?,?,?,?,?,?)',
                            (eid,fingerprint,json.dumps(proposal),'queued',backend,None,None,time.time()))
            self.event(eid,'reserved',proposal['cost'])
            return eid
    def transition(self, eid, target, remote_id=None, result=None):
        allowed = {'queued': {'submitting','abandoned'}, 'submitting': {'running','failed','abandoned'},
                   'running': {'completed','failed','abandoned'}, 'completed':set(), 'failed':set(), 'abandoned':set()}
        with self.transaction():
            row = self.db.execute('SELECT * FROM experiments WHERE id=?',(eid,)).fetchone()
            if row is None or target not in allowed[row['state']]: raise ValueError('Illegal state transition')
            if target=='completed' and (not result or result.get('status')!='pass' or not result.get('evidence')):
                raise ValueError('Missing validated result')
            if remote_id and row['remote_id'] and remote_id != row['remote_id']:
                raise ValueError('Remote identity is immutable')
            self.db.execute('UPDATE experiments SET state=?,remote_id=COALESCE(?,remote_id),result=? WHERE id=?',
                            (target,remote_id,json.dumps(result),eid))
            self.event(eid,target,{'remote_id':remote_id,'result':result})
    def reset_family(self, family, evidence, reviewer):
        if not evidence or not reviewer: raise ValueError('Independent review required')
        with self.transaction():
            self.db.execute('INSERT OR REPLACE INTO resets VALUES(?,?,?,?)',(family,json.dumps(evidence),reviewer,time.time()))
            self.event(None,'family-reset',{'family':family,'evidence':evidence,'reviewer':reviewer})
    def prepare_dispatch(self, eid, plan):
        with self.transaction():
            row=self.db.execute('SELECT state FROM experiments WHERE id=?',(eid,)).fetchone()
            if not row or row[0]!='queued':raise ValueError('Dispatch intent already recorded')
            self.db.execute("UPDATE experiments SET state='submitting' WHERE id=?",(eid,))
            self.event(eid,'dispatch-plan',plan)
    def recovery(self):
        # A crash between remote submission and receipt is deliberately NOT retried.
        return [{'id':r['id'],'action': 'reconcile_by_token_do_not_resubmit' if r['state']=='submitting'
                 else 'poll' if r['state']=='running' else 'dispatch', 'remote_id':r['remote_id']}
                for r in self.rows() if r['state'] in ('queued','submitting','running')]
