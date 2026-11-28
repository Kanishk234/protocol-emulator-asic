"""Synthetic policy benchmark, with no invented physical closure measurements."""
from copy import deepcopy
from pathlib import Path
import tempfile
from pdforge.core.ledger import Ledger
from pdforge.core.diagnostics import CATEGORIES, INTERACTIONS, objectives
from pdforge.core.evidence import digest

def proposal(category='setup', index=0, mechanism='repair'):
    return dict(family=category,mechanism=mechanism,expected_effect='Reduce '+category,
                falsifier='Primary violation unchanged or collateral regression',
                baseline='0'*64,patch_hash=digest(index),checks=['correctness',category,*INTERACTIONS[category]],
                cost=dict(wall_s=1,cpu_s=1,disk_bytes=1,remote_minutes=1,agent_tokens=1,full_flows=0,spend_usd=.01),
                stage='global_route',rollback='Discard isolated experiment',evidence=['fixture-'+category],
                seed=index,config_hash='1'*64,tool_hash='2'*64)

def benchmark():
    outcomes = []
    for category in CATEGORIES:
        with tempfile.TemporaryDirectory() as d:
            ledger = Ledger(Path(d)/'campaign.sqlite')
            ledger.configure()
            failures = 0
            for index in range(2):
                eid=ledger.reserve(proposal(category,index))
                ledger.transition(eid,'submitting'); ledger.transition(eid,'running')
                ledger.transition(eid,'failed',result={'status':'fail','fixture':True})
                failures+=1
            blocked=False
            try: ledger.reserve(proposal(category,2))
            except ValueError as e: blocked='stagnated' in str(e)
            alternative=ledger.reserve(proposal(category,3,'alternative causal mechanism'))
            ledger.transition(alternative,'submitting');ledger.transition(alternative,'running')
            ledger.transition(alternative,'failed',result={'status':'fail'})
            family_blocked=False
            try: ledger.reserve(proposal(category,4,'third mechanism'))
            except ValueError as e: family_blocked='Family blocked' in str(e)
            ledger.reset_family(category,['fixture-new-evidence'],'fixture-independent-reviewer')
            recovered=bool(ledger.reserve(proposal(category,5,'revised diagnosis')))
            outcomes.append({'category':category,'mechanism_blocked':blocked,'family_blocked':family_blocked,
                             'reviewed_reset_admitted':recovered,'physical_runs':0})
    # Explicit setup improvement introducing hold failure cannot be promoted.
    limits={'setup':{'unit':'ns','direction':'min','limit':0},'hold':{'unit':'ns','direction':'min','limit':.05}}
    cross=objectives({'setup':{'value':1,'unit':'ns','evidence':'fixture'},
                      'hold':{'value':-.1,'unit':'ns','evidence':'fixture'}},limits)
    return {'kind':'synthetic controller policy benchmark','cases':outcomes,'denominator':len(CATEGORIES),
            'passed':sum(all(r[k] for k in ('mechanism_blocked','family_blocked','reviewed_reset_admitted')) for r in outcomes),
            'collateral_regression_rejected':not cross['feasible'],
            'real_closure_cases':0,'first_attempt_success':None,'ordinary_codex_comparison':None,
            'limitations':['No held-out native closure dataset','No causal accuracy ground truth','No physical performance claim']}
