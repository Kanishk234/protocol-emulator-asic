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
        for n, word in enumerate(lane["slots"]):
            ln.load_slot(n, int(word, 16))
    if image["routines"]:
        chip.load_sram(image["sram"])
    if run:
        chip.run([int(name[1:]) for name in image["lanes"]])
    return chip
