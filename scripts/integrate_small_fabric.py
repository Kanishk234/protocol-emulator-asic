"""Reproduce the experimental TT integration from the cached FABulous build.

Run inside the project venv. Inputs remain untouched; generated src files
are a checked transformation, not hand edits to upstream installations.
"""
from pathlib import Path
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from patches.reference_reload_hold import transform, word_only_loader, EXPECTED

cache = Path(sys.argv[1]).resolve()
source = cache / 'project/Test/build/fabric_files'
out = ROOT / 'src/fabric_gen'
out.mkdir(exist_ok=True)
names = ['Config_access', 'ConfigFSM', 'eFPGA_top', 'eFPGA',
         'Frame_Data_Reg', 'Frame_Select', 'IO_1_bidirectional_frame_config_pass',
         'LUT4AB_ConfigMem', 'LUT4AB_switch_matrix', 'LUT4AB',
         'LUT4c_frame_config_dffesr', 'models_pack', 'MUX8LUT_frame_config_mux',
         'N_term_single_switch_matrix', 'N_term_single',
         'S_term_single_switch_matrix', 'S_term_single',
         'W_IO_ConfigMem', 'W_IO_switch_matrix', 'W_IO']
manifest = {}
for stem in names:
    name = stem + '.v'
    original = (source/name).read_bytes()
    text = original.decode()
    if name in ('LUT4AB.v', 'LUT4c_frame_config_dffesr.v'):
        assert hashlib.sha256(original).hexdigest() == EXPECTED[name]
        text = transform(name, text)
    elif name == 'eFPGA.v':
        assert text.count('Tile_X1Y1_LUT4AB') == 1
        assert text.count('Tile_X1Y2_LUT4AB') == 1
        anchor = re.match(r'\Amodule\s+\w+[\s\S]*?\n    \(\n', text)
        assert anchor
        text = text[:anchor.end()] + '        input ReloadHold,\n' + text[anchor.end():]
        text, count = re.subn(r'(    Tile_X\d+Y\d+_LUT4AB\n    \(\n)',r'\1    .ReloadHold(ReloadHold),\n',text)
        assert count == 2
    elif name == 'eFPGA_top.v':
        assert 'parameter NumberOfRows=2,' in text and 'parameter NumberOfCols=2,' in text
        text = word_only_loader(transform(name,text))
    text = '\n'.join(line.rstrip() for line in text.splitlines()).rstrip()+'\n'
    (out/name).write_text(text)
    manifest[name] = {'input_sha256': hashlib.sha256(original).hexdigest(),
                      'output_sha256': hashlib.sha256(text.encode()).hexdigest()}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
# Separate small architecture identity and geometry; original tests stay fixed.
exp = ROOT/'experiments/fabric_reference'
validator = (exp/'wp_image_validator.v').read_text().replace('wp_image_validator','wp_small_image_validator')
validator = validator.replace("32'h46524231", "32'h46534231").replace("32'd12024", "32'd504").replace('3005','125').replace('row_word == 14','row_word == 2')
validator = validator.replace('10-column, 14-row', '2-column, 2-row').replace('"FRB1"','"FSB1"')
(ROOT/'src/wp_small_image_validator.v').write_text(validator)
management = (exp/'wp_validated_reload.v').read_text().replace('wp_validated_reload','wp_small_validated_reload').replace('wp_image_validator','wp_small_image_validator')
(ROOT/'src/wp_small_validated_reload.v').write_text(management)
(ROOT/'src/wp_reload_guard.v').write_text((exp/'wp_reload_guard.v').read_text())
wrapper = (exp/'reference_validated_top.v').read_text().replace('reference_validated_top','wp_small_fabric').replace('wp_validated_reload','wp_small_validated_reload')
wrapper = wrapper.replace('[27:0]','[3:0]').replace('[55:0]','[7:0]').replace('O_top[27:2]','O_top[3:2]').replace("28'b0","4'b0").replace("{28{1'b1}}","4'b0")
(ROOT/'src/wp_small_fabric.v').write_text(wrapper)
files = ['tt_um_warp.v','wp_small_fabric.v','wp_small_validated_reload.v','wp_small_image_validator.v','wp_reload_guard.v'] + ['fabric_gen/'+n+'.v' for n in names]
info = (ROOT/'info.yaml').read_text()
info = re.sub(r'  source_files:\n(?:    - .*\n)+','  source_files:\n'+''.join('    - "'+f+'"\n' for f in files),info)
(ROOT/'info.yaml').write_text(info)
make = (ROOT/'test/Makefile').read_text()
(ROOT/'test/Makefile').write_text(re.sub(r'^PROJECT_SOURCES = .*$', 'PROJECT_SOURCES = '+' '.join(files),make,flags=re.M))
# Checked-in test vector is required by isolated CI checkouts (not build output).
image = (cache/'counter.bin').read_bytes()
assert hashlib.sha256(image).hexdigest() == 'e5c8fa594fe4bda05795adc31884d154e8b9e0f365ea7462f01433b77b8e6c36'
(ROOT/'test/small_counter_image.py').write_text('# Generated regression vector; see docs/reports/ANISH_SMALL_COMPILE.md\nIMAGE = bytes.fromhex(\n'+''.join('    "'+image[i:i+32].hex()+'"\n' for i in range(0,len(image),32))+')\n')
