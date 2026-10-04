"""Bounded diagnostic for CI run 36603402850; not production constraints.

Run in the project venv. Refuse to emit configured STA while latch aliases
remain unresolved. baseline.tcl reuses the original netlist/SDC/SPEF.
"""
from pathlib import Path
import re,json,sys,hashlib
root=Path(__file__).resolve().parents[1]
build=root/'build/configured-sta'
build.mkdir(exist_ok=True)
final=root/'build/ci-36603402850/runs/wokwi/final'
net=final/'nl/tt_um_warp.nl.v'
sys.path.insert(0,str(root/'test'))
from small_counter_image import IMAGE
words=[int.from_bytes(IMAGE[i:i+4],'big') for i in range(0,len(IMAGE),4)]
assert len(words)==126
assert words[:5]==[0xaaff01,1,0,0,0xfab0fab1] and words[-1]==0x100000
for col in range(2):
 for frame in range(20):
  assert words[5+(col*20+frame)*3]==(col<<27)|(1<<frame)
entries=[]; unresolved=[]
for m in re.finditer(r'sg13cmos5l_dlhq_\d+\s+(\S+)\s*\((.*?)\);',net.read_text(),re.S):
 q=re.search(r'\.Q\(\\([^\s)]+)\s*\)',m[2])
 assert q, m[0]
 a=re.search(r'Tile_X(\d+)Y(\d+)_.*Inst_Frame(\d+)_bit(\d+)\.Q$',q[1])
 if not a: unresolved.append(dict(pin=m[1]+"/Q",net=q[1])); continue
 col,row,frame,bit=map(int,a.groups())
 assert col<2 and 1<=row<=2 and frame<20 and bit<32
 index=5+(col*20+frame)*3+1+(2-row)
 value=(words[index]>>bit)&1
 entries.append(dict(pin=m[1]+'/Q',net=q[1],value=value,word=index,bit=bit))
assert len({e['pin'] for e in entries})==len(entries)
(build/'cases.json').write_text(json.dumps(entries,indent=2))
lib=Path.home()/'.cache/warp/pdk-2bbec755dc67ca3db0261c3d6163e15735d66710/ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/lib/sg13cmos5l_stdcell_typ_1p20V_25C.lib'
base=f'read_liberty {{{lib}}}\nread_verilog {{{net}}}\nlink_design tt_um_warp\nread_sdc {{{final}/sdc/tt_um_warp.sdc}}\nread_spef {{{final}/spef/nom/tt_um_warp.nom.spef}}\n'
(build/'unresolved.json').write_text(json.dumps(unresolved,indent=2))
if unresolved and (build/'counter.tcl').exists():
 (build/'counter.tcl').unlink()  # Reject stale configured results as inputs.
(build/'audit.json').write_text(json.dumps(dict(mapped=len(entries),unresolved=len(unresolved),
 netlist_sha256=hashlib.sha256(net.read_bytes()).hexdigest(),
 image_sha256=hashlib.sha256(IMAGE).hexdigest(),
 configured_sta_allowed=not unresolved),indent=2)+'\n')
for mode in (['baseline'] if unresolved else ['baseline','counter']):
 text=base
 if mode=='counter':
  for e in entries:
   text+=f'set p [get_pins {{{e["pin"]}}}]\nif {{[llength $p] != 1}} {{error "missing configuration pin"}}\nset_case_analysis {e["value"]} $p\n'
 text+='report_checks -path_delay max -format full_clock_expanded -group_path_count 3\nreport_worst_slack -max\nreport_tns\nexit\n'
 (build/(mode+'.tcl')).write_text(text)
print('configuration pins',len(entries))
