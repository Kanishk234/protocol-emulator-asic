"""WARP bitgen and bitstream file checks (no Yosys/nextpnr needed: uses the committed FASM of the
example designs, test/bitstreams/*.fasm, and the fabric's committed bitstream spec)."""

import pickle
import re
from pathlib import Path

import pytest
import yaml

from compile.bitfile import BitFile, words_from_fabulous_bin
from compile.bitgen import BitgenError, fasm_features, gen_words, load_spec, words
from compile.compile import CompileError, check_frames
from host.protocol import ARCH_VERSION, SYNC_WORD

ROOT = Path(__file__).resolve().parents[3]
ARCH = yaml.safe_load((ROOT / "arch" / (ROOT / "arch/CURRENT").read_text().strip() / "arch.yaml").read_text())
SPEC = ROOT / ARCH["macro"] / "fabulous/bitStreamSpec.bin"
ROWS = ARCH["config_rows"]
COLS = ARCH["config_cols"]
BITS = ROOT / "test/bitstreams"
EXAMPLES = sorted(p.stem for p in BITS.glob("*.fasm"))


@pytest.mark.parametrize("name", EXAMPLES)
def test_committed_bitstreams_match_their_fasm(name):
    """test/bitstreams/<name>.wbit is exactly what bitgen makes of the committed FASM."""
    bf = BitFile.load(BITS / f"{name}.wbit")
    assert bf.words == gen_words(BITS / f"{name}.fasm", SPEC)
    check_frames(bf.words, ROWS)


@pytest.mark.parametrize("name", EXAMPLES)
def test_matches_fabulous_bit_gen_except_clk_features(name, tmp_path):
    """Word for word the same as FABulous's own generator (border rows on), for every feature
    fabulous_bit_gen does not drop (BUGS #13: it skips features containing "CLK")."""
    bit_gen = pytest.importorskip("fabulous_bit_gen.bit_gen")
    feats = [f for f in fasm_features(BITS / f"{name}.fasm") if "CLK" not in f]
    fasm = tmp_path / "noclk.fasm"
    fasm.write_text("\n".join(feats) + "\n")
    spec = load_spec(SPEC)
    spec.setdefault("ArchSpecs", {})["IncludeBorderRows"] = True
    spec_file = tmp_path / "spec.bin"
    spec_file.write_bytes(pickle.dumps(spec))
    bit_gen.gen_bitstream(str(fasm), str(spec_file), str(tmp_path / "ref.bin"))
    ref = words_from_fabulous_bin((tmp_path / "ref.bin").read_bytes())
    assert words(feats, load_spec(SPEC)) == ref


def word_bit(w, tile, idx):
    """The value in the bitstream of spec bit `idx` of tile XnYm: column n, frame idx // 32,
    row m (rows are sent bottom first), bit idx % 32."""
    x, y = (int(v) for v in tile[1:].split("Y"))
    frame, bit = divmod(idx, 32)
    at = 1 + (x * 20 + frame) * (1 + ROWS) + 1 + (ROWS - 1 - y)
    assert w[at - 1 - (ROWS - 1 - y)] == (x << 27) | (1 << frame)     # the frame header
    return (w[at] >> bit) & 1


@pytest.mark.parametrize("name", EXAMPLES)
def test_gclk_mux_selects_are_written(name):
    """BUGS #13: fabulous_bit_gen drops features containing "CLK", which includes the LUT tiles'
    global-clock mux selects (GCLK_BEG0). Every such feature with configuration bits must be in
    the bitstream."""
    spec = load_spec(SPEC)
    w = gen_words(BITS / f"{name}.fasm", SPEC)
    checked = 0
    for f in fasm_features(BITS / f"{name}.fasm"):
        if "GCLK_BEG" not in f:
            continue
        tile, feat = f.split(".", 1)
        for idx, val in spec["TileSpecs"][tile][feat].items():
            assert word_bit(w, tile, idx) == int(val), f"{f}: bit {idx}"
            checked += 1
    feats = fasm_features(BITS / f"{name}.fasm")
    if any(f.endswith(".FF") for f in feats):          # clocked designs route a global clock
        assert any("GCLK_BEG" in f for f in feats)


def test_unknown_feature_is_an_error():
    with pytest.raises(BitgenError):
        words(["X1Y1.NO_SUCH.FEATURE"], load_spec(SPEC))
    with pytest.raises(BitgenError):
        words(["X9Y9.A.B"], load_spec(SPEC))


def test_empty_design_framing():
    w = words([], load_spec(SPEC))
    assert w[0] == SYNC_WORD and w[-1] == 1 << 20
    assert len(w) == 2 + COLS * 20 * (1 + ROWS)
    check_frames(w, ROWS)
    with pytest.raises(CompileError):
        check_frames(w, ROWS - 2)


def test_bitfile_roundtrip_and_errors():
    bf = BitFile(ARCH_VERSION, [SYNC_WORD, 1, 2, 1 << 20])
    data = bf.to_bytes()
    assert BitFile.from_bytes(data) == bf
    with pytest.raises(ValueError):
        BitFile.from_bytes(b"XXXX" + data[4:])
    bad = bytearray(data)
    bad[-1] ^= 1
    with pytest.raises(ValueError):
        BitFile.from_bytes(bytes(bad))
    with pytest.raises(ValueError):
        BitFile.from_bytes(BitFile(ARCH_VERSION, [1, 2]).to_bytes())


def test_arch_version_is_one_number():
    """arch.yaml, the shell's ARCH_VERSION parameter in the top level, the host default and the
    committed bitstreams must agree."""
    arch = ARCH["arch_version"]
    top = (ROOT / "src/tt_um_warp.v").read_text()
    m = re.search(r"\.ARCH_VERSION\(16'h([0-9A-Fa-f]+)\)", top)
    assert m and int(m.group(1), 16) == arch == ARCH_VERSION
    for name in EXAMPLES:
        assert BitFile.load(BITS / f"{name}.wbit").arch_version == arch
