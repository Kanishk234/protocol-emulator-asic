"""Optional white-box diagnostics for scratch hardened-fabric load failures."""

import re
import json
import os
from pathlib import Path
from cocotb.handle import HierarchyObject


def report_loaded_config(dut, words):
    """Audit every exposed mapped configuration bit, without forcing any signal."""
    fabric = dut.user_project.u_fabric
    total_bits = total_unknown = total_mismatch = 0
    tiles = sorted((tile for tile in fabric if isinstance(tile, HierarchyObject)
                    and tile._name.startswith("Tile_X")
                    and re.match(r"Tile_X\d+Y\d+_", tile._name)),
                   key=lambda tile: tile._name)
    rows = 1 + max(int(re.match(r"Tile_X\d+Y(\d+)_", tile._name)[1]) for tile in tiles)
    if words[0] != 0xFAB0FAB1 or words[-1] != 1 << 20:
        raise ValueError("Configuration audit requires a complete framed image")
    expected = {}
    for offset in range(1, len(words) - 1, rows + 1):
        header = words[offset]
        column, select = header >> 27, header & ((1 << 20) - 1)
        if not select or select & (select - 1):
            raise ValueError("Configuration audit requires one selected frame per header")
        frame = select.bit_length() - 1
        for y in range(rows):
            expected[column, y, frame] = words[offset + rows - y]
    for tile in tiles:
        name = tile._name
        bits = [signal for signal in tile
                if re.search(r"ConfigMem\.Inst_frame\d+_bit\d+\.Q$", signal._name)]
        unknown = [signal._name for signal in bits
                   if any(c in str(signal.value).lower() for c in "xz")]
        dut._log.info("CONFIG %s: %d bits, %d unknown; first unknowns %s",
                      name, len(bits), len(unknown), unknown[:8])
        total_bits += len(bits)
        total_unknown += len(unknown)
        x, y = map(int, re.match(r"Tile_X(\d+)Y(\d+)_", name).groups())
        mismatch = []
        for signal in bits:
            if signal._name in unknown:
                continue
            frame, bit = map(int, re.search(r"Inst_frame(\d+)_bit(\d+)\.Q$", signal._name).groups())
            value = (expected[x, y, frame] >> bit) & 1
            if int(signal.value) != value:
                mismatch.append(signal._name)
        total_mismatch += len(mismatch)
        if mismatch:
            dut._log.error("CONFIG MISMATCH %s: %d bits; %s", name, len(mismatch), mismatch[:8])
        for port in ("GCLK_BEG", "A_OUT_top", "A_IN_top", "A_EN_top"):
            try:
                signal = getattr(tile, port)
            except AttributeError:
                continue
            dut._log.info("PORT %s.%s = %s", name, port, signal.value)
    dut._log.info("CONFIG TOTAL: %d bits, %d unknown, %d image mismatches",
                  total_bits, total_unknown, total_mismatch)
    if not total_bits:
        raise RuntimeError("Mapped configuration audit found no storage bits")
    if total_unknown:
        raise AssertionError(f"{total_unknown} mapped configuration bits remain unknown")
    if total_mismatch:
        raise AssertionError(f"{total_mismatch} mapped configuration bits disagree with loaded image")


def report_runtime(dut, label):
    """Localize unknowns at shell, clock/reset and logic-cell boundaries."""
    top = dut.user_project
    for name in ("running", "user_reset", "user_rst_n", "cell_val", "cell_en", "out_q"):
        try:
            signal = getattr(top, name)
        except AttributeError:
            continue
        dut._log.info("RUNTIME %s %s = %s", label, name, signal.value)
    for tile in top.u_fabric:
        if not isinstance(tile, HierarchyObject) or not re.match(r"Tile_X\d+Y\d+_", tile._name):
            continue
        signals = [signal for signal in tile
                   if re.search(r"(?:^GCLK_BEG$|UserCLK|UserReset|\.D$|\.Q$|FABULOUS_LC\.(?:LUT_flop|O)$)", signal._name)
                   and "ConfigMem" not in signal._name]
        unknown = [signal._name for signal in signals
                   if any(c in str(signal.value).lower() for c in "xz")]
        if signals:
            dut._log.info("RUNTIME %s %s: %d state/clock signals, %d unknown; %s",
                          label, tile._name, len(signals), len(unknown), unknown[:12])
        for letter in "ABCDEFGH":
            prefix = f"Inst_L{letter}_FABULOUS_LC."
            try:
                selected = getattr(tile, prefix + "c_out_mux")
                state = getattr(tile, prefix + "LUT_flop")
                output = getattr(tile, prefix + "O")
            except AttributeError:
                continue
            if selected.value.is_resolvable and int(selected.value):
                dut._log.info("REGISTER %s %s L%s: Q=%s O=%s", label,
                              tile._name, letter, state.value, output.value)
    cone_file = os.environ.get("WARP_COMPACT_CONE_JSON")
    if cone_file:
        report_unknown_cone(dut, label, Path(cone_file))
    io_cone = os.environ.get("WARP_COMPACT_IO_CONE_JSON")
    if io_cone:
        module = json.loads(Path(io_cone).read_text())["modules"]["E_IO4_wide"]
        tile = top.u_fabric.Tile_X6Y2_E_IO4_wide
        trace_unknown_cone(dut, label + " UART_TX", module, tile,
                           module["ports"]["B_IN_top"]["bits"][0])


def report_unknown_cone(dut, label, path):
    """Trace one configured flop's unknown D cone using mapped-cell connectivity."""
    module = json.loads(path.read_text())["modules"]["LUT4x8_ha"]
    tile = dut.user_project.u_fabric.Tile_X1Y1_LUT4x8_ha
    target = module["netnames"]["Inst_LB_FABULOUS_LC.LUT_flop"]["bits"][0]
    flop = next(cell for cell in module["cells"].values()
                if any(target in cell["connections"][port]
                       for port, direction in cell["port_directions"].items()
                       if direction == "output"))
    trace_unknown_cone(dut, label + " LB_D", module, tile,
                       flop["connections"]["D"][0])


def trace_unknown_cone(dut, label, module, tile, start):
    """Read-only tile cone; known mux selects exclude inactive data branches."""
    aliases, drivers = {}, {}
    for name, net in module["netnames"].items():
        for index, bit in enumerate(net["bits"]):
            aliases.setdefault(bit, []).append((name, index))
    for name, cell in module["cells"].items():
        for port, direction in cell["port_directions"].items():
            if direction == "output":
                for bit in cell["connections"][port]:
                    drivers[bit] = (name, cell)

    def value(bit):
        if isinstance(bit, str):
            return bit
        for name, index in aliases.get(bit, []):
            try:
                return str(tile[name].value)[-1 - index].lower()
            except (AttributeError, KeyError, IndexError):
                continue
        return "?"

    visited = set()

    def trace(bit, depth):
        if value(bit) in ("0", "1") or bit in visited or len(visited) >= 80:
            return
        visited.add(bit)
        entry = drivers.get(bit)
        names = [f"{name}[{index}]" for name, index in aliases.get(bit, [])][:2]
        if entry is None:
            dut._log.info("CONE %s %s depth=%d %s=%s tile input/constant or no local driver",
                          label, tile._name, depth, names, value(bit))
            return
        name, cell = entry
        inputs = [(port, b) for port, direction in cell["port_directions"].items()
                  if direction == "input" for b in cell["connections"][port]]
        active = inputs
        connections = cell["connections"]
        if cell["type"].startswith("sg13cmos5l_mux2_"):
            select = value(connections["S"][0])
            if select in ("0", "1"):
                active = [("A" + select, connections["A" + select][0])]
        elif cell["type"].startswith("sg13cmos5l_mux4_"):
            s0, s1 = (value(connections[port][0]) for port in ("S0", "S1"))
            if s0 in ("0", "1") and s1 in ("0", "1"):
                port = "A" + str(int(s0) + 2 * int(s1))
                active = [(port, connections[port][0])]
        dut._log.info("CONE %s %s depth=%d %s=%s via %s %s inputs=%s traced=%s", label,
                      tile._name, depth, names, value(bit), name, cell["type"],
                      [(port, value(b)) for port, b in inputs], [port for port, _ in active])
        # State is a boundary: never trace a DFF's feedback into another cycle.
        if "CLK" not in cell["connections"] and "GATE" not in cell["connections"]:
            for _, child in active:
                trace(child, depth + 1)

    trace(start, 0)
    dut._log.info("CONE %s: visited %d unknown nodes (limit 80)", label, len(visited))
