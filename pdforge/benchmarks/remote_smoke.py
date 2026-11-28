"""Cloud-safe bounded infrastructure validation, never a chip EDA/signoff run."""
import hashlib
import json
import os
from pathlib import Path
import sys
import unittest
from pdforge.benchmarks.replay import benchmark


def main():
    out=Path('pdforge/.local/remote');out.mkdir(parents=True,exist_ok=True)
    suite=unittest.defaultTestLoader.discover('pdforge/tests')
    with (out/'tests.txt').open('w') as log:
        result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    b=benchmark();(out/'benchmark.json').write_text(json.dumps(b,indent=2)+'\n')
    receipt={'revision':os.environ['GITHUB_SHA'],'run_id':os.environ['GITHUB_RUN_ID'],
             'attempt':os.environ['GITHUB_RUN_ATTEMPT'],'token':os.environ['PDFORGE_TOKEN'],
             'tests_run':result.testsRun,'tests_passed':result.wasSuccessful(),
             'test_failures':len(result.failures),'test_errors':len(result.errors),'physical_qualified':False,
             'files':{name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in ['tests.txt','benchmark.json']}}
    (out/'result.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return 0 if result.wasSuccessful() else 1

if __name__=='__main__':sys.exit(main())
