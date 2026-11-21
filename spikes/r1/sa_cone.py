"""Read-only structural backward graph of observed unknown native pins."""
import argparse
import io,json
from pathlib import Path
from profiling.r1_quiesce import PlainSpec
from compile.bitgen import fasm_features
from compile.bitfile import BitFile
from global_support import flatten
from unused_input_sweep import prove_input,carry_modes
parser=argparse.ArgumentParser(description=__doc__)
for name in ('capsule','native','functional','out'):parser.add_argument('--'+name,type=Path,required=True)
parser.add_argument('--snapshot',choices=('runtime-failure.json','runtime-after-load.json','runtime-before-reset-release.json'),default='runtime-failure.json')
parser.add_argument('--root-port',default='Tile_X2Y4_B_IN_top')
parser.add_argument('--include-registered',action='store_true')
args=parser.parse_args()
cap=args.capsule;native=args.native;case=args.functional/'candidate-case';root=args.functional/'candidate'
state=json.loads((root/'configuration-state.json').read_text());runtime=json.loads((root/args.snapshot).read_text());mods=json.loads((native/'registered_native/all-native.json').read_text())['modules'];top=json.loads((cap/'analysis/top.json').read_text())['modules']['eFPGA'];flat,q=flatten(top,mods,state['tiles']);values={};conflicts=[]
for tile,row in runtime['tiles'].items():
 for name,c in row['cells'].items():
  model=flat['cells'].get(tile+'/'+name)
  if model is None:
   assert c['type'] in ('sg13cmos5l_tiehi','sg13cmos5l_tielo');continue
  for pin,value in c['pins'].items():
   if pin not in model['connections']:continue
   bits=model['connections'][pin]
   assert len(value)==len(bits),(name,pin,value)
   for bit,v in zip(bits,reversed(value)):
    if bit in values and values[bit]!=v:conflicts.append((tile,name,pin,bit,values[bit],v))
    values[bit]=v
for name,value in q.items():values[flat['cells'][name]['connections']['Q'][0]]=value
print('CAPTURED',len(values),'CONFLICTS',len(conflicts));assert not conflicts
port=flat['ports'][args.root_port]
if port['direction']!='output' or len(port['bits'])!=1:raise ValueError('Require a scalar observed output root')
rootbit=port['bits'][0];drivers={b:(name,c) for name,c in flat['cells'].items() for p,d in c['port_directions'].items() if d=='output' for b in c['connections'][p]};cone=set();todo=[rootbit]
while todo:
 b=todo.pop()
 if b in cone or values.get(b) not in ('X','Z'):continue
 cone.add(b)
 if b in drivers:
  name,c=drivers[b];todo.extend(b for p,d in c['port_directions'].items() if d=='input' for b in c['connections'][p] if values.get(b) in ('X','Z'))
print('UNKNOWN_CONE',len(cone))
spec=PlainSpec(io.BytesIO((cap/'model/resource/macro/fabulous/bitStreamSpec.bin').read_bytes())).load();pips=(cap/'model/resource/macro/fabulous/.FABulous/pips.txt').read_text();words=BitFile.load(root/'quiesced.wbit').words;features=fasm_features(case/'design.fasm');enabled=carry_modes(spec,mods,state);ground={(r['tile'],r['output']) for r in json.loads((root/'quiescence.json').read_text())['changes']};instances={t.split('_')[1]:t for t in top['cells']}
def terminal(node):
 if node in ground:return '0'
 xy,wire=node;inst=instances[xy];key=inst+'/'+wire
 if key in flat['netnames'] and len(flat['netnames'][key]['bits'])==1:return values.get(flat['netnames'][key]['bits'][0])
 return runtime['tiles'][inst]['signals'].get(wire)
found=[]
for tile,row in runtime['tiles'].items():
 if row['tile_type']!='LUT4x8_ha':continue
 xy=tile.split('_')[1]
 for l in 'ABCDEFGH':
  if flat['netnames'][tile+'/L'+l+'_O']['bits'][0] not in cone:continue
  for i in range(4):
   try:change=prove_input(xy,l,i,spec,mods['LUT4x8_ha'],state,features,words,pips,enabled,allow_registered=args.include_registered)
   except ValueError:continue
   before=terminal(tuple(change['route_before'][-1]));after=terminal(tuple(change['route_after'][-1]))
   if before in ('X','Z') and after in ('0','1'):
    change.update(observed_terminal_before=before,observed_terminal_after=after);found.append(change)
    print('CANDIDATE',xy,l,i,hex(change['observed_init']),change['route_before'][-1],change['route_after'][-1],after)
report=dict(scope='Read-only search within an observed unknown output cone. Binary cofactor/carry proof only; no functional repair or timing proof.',snapshot=args.snapshot,root_port=args.root_port,registered_input_proofs_enabled=args.include_registered,unknown_cone_bits=len(cone),captured_bits=len(values),conflicts=conflicts,candidates=found)
args.out.write_text(json.dumps(report,indent=2)+'\n');print('CANDIDATES',len(found))
