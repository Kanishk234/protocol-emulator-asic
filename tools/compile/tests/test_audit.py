"""Evidence checks reject changed sources, swapped images and misleading reports."""
import hashlib
import json

import pytest

from compile.audit import audit
from compile.bitfile import BitFile
from compile.compile import CompileError, fingerprint_inputs
from host.protocol import SYNC_WORD


@pytest.fixture
def evidence(tmp_path):
    source = tmp_path / "user.v"
    source.write_text("module user; endmodule\n")
    image = tmp_path / "user.wbit"
    bf = BitFile(3, [SYNC_WORD, 1 << 20])
    bf.save(image)
    report = {"arch_version": "0x0003", "words": 2, "crc32": f"0x{bf.crc:08X}",
              "provenance": {"inputs": [{"path": str(source),
                  "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}],
                  "bitfile": str(image), "bitfile_sha256": hashlib.sha256(image.read_bytes()).hexdigest()}}
    path = tmp_path / "report.json"
    path.write_text(json.dumps(report))
    return source, image, report, path


def test_matching_evidence(evidence):
    assert audit(evidence[3]) == []


def test_changed_source(evidence):
    source, _, _, path = evidence
    source.write_text("module changed; endmodule\n")
    assert any(str(source) in problem for problem in audit(path))


def test_different_valid_image(evidence):
    _, image, _, path = evidence
    BitFile(4, [SYNC_WORD, 123, 1 << 20]).save(image)
    problems = audit(path)
    assert any("changed:" in p for p in problems)
    assert any("disagrees" in p for p in problems)


def test_truncated_header(evidence):
    _, image, _, path = evidence
    image.write_bytes(b"WBIT")
    assert any("invalid bitstream" in p for p in audit(path))


def test_report_payload_disagrees(evidence):
    _, _, report, path = evidence
    report["words"] = 3
    path.write_text(json.dumps(report))
    assert any("disagrees" in p for p in audit(path))


def test_missing_source(evidence):
    source, _, _, path = evidence
    source.unlink()
    assert any("missing:" in p for p in audit(path))


def test_legacy_report_needs_rebuild(tmp_path):
    path = tmp_path / "report.json"
    path.write_text("{}")
    with pytest.raises(ValueError, match="no provenance"):
        audit(path)


def test_input_snapshot_detects_edits_and_deduplicates(tmp_path):
    source = tmp_path / "user.v"
    source.write_text("first version")
    first = fingerprint_inputs([source, source])
    assert len(first) == 1
    source.write_text("second version")
    assert fingerprint_inputs([source]) != first


def test_missing_compile_input_is_a_compile_error(tmp_path):
    with pytest.raises(CompileError, match="Cannot fingerprint compile input"):
        fingerprint_inputs([tmp_path / "missing.v"])
