"""Load a tripc image into a chip through its host interface (tripsim today; tools/host later)."""


def load(chip, image, run=True):
    for unit, cfg in image["pins"].items():
        chip.pin_config(int(unit[1:]), **cfg)
    for pad, unit in image["own"]:
        chip.own(pad, unit)
    for port, producer, mode, accept in image["connect"]:
        chip.connect(port, producer, mode, accept)
    for name, lane in image["lanes"].items():
        ln = chip.lanes[int(name[1:])]
        ln.k[:] = lane["k"]
        ln.regs[:] = lane["regs"]
        # §14 H1: slot latches have no reset, so write every slot; unused ones get V = 0
        for n in range(len(ln.slots)):
            ln.load_slot(n, int(lane["slots"][n], 16) if n < len(lane["slots"]) else 0)
    if image["routines"]:
        chip.load_sram(image["sram"])
    if run:
        chip.run([int(name[1:]) for name in image["lanes"]])
    return chip
