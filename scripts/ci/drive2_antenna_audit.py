"""Read-only antenna geometry comparison on two exact native-drive checkpoints."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

VIEWS = {'43-openroad-repairantennas': {'path': 'runs/stock-official-baseline/43-openroad-repairantennas/1-openroad-diodeinsertion/tt_um_tripwire.odb',
                                'sha256': '29ef19fd99fbfa98d23ec860c0c9da9c079038ec3b0cbf0a7a571931d8435368'},
 '44-openroad-resizertimingpostgrt': {'path': 'runs/stock-official-baseline/44-openroad-resizertimingpostgrt/tt_um_tripwire.odb',
                                      'sha256': '6ec966f4b13aa388953857f09aff1024e05526bd42845ee2286b23d58dd73ae3'}}
IMAGE = 'ghcr.io/librelane/librelane@sha256:af2405f5d48d8fe14d406ecce913811177a95e365e3b625859677307cace2469'


def main():
    root = Path.cwd().resolve()
    run = json.loads(Path('drive2-source-run.json').read_text())
    expected = dict(id=43178099947, head_sha='991d07c6aabf1675bacdeaf9760ce35f98c3065b', head_branch='main',
                    path='.github/workflows/gds-official-dev4-drive2-screen.yaml', conclusion='failure')
    if any(run.get(k) != v for k,v in expected.items()):
        raise ValueError('Wrong native-drive source run')
    frozen=root/'frozen-screen'
    output=root/'runs/drive2-antenna-audit'
    output.mkdir(parents=True, exist_ok=False)
    hashes={}
    for stage, view in VIEWS.items():
        odb=frozen/view['path']
        if hashlib.sha256(odb.read_bytes()).hexdigest()!=view['sha256']:
            raise ValueError('Wrong exact ODB checkpoint')
        hashes[stage]=view['sha256']
        report=output/(stage+'.rpt')
        tcl=output/(stage+'.tcl')
        tcl.write_text(f'read_db {{{odb}}}\n'
                       'set net [[ord::get_db_block] findNet net14163]\n'
                       'if {$net == "NULL"} {error "Missing bound net14163"}\n'
                       f'check_antennas -net net14163 -verbose -report_file {{{report}}}\nexit\n')
        cmd=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
             '-v',f'{root}:{root}','-w',str(root),IMAGE,'openroad','-exit','-no_init',str(tcl)]
        with (output/(stage+'.log')).open('w') as log:
            subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
        if not report.is_file() or 'net14163' not in report.read_text():
            raise ValueError('Missing target-net geometry report')
        if hashlib.sha256(odb.read_bytes()).hexdigest()!=view['sha256']:
            raise ValueError('Read-only audit modified source database')
    (output/'receipt.json').write_text(json.dumps(dict(source_run=run['id'],source_sha=run['head_sha'],
        source_odb_hashes=hashes, net='net14163',physical_repairs=False,
        qualified=False, official_signoff=False),indent=2)+'\n')


if __name__ == '__main__':
    main()
