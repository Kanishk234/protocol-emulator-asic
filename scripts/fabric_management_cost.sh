#!/usr/bin/env bash
# Map the actual management wrapper, retaining exactly one fabric black box.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INPUT=$(realpath "${1:?Usage: fabric_management_cost.sh build/fabric-reference-RUN}")
WORK=$(mktemp -d /tmp/warp-management.XXXXXXXX)
OUT="$ROOT/build/$(basename "$WORK")"
mkdir -p "$OUT"
trap 'cp -a "$WORK"/. "$OUT"/; echo "Management evidence: $OUT"' EXIT
cp "${BASH_SOURCE[0]}" "$WORK/runner.sh"
for name in wp_image_validator.v wp_validated_reload.v wp_reload_guard.v reference_validated_top.v loader_fixture.v loader_handshake_tb.v; do
  cp "$ROOT/experiments/fabric_reference/$name" "$WORK/"
done
for name in eFPGA_Config.v ConfigFSM.v Frame_Data_Reg.v config_UART.v bitbang.v; do
  cp "$INPUT/reference/Test/build/fabric_files/$name" "$WORK/"
done
PDK="${XDG_CACHE_HOME:-$HOME/.cache}/warp/pdk-2bbec755dc67ca3db0261c3d6163e15735d66710/ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell"
IV="${XDG_CACHE_HOME:-$HOME/.cache}/warp/iverilog-13"
cp "$PDK/lib/sg13cmos5l_stdcell_typ_1p20V_25C.lib" "$WORK/cells.lib"
python - "$INPUT/counter.bin" "$WORK" <<'PY'
import sys, struct, zlib
from pathlib import Path
data = Path(sys.argv[1]).read_bytes()
assert len(data)==12024
out = Path(sys.argv[2])
out.joinpath("counter.hex").write_text("".join(f"{w:08x}\n" for w in struct.unpack(">3006I",data)))
out.joinpath("crc.txt").write_text(f"{zlib.crc32(data):08x}")
PY
sha256sum "$WORK"/*.v "$WORK/runner.sh" "$WORK/cells.lib" "$PDK"/verilog/*.v "$INPUT/counter.bin" > "$WORK/input-sha256.txt"
yosys -V > "$WORK/versions.txt"
"$IV/usr/bin/iverilog" -B "$IV/usr/lib/ivl" -V >> "$WORK/versions.txt" 2>&1
cd "$WORK"
sources="wp_image_validator.v wp_validated_reload.v wp_reload_guard.v reference_validated_top.v"
for variant in word byte; do
  serial=0; defines=(-DWORD_CRC)
  if [ "$variant" = byte ]; then serial=1; defines=(); fi
  # -lib ignores ALL fixture implementation: fabric outputs remain unknown
  # to synthesis, preventing constant-pad optimization. Do not read it normally.
  timeout 90s yosys -Q -T -p "read_verilog -lib loader_fixture.v; read_verilog $sources; chparam -set SERIAL_CRC $serial reference_validated_top; synth -top reference_validated_top -flatten; check -assert; read_liberty -lib cells.lib; dfflibmap -liberty cells.lib; abc -liberty cells.lib; opt_clean; check -assert; tee -o $variant-area.json stat -json -liberty cells.lib; write_json $variant-net.json; write_verilog -noattr -noexpr $variant-net.v" > "$variant-synth.log" 2>&1
  "$IV/usr/bin/iverilog" -B "$IV/usr/lib/ivl" -g2012 -DMAPPED_WRAPPER "${defines[@]}" -s loader_handshake_tb -o "$variant.vvp" "$PDK/verilog/sg13cmos5l_udp.v" "$PDK/verilog/sg13cmos5l_stdcell.v" "$variant-net.v" loader_fixture.v eFPGA_Config.v ConfigFSM.v Frame_Data_Reg.v config_UART.v bitbang.v loader_handshake_tb.v > "$variant-compile.log" 2>&1
  timeout 30s "$IV/usr/bin/vvp" "$variant.vvp" +image=counter.hex +crc="$(cat crc.txt)" > "$variant.log" 2>&1
  grep '^PASS: loader handshake' "$variant.log"
done
python - <<'PY'
import json
from pathlib import Path
report = {}
for name in ("word", "byte"):
    net = json.loads(Path(f"{name}-net.json").read_text())
    fabric = net["modules"]["eFPGA_top"]
    assert int(fabric["attributes"]["blackbox"],2)==1 and not fabric["cells"]
    top = net["modules"]["reference_validated_top"]
    assert sum(c["type"]=="eFPGA_top" for c in top["cells"].values())==1
    stat = json.loads(Path(f"{name}-area.json").read_text())["modules"]["\\reference_validated_top"]
    cells = stat["num_cells_by_type"]
    assert cells.get("eFPGA_top")==1
    assert all(c.startswith("sg13cmos5l_") or c in ("eFPGA_top","$scopeinfo") for c in cells)
    report[name] = {"standard_cells":sum(n for c,n in cells.items() if c.startswith("sg13cmos5l_")),
                    "area_um2":stat["area"],"excluded_fabric_blackboxes":1}
Path("summary.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report))
PY
