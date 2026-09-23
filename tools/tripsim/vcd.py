"""Write pad activity to a VCD so sigrok decoders can check model runs."""

CLK_NS = 20  # 50 MHz


class VcdRecorder:
    """Chip observer. signals: {name: fn(chip) -> 0/1}, sampled after every clock edge."""

    def __init__(self, signals):
        self.signals = signals
        self.changes = []            # (time_ns, index, value)
        self._last = [None] * len(signals)

    def __call__(self, chip):
        t = chip.cycle * CLK_NS
        for i, fn in enumerate(self.signals.values()):
            v = fn(chip)
            if v != self._last[i]:
                self.changes.append((t, i, v))
                self._last[i] = v

    def write(self, path):
        ids = [chr(33 + i) for i in range(len(self.signals))]
        with open(path, "w") as f:
            f.write("$timescale 1ns $end\n$scope module tripsim $end\n")
            for name, ident in zip(self.signals, ids):
                f.write(f"$var wire 1 {ident} {name} $end\n")
            f.write("$upscope $end\n$enddefinitions $end\n")
            last_t = None
            for t, i, v in self.changes:
                if t != last_t:
                    f.write(f"#{t}\n")
                    last_t = t
                f.write(f"{v}{ids[i]}\n")
            if self.changes:
                f.write(f"#{self.changes[-1][0] + CLK_NS}\n")
