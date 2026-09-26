"""Load a tripc image into a chip through its host interface (tripsim today; tools/host later)."""


def load(chip, image, run=True):
    # §14 H1 (D-038): pin configuration latches have no reset, so write every unit's block;
    # units the program does not use get the default (off, no pads)
    for u in range(len(chip.pins)):
        chip.pin_config(u, **image["pins"].get(f"U{u}", {}))
    for pad, unit in image["own"]:
        chip.own(pad, unit)
    for port, producer, mode, accept in image["connect"]:
        chip.connect(port, producer, mode, accept)
    for name, lane in image["lanes"].items():
        ln = chip.lanes[int(name[1:])]
        for i in range(4):                  # §14 H1: K latches and registers through the host (§9)
            ln.write_k(i, lane["k"][i])
            ln.write_reg(i, lane["regs"][i])
        # §14 H1: slot latches have no reset, so write every slot; unused ones get V = 0
        for n in range(len(ln.slots)):
            ln.load_slot(n, int(lane["slots"][n], 16) if n < len(lane["slots"]) else 0)
    if image["routines"]:
        chip.load_sram(image["sram"])
    if run:
        chip.run([int(name[1:]) for name in image["lanes"]])
    return chip
