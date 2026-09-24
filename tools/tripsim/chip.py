"""TRIPWIRE chip model: lanes, fabric, pin units, SRAM rotation, host FIFOs, pads.

Token-level and cycle-accurate, parameterised for architecture exploration
(DECISIONS D-008). The host interface is modelled at the register level (direct
calls); the SPI transport of ARCHITECTURE.md §9 is not modelled here.

Pads are numbered 0-7 ui_in, 8-15 uo_out, 16-23 uio. ui[4..6] and uo[6..7] belong
to the host port (§10) and cannot be attached to pin units.
"""

import os
from collections import deque

import tripwire_spec as _S

from .fabric import Fabric
from .lane import Lane
from .pinunit import PinUnit

PAD_UI, PAD_UO, PAD_UIO = (_S.PAD_GROUPS[g][0] for g in ("ui", "uo", "uio"))
HOST_PADS = set(_S.HOST_PADS)


class Sram:
    def __init__(self, words):
        self.mem = [0] * words
        self.reads = self.writes = 0

    def read(self, addr):
        self.reads += 1
        return self.mem[addr % len(self.mem)]

    def write(self, addr, value):
        self.writes += 1
        self.mem[addr % len(self.mem)] = value & 0xFFFF


class Chip:
    def __init__(self, lanes=3, slots=12, pin_units=6, sram_words=512,
                 fire_period=None, host_fifo_depth=16):
        if fire_period is None:                 # R1 experiments: TRIPSIM_FIRE_PERIOD=2 for every chip
            fire_period = int(os.environ.get("TRIPSIM_FIRE_PERIOD", "1"))
        self.fabric = f = Fabric()
        for u in range(pin_units):
            f.producer(f"U{u}.rx")
            f.port(f"U{u}.tx")
        for k in range(lanes):
            for o in ("O0", "O1"):
                f.producer(f"L{k}.{o}")
            for i in ("I0", "I1"):
                f.port(f"L{k}.{i}")
        f.producer("HOST_IN")
        f.port("HOST_OUT")
        self.lanes = [Lane(k, slots, [f.ports[f"L{k}.I0"], f.ports[f"L{k}.I1"]],
                           [f.producers[f"L{k}.O0"], f.producers[f"L{k}.O1"]], fire_period)
                      for k in range(lanes)]
        self.pins = [PinUnit(u, f.ports[f"U{u}.tx"], f.producers[f"U{u}.rx"])
                     for u in range(pin_units)]
        self.sram = Sram(sram_words)
        self.cycle = 0
        self.host_in = deque()
        self.host_out = deque()
        self.host_fifo_depth = host_fifo_depth
        self.owner = [None] * 24
        self.ui_in = 0
        self.uio_in = 0xFF              # environment drives the resolved uio wires
        self._sync = [(0, 0xFF), (0, 0xFF)]  # 2-FF synchronisers: (ui, uio) of clocks n-1, n-2
        self.observers = []

    # ------------------------------------------------------------ host API
    def connect(self, port, producer, mode="blocking", accept=0xF):
        self.fabric.connect(port, producer, mode, accept)

    def pin_config(self, unit, **cfg):
        for key in ("pin_a", "pin_b", "pin_c", "pin_s", "pin_n"):
            pad = cfg.get(key)
            if pad is not None and pad in HOST_PADS:
                raise ValueError(f"pad {pad} belongs to the host port")
        self.pins[unit].configure(**cfg)

    def own(self, pad, unit):
        """Output ownership (§7.1): only the owner's TX half drives the pad."""
        if pad in HOST_PADS or pad < PAD_UO:
            raise ValueError(f"pad {pad} is not drivable")
        self.owner[pad] = unit

    def load_sram(self, image, base=0):
        for i, w in enumerate(image):
            self.sram.mem[base + i] = w & 0xFFFF

    def run(self, lanes=None):
        for k in (range(len(self.lanes)) if lanes is None else lanes):
            self.lanes[k].running = True

    def halt(self, lanes=None):
        for k in (range(len(self.lanes)) if lanes is None else lanes):
            self.lanes[k].running = False

    def settle_inputs(self, ui=None, uio=None):
        """Pads held stable through reset: set the inputs and both synchroniser stages."""
        if ui is not None:
            self.ui_in = ui
        if uio is not None:
            self.uio_in = uio
        self._sync = [(self.ui_in, self.uio_in)] * 2

    def host_push(self, data, tag=0):
        self.host_in.append((tag, data))

    # ---------------------------------------------------------------- pads
    def synced(self, pad):
        """Level a pin unit sees on `pad` this clock.

        ui/uio pads: through the 2-FF synchroniser (§14 P1). uo pads are output-only;
        a unit linked to one (e.g. SPI data linked to our own SCK) sees its driven
        value directly, with no synchroniser (§14 P7, draft).
        """
        if pad is None:
            return None
        ui, uio = self._sync[1]
        if PAD_UI <= pad < PAD_UO:
            return (ui >> pad) & 1
        if PAD_UIO <= pad < PAD_UIO + 8:
            return (uio >> (pad - PAD_UIO)) & 1
        return (self.outputs()[0] >> (pad - PAD_UO)) & 1

    def outputs(self):
        """(uo_out, uio_out, uio_oe) from the registered pin-unit outputs."""
        uo = uio = oe = 0
        for pad, unit in enumerate(self.owner):
            if unit is None:
                continue
            u_ = self.pins[unit]
            v, e = u_.pad_drive_n() if pad == u_.cfg.pin_n else u_.pad_drive()
            if PAD_UO <= pad < PAD_UIO:
                uo |= v << (pad - PAD_UO)
            else:
                uio |= v << (pad - PAD_UIO)
                oe |= e << (pad - PAD_UIO)
        return uo, uio, oe

    # ---------------------------------------------------------------- clock
    def step(self):
        now = self.cycle
        for lane in self.lanes:
            lane.compute_exec(now)
        for lane in self.lanes:
            lane.compute_eval(now)
        rot = now % 4
        if rot < len(self.lanes) and self.lanes[rot].running:
            self.lanes[rot].mem_access(self.sram)
        for u in self.pins:
            sense = u.cfg.pin_a if u.cfg.pin_s is None else u.cfg.pin_s
            a, b = self.synced(sense), self.synced(u.cfg.pin_b)
            u.compute_rx(now, a, b, self.synced(u.cfg.pin_c))
            u.compute_tx(now, b, a)
        hin = self.fabric.producers["HOST_IN"]
        if self.host_in and hin.free():
            hin.load(*self.host_in.popleft())
        hout = self.fabric.ports["HOST_OUT"]
        if hout.avail() and len(self.host_out) < self.host_fifo_depth:
            self.host_out.append(hout.head())
            hout.take()
        # clock edge
        self.fabric.commit()
        for lane in self.lanes:
            lane.commit()
        for u in self.pins:
            u.commit()
        self._sync = [(self.ui_in, self.uio_in), self._sync[0]]
        self.cycle += 1
        for obs in self.observers:
            obs(self)

    def run_for(self, n, env=None):
        """Step n clocks; env(chip) sets ui_in/uio_in before each clock."""
        for _ in range(n):
            if env is not None:
                env(self)
            self.step()
