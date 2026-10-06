"""Build a separately configured RTL companion; never edit mapped/upstream inputs."""
import json
import os
from pathlib import Path
import re


def prepare_shadow(root, library, fabric_rtl, tiles, sim):
    originals = [fabric_rtl, library / "models_pack.v"]
    for tile in sorted(tiles):
        originals.extend(sorted((library / "tiles/tiny" / tile).glob("*.v")))
    for primitive in ("FABULOUS_LC", "IOBUF", "GBUF", "SYS_RESET"):
        originals.append(library / "primitives" / primitive / "fabulous" / f"{primitive}.v")
    originals.extend(sorted((root / "arch/prims").glob("*.v")))
    texts = [path.read_text() for path in originals]
    modules = {name for text in texts for name in re.findall(r"(?m)^\s*module\s+(\w+)", text)}
    names = {name: name + "_shadow" for name in modules}
    pattern = re.compile(r"\b(?:" + "|".join(re.escape(name) for name in sorted(modules, key=len, reverse=True)) + r")\b")
    directory = sim / "shadow_sources"
    directory.mkdir(exist_ok=False)
    sources = []
    for index, (original, text) in enumerate(zip(originals, texts)):
        target = directory / f"{index:03d}_{original.name}"
        target.write_text(pattern.sub(lambda match: names[match[0]], text))
        sources.append(target)
    top = os.environ["WARP_COMPACT_FABRIC_TOP"]
    macro = json.loads(Path(os.environ["WARP_COMPACT_FABRIC_CONE_JSON"]).read_text())["modules"][top]
    connections = [f".{name}(user_project.u_fabric.{name})" if port["direction"] == "input"
                   else f".{name}()" for name, port in macro["ports"].items()]
    instance = names[top] + " rtl_shadow(" + ",\n".join(connections) + ");\n"
    # Tile-local companions receive the *mapped tile's* actual inputs. Unlike
    # the whole RTL fabric above, they cannot hide a bad incoming route.
    design = json.loads(Path(os.environ["WARP_COMPACT_FABRIC_CONE_JSON"]).read_text())["modules"]
    for cell_name, cell in macro["cells"].items():
        if not cell_name.startswith("Tile_X") or cell["type"] not in names:
            continue
        ports = design[cell["type"]]["ports"]
        connections = [f".{name}(user_project.u_fabric.{cell_name}.{name})"
                       if port["direction"] == "input" else f".{name}()"
                       for name, port in ports.items()]
        instance += names[cell["type"]] + " native_inputs_" + cell_name + "(" + ",\n".join(connections) + ");\n"
    # Same D-023 routing pulse as the ordinary RTL control. No storage,
    # configuration or user state is forced in either fabric.
    refs = ["rtl_shadow." + match[1] for match in re.finditer(
        r"(?m)^\s*wire\s*(?:\[[^\]]*\])?\s*(Tile_X\d+Y\d+_\w+)\s*;", texts[0])
        if not match[1].split("_", 2)[2].startswith(("FrameData", "FrameStrobe"))]
    if not refs:
        raise RuntimeError("No companion routing nets found")
    return sources, instance, refs
