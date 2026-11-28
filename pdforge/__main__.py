"""PDForge command line; all output is JSON and live dispatch is explicit."""
import argparse
import json
from pathlib import Path
import sys
from .core.evidence import inventory, load, ROOT
from .core.diagnostics import parse_sta, diagnose, compare
from .core.knowledge import Index
from .core.ledger import Ledger, validate
from .adapters.metrics import ingest_metrics
from .adapters.backends import MockBackend, GitHubBackend, CloudBackend, NativeBackend, extract_zip
from .benchmarks.replay import benchmark


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('doctor',help='Read-only workspace and physical-input inventory')
    for name in ('ingest','diagnose'):
        p=sub.add_parser(name,help='Parse explicit-stage OpenSTA evidence or LibreLane metrics')
        p.add_argument('path');p.add_argument('--stage',required=True);p.add_argument('--corner',default='unknown')
        p.add_argument('--unit',choices=['ps','ns','us']);p.add_argument('--metrics',action='store_true')
    p=sub.add_parser('compare',help='Compare two ingested timing JSON files');p.add_argument('before');p.add_argument('after')
    p=sub.add_parser('propose',help='Validate manual strict proposal JSON');p.add_argument('proposal')
    p=sub.add_parser('retrieve',help='Index a pinned manifest and return cited excerpts');p.add_argument('manifest');p.add_argument('query')
    p.add_argument('--index',default='pdforge/.local/knowledge.sqlite')
    p=sub.add_parser('campaign',help='Reserve and plan an experiment; dry-run by default')
    p.add_argument('proposal');p.add_argument('--db',default='pdforge/.local/campaign.sqlite')
    p.add_argument('--backend',choices=['mock','github','cloud','native'],default='mock')
    p.add_argument('--repository',default='Kanishk234/protocol-emulator-asic')
    p.add_argument('--dry-run',action='store_true');p.add_argument('--reserve',action='store_true')
    for name in ('status','resume','export'):
        p=sub.add_parser(name,help='Inspect durable state without resubmitting remote jobs')
        p.add_argument('--db',default='pdforge/.local/campaign.sqlite')
    sub.add_parser('benchmark',help='Run bounded synthetic multi-category policy benchmark')
    p=sub.add_parser('unpack',help='Safely unpack a downloaded artifact in local scratch');p.add_argument('archive');p.add_argument('destination')
    p=sub.add_parser('remote',help='Explicitly authorize dispatch or resume an owned validation run')
    p.add_argument('action',choices=['dispatch','poll','download','validate'])
    p.add_argument('experiment_id');p.add_argument('--db',default='pdforge/.local/campaign.sqlite')
    p.add_argument('--branch',default='autonomous-pd');p.add_argument('--revision')
    p.add_argument('--authorize-remote',action='store_true');p.add_argument('--artifact-dir')
    args=parser.parse_args()
    try:
        for name in ('db','index'):
            if hasattr(args,name):
                path=Path(getattr(args,name)).resolve()
                if not path.is_relative_to(ROOT/'pdforge/.local'):raise ValueError('State must remain under pdforge/.local')
                path.parent.mkdir(parents=True,exist_ok=True)
        if args.command=='doctor': result=inventory()
        elif args.command in ('ingest','diagnose'):
            if args.metrics: result=ingest_metrics(args.path,args.stage)
            else:
                result=parse_sta(args.path,args.stage,args.corner,args.unit)
                if args.command=='diagnose': result=diagnose(result)
        elif args.command=='compare': result=compare(load(args.before),load(args.after))
        elif args.command=='propose': result={'valid':True,'fingerprint':validate(load(args.proposal))}
        elif args.command=='retrieve':
            index=Index(args.index);index.ingest(load(args.manifest));result=index.search(args.query)
        elif args.command=='campaign':
            proposal=load(args.proposal);fingerprint=validate(proposal)
            backend={'mock':MockBackend,'github':lambda:GitHubBackend(args.repository),'cloud':CloudBackend,'native':NativeBackend}[args.backend]()
            row={'fingerprint':fingerprint,'proposal':json.dumps(proposal)}
            result={'plan':backend.plan(row),'dry_run':True,'submitted':False}
            if args.reserve:
                if args.dry_run: raise ValueError('--dry-run and --reserve are mutually exclusive')
                ledger=Ledger(args.db);ledger.configure();result['experiment_id']=ledger.reserve(proposal,args.backend)
        elif args.command in ('status','resume','export'):
            if not Path(args.db).is_file(): raise ValueError('Campaign does not exist')
            ledger=Ledger(args.db)
            result={'experiments':ledger.rows(),'recovery':ledger.recovery()}
        elif args.command=='remote':
            from .adapters.github import dispatch,resume,validate_result,GitHubValidation,download_artifact
            ledger=Ledger(args.db)
            if args.action=='dispatch':
                result=dispatch(ledger,args.experiment_id,args.branch,args.revision,authorized=args.authorize_remote)
            elif args.action=='poll':result=resume(ledger,args.experiment_id)
            elif args.action=='validate':
                if not args.artifact_dir:raise ValueError('--artifact-dir required')
                result=validate_result(ledger,args.experiment_id,args.artifact_dir)
            else:
                row=next(r for r in ledger.rows() if r['id']==args.experiment_id)
                if row['state']!='running' or not row['remote_id']:raise ValueError('No owned run to download')
                bridge=GitHubValidation()
                state=resume(ledger,args.experiment_id,bridge)
                if state.get('receipt',{}).get('conclusion')!='success':raise ValueError('Run has not succeeded')
                items=bridge.artifacts(row['remote_id'])
                matches=[a for a in items if a['name']=='pdforge-validation-'+row['remote_id']]
                if len(matches)!=1:raise ValueError('Missing or ambiguous artifact')
                destination=ROOT/'pdforge/.local'/('artifact-'+row['remote_id'])
                downloaded=download_artifact(matches[0],str(destination)+'.zip',10_000_000)
                result=extract_zip(downloaded['path'],destination,10_000_000)
                ledger.event(args.experiment_id,'artifact-download',downloaded)
                result['directory']=str(destination)
        elif args.command=='benchmark': result=benchmark()
        elif args.command=='unpack':
            if not Path(args.destination).resolve().is_relative_to(ROOT/'pdforge/.local'):
                raise ValueError('Artifact destination must be pdforge/.local')
            result=extract_zip(args.archive,args.destination)
        print(json.dumps(result,indent=2,allow_nan=False))
    except (ValueError,OSError,KeyError,TypeError) as e:
        print(json.dumps({'error':str(e)}));return 2
    return 0

if __name__=='__main__': sys.exit(main())
