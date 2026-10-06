"""Optional white-box diagnostics for scratch hardened-fabric load failures."""

import re
import json
import os
from pathlib import Path
from functools import lru_cache
from itertools import product
import cocotb
from cocotb.triggers import FallingEdge, RisingEdge, ReadOnly

_timer_watch_started = False
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
    if os.environ.get("WARP_COMPACT_SHADOW_RTL") == "1":
        report_shadow(dut, label)
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
    full_cone = os.environ.get("WARP_COMPACT_FABRIC_CONE_JSON")
    if full_cone:
        module = read_cone_json(full_cone)["modules"]["LUT4x8_ha_C2"]
        tile = top.u_fabric.Tile_X2Y3_LUT4x8_ha_C2
        prefix = "Inst_LH_FABULOUS_LC."
        state_bit = module["netnames"][prefix + "LUT_flop"]["bits"][0]
        flop = next(cell for cell in module["cells"].values()
                    if state_bit in cell["connections"].get("Q", []))
        for name in ("LUT_flop", "c_out_mux", "c_reset_value", "O"):
            dut._log.info("UART SOURCE %s %s %s=%s", label, tile._name,
                          name, tile[prefix + name].value)
        for port in ("D", "RESET_B"):
            trace_unknown_cone(dut, label + " UART_SOURCE_" + port, module,
                               tile, flop["connections"][port][0])
        module = read_cone_json(full_cone)["modules"]["PRIM2T2S_C2"]
        tile = top.u_fabric.Tile_X2Y2_PRIM2T2S_C2
        global _timer_watch_started
        if not _timer_watch_started:
            _timer_watch_started = True
            cocotb.start_soon(watch_timer_first_unknown(dut, module, tile))
        prefix = "Inst_TB_wp_timer."
        count = "".join(str(tile[prefix + f"count[{i}]"].value) for i in range(15, -1, -1))
        dut._log.info("UART TIMER %s count=%s armed=%s", label, count, tile[prefix + "armed"].value)
        # Physical synthesis removed primitive port aliases. Trace preserved
        # state's actual D inputs instead of inventing reset/control bindings.
        for name in ("count[0]", "armed"):
            state = module["netnames"][prefix + name]["bits"][0]
            flop = next(cell for cell in module["cells"].values()
                        if state in cell["connections"].get("Q", []))
            trace_unknown_cone(dut, label + " UART_TIMER_" + name + "_D", module,
                               tile, flop["connections"]["D"][0])


async def watch_timer_first_unknown(dut, module, tile):
    """Retain stable pre-edge timer inputs, then report its first known→X edge."""
    prefix = "Inst_TB_wp_timer."
    aliases = {}
    for name, net in module["netnames"].items():
        for index, bit in enumerate(net["bits"]):
            aliases.setdefault(bit, []).append((name, index))
    flops = []
    for i in range(16):
        bit = module["netnames"][prefix + f"count[{i}]"]["bits"][0]
        flops.append(next(cell for cell in module["cells"].values()
                          if bit in cell["connections"].get("Q", [])))

    def value(bit):
        if isinstance(bit, str):
            return bit
        for name, index in aliases.get(bit, []):
            try:
                return str(tile[name].value)[-1-index].lower()
            except (AttributeError, KeyError, IndexError):
                continue
        return "?"

    def counter():
        return "".join(str(tile[prefix + f"count[{i}]"].value).lower()
                       for i in range(15, -1, -1))

    preedge_reported = False
    for _ in range(12000):
        await FallingEdge(dut.clk)
        await ReadOnly()
        before = counter()
        data = "".join(value(flop["connections"]["D"][0]) for flop in reversed(flops))
        resets = "".join(value(flop["connections"]["RESET_B"][0]) for flop in reversed(flops))
        if (not preedge_reported and all(c in "01" for c in before)
                and any(c not in "01" for c in data) and resets == "1" * 16):
            preedge_reported = True
            dut._log.info("FIRST TIMER UNKNOWN INPUT: count=%s D=%s RESET_B=%s", before, data, resets)
            words = [int(word, 16) for word in Path(os.environ["WARP_COMPACT_WORDS"]).read_text().split()]
            report_loaded_config(dut, words)
            report_runtime(dut, "timer unknown input before corrupt edge")
        await RisingEdge(dut.clk)
        await ReadOnly()
        after = counter()
        if all(c in "01" for c in before) and any(c not in "01" for c in after):
            dut._log.info("FIRST TIMER X: stable pre-edge count=%s D=%s RESET_B=%s; post-edge count=%s",
                          before, data, resets, after)
            report_runtime(dut, "first timer known-to-X edge")
            return


def report_shadow(dut, label):
    """Compare separate RTL state/routes at the same real loaded clock sample."""
    fabric = dut.rtl_shadow
    timer_tile = fabric.Tile_X2Y2_PRIM2T2S_C2
    timer = timer_tile.Inst_TB_wp_timer
    dut._log.info("SHADOW %s timer count=%s armed=%s rst=%s load=%s half=%s en=%s tc=%s",
                  label, timer.count.value, timer.armed.value, timer_tile.TB_rst.value,
                  timer_tile.TB_load.value, timer_tile.TB_half.value, timer_tile.TB_en.value,
                  timer_tile.TB_tc.value)
    for instance, ports in (("Tile_X2Y2_PRIM2T2S_C2", ("N1END", "S1BEG", "E1BEG")),
                            ("Tile_X2Y3_LUT4x8_ha_C2", ("N1BEG", "S1BEG", "N2MID"))):
        native = dut.user_project.u_fabric[instance]
        companion = fabric[instance]
        for port in ports:
            dut._log.info("SHADOW %s %s.%s mapped=%s rtl=%s", label, instance, port,
                          native[port].value, companion[port].value)
    modules = read_cone_json(os.environ["WARP_COMPACT_FABRIC_CONE_JSON"])["modules"]
    macro = modules[os.environ["WARP_COMPACT_FABRIC_TOP"]]
    differences = 0
    for instance, cell in macro["cells"].items():
        if not instance.startswith("Tile_X") or cell["type"] not in modules:
            continue
        native = dut.user_project.u_fabric[instance]
        companion = dut["native_inputs_" + instance]
        for name, port in modules[cell["type"]]["ports"].items():
            if port["direction"] != "output" or name.startswith(("Frame", "GCLK", "GSR", "GEN")):
                continue
            actual, expected = str(native[name].value).lower(), str(companion[name].value).lower()
            if len(actual) != len(expected):
                raise RuntimeError("Matched-input companion output width differs")
            mismatches = [(len(actual)-1-index, a, b) for index, (a, b) in enumerate(zip(actual, expected))
                          if b in "01" and a != b]
            if mismatches:
                differences += 1
                if differences <= 24:
                    dut._log.info("TILE SAME INPUT %s %s.%s mapped=%s rtl=%s differences=%s",
                                  label, instance, name, actual, expected, mismatches)
    dut._log.info("TILE SAME INPUT %s: %d output ports with differing RTL-known bits (first24 logged)",
                  label, differences)
    local = dut.native_inputs_Tile_X2Y2_PRIM2T2S_C2
    timer = local.Inst_TB_wp_timer
    dut._log.info("LOCAL TIMER %s count=%s armed=%s rst=%s load=%s half=%s en=%s cfg=%s",
                  label, timer.count.value, timer.armed.value, timer.rst.value,
                  timer.load.value, timer.half.value, timer.en.value, timer.ConfigBits.value)
    # Read-only local truth-table checks. Enumerating every binary completion
    # avoids interpreting RTL if/case optimism as evidence of a correct gate.
    for instance in ("Tile_X1Y2_LUT4x8_ha", "Tile_X2Y1_LUT4x8_ha_C2",
                     "Tile_X2Y3_LUT4x8_ha_C2"):
        native = dut.user_project.u_fabric[instance]
        local = dut["native_inputs_" + instance]
        for letter in "ABCDEFGH":
            name = "Inst_L" + letter + "_FABULOUS_LC"
            cell = local[name]
            index, values = str(cell.LUT_index.value).lower(), str(cell.LUT_values.value).lower()
            possibilities = lut_completion_values(index, values)
            actual = {}
            for signal in ("LUT_flop", "O", "LUT_out", "c_out_mux", "c_reset_value"):
                try:
                    actual[signal] = str(getattr(native, name + "." + signal).value).lower()
                except AttributeError:
                    pass  # Synthesis may remove this alias; do not invent it.
            dut._log.info("LOCAL LUT %s %s L%s I=%s index=%s INIT=%s SR=%s EN=%s "
                          "cfg=%s Q=%s comb=%s O=%s binary_outputs=%s mapped=%s",
                          label, instance, letter, cell.I.value, index, values,
                          cell.SR.value, cell.EN.value, cell.ConfigBits.value,
                          cell.LUT_flop.value, cell.LUT_out.value, cell.O.value,
                          sorted(possibilities), actual)
            if (label == "timer unknown input before corrupt edge"
                    and cell.c_out_mux.value.is_resolvable and not int(cell.c_out_mux.value)
                    and len(possibilities) == 1 and actual.get("O") in ("x", "z")):
                module = modules[macro["cells"][instance]["type"]]
                bit = module["netnames"][name + ".O"]["bits"][0]
                trace_unknown_cone(dut, "CONSTANT LUT " + instance + " L" + letter,
                                   module, native, bit)


def lut_completion_values(index, values):
    """Conservative output set for a LUT with partially unknown index/INIT."""
    if len(values) != 1 << len(index) or any(c not in "01xz" for c in index + values):
        raise ValueError("Invalid LUT index/truth-table widths or digits")
    outputs = set()
    choices = [(c,) if c in "01" else ("0", "1") for c in index]
    for bits in product(*choices):
        value = values[-1 - int("".join(bits), 2)]
        outputs.update((value,) if value in "01" else ("0", "1"))
    return outputs


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


@lru_cache(maxsize=4)
def read_cone_json(path):
    return json.loads(Path(path).read_text())


def sensitive_ports(kind, values):
    """Conservative Boolean sensitivity for gates with known controlling inputs."""
    if kind == "mux2":
        function = lambda v: v["A" + str(v["S"])]
    elif kind == "mux4":
        function = lambda v: v["A" + str(v["S0"] + 2 * v["S1"])]
    elif kind in ("a21o", "a21oi"):
        function = lambda v: (v["A1"] and v["A2"]) or v["B1"]
    elif kind in ("o21a", "o21ai"):
        function = lambda v: (v["A1"] or v["A2"]) and v["B1"]
    elif kind in ("a22o", "a22oi"):
        function = lambda v: (v["A1"] and v["A2"]) or (v["B1"] and v["B2"])
    elif kind in ("o22a", "o22ai"):
        function = lambda v: (v["A1"] or v["A2"]) and (v["B1"] or v["B2"])
    elif kind in ("a221o", "a221oi"):
        function = lambda v: (v["A1"] and v["A2"]) or (v["B1"] and v["B2"]) or v["C1"]
    elif re.fullmatch(r"(?:and|nand|or|nor)[234]", kind):
        function = (lambda v: all(v.values())) if "and" in kind else (lambda v: any(v.values()))
    elif kind == "nand2b":
        function = lambda v: (not v["A_N"]) and v["B"]
    elif kind == "nor2b":
        function = lambda v: v["A"] or (not v["B_N"])
    else:
        return set(values)
    # Output inversion does not change sensitivity. Treat other unknown pins
    # independently: this can overtrace correlated inputs, never remove one
    # merely because the current unknown has a convenient assumed value.
    known = {port: int(v) for port, v in values.items() if v in ("0", "1")}
    unknown = [port for port in values if port not in known]
    active = set(known)
    for port in unknown:
        others = [name for name in unknown if name != port]
        for assignment in product((0, 1), repeat=len(others)):
            pins = dict(known, **dict(zip(others, assignment)))
            if bool(function(dict(pins, **{port: 0}))) != bool(function(dict(pins, **{port: 1}))):
                active.add(port)
                break
    return active


def trace_unknown_cone(dut, label, module, tile, start):
    """Follow selected data across actual macro wiring, stopping at state."""
    fabric_file = os.environ.get("WARP_COMPACT_FABRIC_CONE_JSON")
    fabric = read_cone_json(fabric_file)["modules"] if fabric_file else {}
    macro = fabric.get(os.environ.get("WARP_COMPACT_FABRIC_TOP"), {})
    macro_drivers = {}
    for instance, cell in macro.get("cells", {}).items():
        for port, direction in cell["port_directions"].items():
            if direction == "output":
                for index, bit in enumerate(cell["connections"][port]):
                    macro_drivers.setdefault(bit, []).append((instance, cell["type"], port, index))
    indexes = {}

    def index_for(mod):
        key = id(mod)
        if key not in indexes:
            aliases, drivers, inputs = {}, {}, {}
            for name, net in mod["netnames"].items():
                for index, bit in enumerate(net["bits"]):
                    aliases.setdefault(bit, []).append((name, index))
            for name, cell in mod["cells"].items():
                for port, direction in cell["port_directions"].items():
                    if direction == "output":
                        for bit in cell["connections"][port]:
                            drivers[bit] = (name, cell)
            for name, port in mod["ports"].items():
                if port["direction"] == "input":
                    for index, bit in enumerate(port["bits"]):
                        inputs.setdefault(bit, []).append((name, index))
            indexes[key] = aliases, drivers, inputs
        return indexes[key]

    def value(bit, mod, handle):
        if isinstance(bit, str):
            return bit
        for name, index in index_for(mod)[0].get(bit, []):
            try:
                return str(handle[name].value)[-1 - index].lower()
            except (AttributeError, KeyError, IndexError):
                continue
        return "?"

    visited = set()

    def trace(bit, depth, mod, handle):
        val = value(bit, mod, handle)
        key = (handle._name, bit)
        if val in ("0", "1") or key in visited or len(visited) >= 160:
            return
        visited.add(key)
        aliases, drivers, ports = index_for(mod)
        entry = drivers.get(bit)
        names = [f"{name}[{index}]" for name, index in aliases.get(bit, [])][:2]
        if entry is None:
            instance = macro.get("cells", {}).get(handle._name)
            for port, index in ports.get(bit, []):
                if instance is None:
                    break
                wire = instance["connections"][port][index]
                sources = macro_drivers.get(wire, [])
                if len(sources) != 1:
                    continue
                source, kind, source_port, source_index = sources[0]
                if kind not in fabric:
                    continue
                dut._log.info("CROSS %s %s.%s[%d] <- %s.%s[%d]", label,
                              handle._name, port, index, source, source_port, source_index)
                source_mod = fabric[kind]
                source_bit = source_mod["ports"][source_port]["bits"][source_index]
                trace(source_bit, depth + 1, source_mod, dut.user_project.u_fabric[source])
                return
            dut._log.info("CONE %s %s depth=%d %s=%s tile input/constant or no unique traced driver",
                          label, handle._name, depth, names, val)
            return
        name, cell = entry
        inputs = [(port, b) for port, direction in cell["port_directions"].items()
                  if direction == "input" for b in cell["connections"][port]]
        active = inputs
        connections = cell["connections"]
        if cell["type"].startswith("sg13cmos5l_mux2_"):
            select = value(connections["S"][0], mod, handle)
            if select in ("0", "1"):
                active = [("A" + select, connections["A" + select][0])]
            else:
                sensitive = sensitive_ports("mux2", {port: value(b, mod, handle) for port, b in inputs})
                active = [(port, b) for port, b in inputs if port in sensitive]
        elif cell["type"].startswith("sg13cmos5l_mux4_"):
            s0, s1 = (value(connections[port][0], mod, handle) for port in ("S0", "S1"))
            if s0 in ("0", "1") and s1 in ("0", "1"):
                port = "A" + str(int(s0) + 2 * int(s1))
                active = [(port, connections[port][0])]
            else:
                sensitive = sensitive_ports("mux4", {port: value(b, mod, handle) for port, b in inputs})
                active = [(port, b) for port, b in inputs if port in sensitive]
        elif cell["type"].startswith("sg13cmos5l_"):
            kind = cell["type"][len("sg13cmos5l_"):].rsplit("_", 1)[0]
            sensitive = sensitive_ports(kind, {port: value(b, mod, handle) for port, b in inputs})
            active = [(port, b) for port, b in inputs if port in sensitive]
        dut._log.info("CONE %s %s depth=%d %s=%s via %s %s inputs=%s traced=%s", label,
                      handle._name, depth, names, val, name, cell["type"],
                      [(port, value(b, mod, handle)) for port, b in inputs],
                      [port for port, _ in active])
        if "CLK" not in connections and "GATE" not in connections:
            for _, child in active:
                trace(child, depth + 1, mod, handle)

    trace(start, 0, module, tile)
    dut._log.info("CONE %s: visited %d unknown nodes (limit 160)", label, len(visited))
