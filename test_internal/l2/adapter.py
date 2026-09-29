"""Normalize candidate debug taps to tools.tripsim.lockstep's logical schema."""

from __future__ import annotations

import pathlib
import re

import tripwire_spec as S
from tripsim.lockstep import snapshot


def _defines(src: pathlib.Path) -> dict[str, int]:
    text = (src / "trw_defs.vh").read_text()
    values = re.findall(r"^`define\s+(TRW_HA_\w+)\s+(16'h[0-9a-fA-F]+|\d+)", text, re.M)
    return {name: int(value.split("'h", 1)[1], 16) if "'h" in value else int(value)
            for name, value in values}


def _numbered_names(src: pathlib.Path, kind: str) -> tuple[str, ...]:
    text = (src / "trw_fabric.v").read_text()
    match = re.search(rf"^// {kind}:\s*(.+)$", text, re.M)
    if not match:
        raise ValueError(f"missing generated {kind.lower()} list in {src / 'trw_fabric.v'}")
    pairs = re.findall(r"(\d+)\s+([A-Z][A-Z0-9]*\.[A-Za-z][A-Za-z0-9]*|HOST_IN|HOST_OUT)", match.group(1))
    if not pairs:
        raise ValueError(f"could not parse generated {kind.lower()} list")
    pairs.sort(key=lambda pair: int(pair[0]))
    if [int(index) for index, _ in pairs] != list(range(len(pairs))):
        raise ValueError(f"non-contiguous generated {kind.lower()} indices: {pairs}")
    return tuple(name for _, name in pairs)


class CandidateMap:
    """Candidate-specific maps derived from its generated fabric and header."""

    def __init__(self, rtl_src: str | pathlib.Path):
        self.src = pathlib.Path(rtl_src)
        self.defs = _defines(self.src)
        self.producers = _numbered_names(self.src, "Producers")
        self.consumers = _numbered_names(self.src, "Consumers")
        # The generated consumer comment on each module gives sel -> producer.
        text = (self.src / "trw_fabric.v").read_text()
        sections = re.findall(r"^\s*//\s*\d+\s+((?:L\d+\.I\d+|U\d+\.tx|HOST_OUT)):\s*(.+)$", text, re.M)
        self.legal_sources = {}
        for port, listing in sections:
            self.legal_sources[port] = tuple(re.findall(r"(?:U\d+\.rx|L\d+\.O\d|HOST_IN)", listing))
        if set(self.legal_sources) != set(self.consumers):
            raise ValueError("consumer legal-source comments do not cover the generated consumer list")

    def host_address(self, block: str, logical_name: str | None = None) -> int:
        base = self.defs[f"TRW_HA_{block}"]
        if logical_name is None:
            return base
        names = self.consumers if block in ("PORTS", "DROPPED") else ()
        return base + names.index(logical_name)

    def port_word(self, port: str, source: str, *, enable: bool = True, tap: bool = False,
                  accept: int = 0xF) -> int:
        sel = self.legal_sources[port].index(source)
        return int(enable) | (int(tap) << 1) | (sel << 2) | ((accept & 15) << 6)


def _bits(handle) -> int:
    value = handle.value
    if not value.is_resolvable:
        raise AssertionError(f"unresolved debug tap {handle._name}: {value}")
    return int(value)


def _lane_words(ld: int) -> tuple[int, ...]:
    # trw_chip packs the debug word as
    # {head[35:0], avail[1:0], out_tok[35:0], ... , regs[63:0]}.
    # The two input heads therefore start at bit 144 and availability is at 142.
    avail = (ld >> 142) & 0x3
    i0_avail, i1_avail = avail & 1, (avail >> 1) & 1
    o0_valid, o1_valid = (ld >> 102) & 1, (ld >> 103) & 1
    words = {
        "r0": (ld >> 0) & 0xFFFF,
        "r1": (ld >> 16) & 0xFFFF,
        "r2": (ld >> 32) & 0xFFFF,
        "r3": (ld >> 48) & 0xFFFF,
        "state": (ld >> 64) & 0xF,
        "flags": ((ld >> 68) & 0xF) | (((ld >> 72) & 0x7) << 4),
        "rpc": (ld >> 75) & 0x1FF,
        "rir_status": (((ld >> 84) & 1) << 15) | (((ld >> 101) & 1) << 14),
        "rir": (ld >> 85) & 0xFFFF,
        "channels": avail | (((ld >> 104) & 1) << 2) | (((ld >> 102) & 1) << 3) |
                    (((ld >> 105) & 1) << 4) | (((ld >> 103) & 1) << 5),
        "i0_tag": ((ld >> 160) & 0x3) if i0_avail else 0,
        "i0_data": ((ld >> 144) & 0xFFFF) if i0_avail else 0,
        "i1_tag": ((ld >> 178) & 0x3) if i1_avail else 0,
        "i1_data": ((ld >> 162) & 0xFFFF) if i1_avail else 0,
        "o0_tag": ((ld >> 122) & 0x3) if o0_valid else 0,
        "o0_data": ((ld >> 106) & 0xFFFF) if o0_valid else 0,
        "o1_tag": ((ld >> 140) & 0x3) if o1_valid else 0,
        "o1_data": ((ld >> 124) & 0xFFFF) if o1_valid else 0,
    }
    return tuple(words[name] for name in S.HOST_LANE_WORDS)


def rtl_snapshot(dut, cmap: CandidateMap) -> dict:
    """Candidate RTL state with the same keys and logical naming as model snapshot()."""
    lanes_n = len(cmap.producers)  # replaced below from generated logical lane names
    lane_ids = sorted({int(m.group(1)) for name in cmap.producers
                       if (m := re.fullmatch(r"L(\d+)\.O[01]", name))})
    if not lane_ids:
        raise ValueError("candidate has no lane producers")
    lanes_n = max(lane_ids) + 1
    unit_ids = sorted({int(m.group(1)) for name in cmap.producers
                       if (m := re.fullmatch(r"U(\d+)\.rx", name))})

    lane_bus = _bits(dut.dbg_lane)
    lanes = tuple({"name": f"L{k}", "debug": _lane_words((lane_bus >> (180 * k)) & ((1 << 180) - 1))}
                   for k in range(lanes_n))
    p_valid, p_seq, p_tok = map(_bits, (dut.dbg_p_valid, dut.dbg_p_seq, dut.dbg_p_tok))
    producers = tuple(
        (name, ((p_valid >> i) & 1, (p_seq >> i) & 1,
                (p_tok >> (18 * i + 16)) & 3, (p_tok >> (18 * i)) & 0xFFFF))
        for i, name in enumerate(cmap.producers)
    )
    port_bus, dropped_bus = _bits(dut.dbg_port_state), _bits(dut.dbg_dropped)
    ports = tuple((name, (port_bus >> (10 * i)) & 0x3FF, (dropped_bus >> (8 * i)) & 0xFF)
                  for i, name in enumerate(cmap.consumers))
    overrun, late = _bits(dut.dbg_overrun), _bits(dut.dbg_late)
    flags = tuple(((overrun >> u) & 1) | (((late >> u) & 1) << 1) for u in unit_ids)
    run_mask = _bits(dut.dbg_run)
    return {
        "cycle": _bits(dut.dbg_cycle),
        "run": run_mask | (_bits(dut.dbg_live) << S.HOST_RUN_LIVE_BIT),
        "lanes": lanes,
        "producers": producers,
        "ports": ports,
        "unit_flags": flags,
        "pads": (_bits(dut.uo_out), _bits(dut.uio_out), _bits(dut.uio_oe)),
    }


def model_snapshot(chip) -> dict:
    """Use the main-branch snapshot helper for the model side."""
    state = snapshot(chip)
    # RTL exposes a 16-bit time counter; Python scheduler bookkeeping is unbounded.
    state["cycle"] &= 0xFFFF
    return state
