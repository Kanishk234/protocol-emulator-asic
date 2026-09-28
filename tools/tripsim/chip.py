"""TRIPWIRE chip model: lanes, fabric, pin units, SRAM rotation, host FIFOs, pads.

Token-level and cycle-accurate, parameterised for architecture exploration
(DECISIONS D-008). The host interface is modelled at the register level (direct
calls); the SPI transport of ARCHITECTURE.md §9 is not modelled here.

Pads are numbered 0-7 ui_in, 8-15 uo_out, 16-23 uio. The host port's pads (§10:
ui[4..6], uo[3], uo[6]) cannot be attached to pin units.
"""

import dataclasses
import os
from collections import deque

import tripwire_spec as _S

from .fabric import Fabric
from .lane import Lane
from . import pinregs
from .pinunit import PinConfig, PinUnit

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
    def __init__(self, lanes=None, slots=12, pin_units=None, sram_words=512,
                 fire_period=None, host_fifo_depth=16):
        lanes = sum(name.startswith("L") and name.endswith(".I0") for name in _S.LEGAL_SOURCES) if lanes is None else lanes
        pin_units = len(_S.PIN_UNIT_FEATURES) if pin_units is None else pin_units
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
        self.live = False
        self.host_in = deque()
        self.host_out = deque()
        self.host_fifo_depth = host_fifo_depth
        self.owner = [None] * 24
        self.pin_regs = [pinregs.encode(PinConfig(), u) for u in range(pin_units)]
        self.pin_written = set()        # §14 H1 (D-038): units whose configuration block the host wrote
        self.ui_in = 0
        self.uio_in = 0xFF              # environment drives the resolved uio wires
        self._sync = [(0, 0xFF), (0, 0xFF)]  # 2-FF synchronisers: (ui, uio) of clocks n-1, n-2
        self.observers = []
        self.unit_flags = [0] * pin_units
        self.irq_en = 0
        self.port_names = _S.FABRIC_CONSUMERS
        self.producer_names = _S.FABRIC_PRODUCERS

    # ------------------------------------------------------------ host API
    def connect(self, port, producer, mode="blocking", accept=0xF):
        self.fabric.connect(port, producer, mode, accept)
        if port in _S.LEGAL_SOURCES:
            sources = _S.LEGAL_SOURCES[port]
            self.fabric.ports[port].host_sel = sources.index(producer) if producer in sources else len(sources)

    def pin_config(self, unit, **cfg):
        for key in ("pin_a", "pin_b", "pin_c", "pin_s", "pin_n"):
            pad = cfg.get(key)
            if pad is not None and pad in HOST_PADS:
                raise ValueError(f"pad {pad} belongs to the host port")
        # §7.2 (D-036): through the register encoding, so only representable values run;
        # a lean unit (D-040) rejects the features it does not have
        words = pinregs.encode(PinConfig(**cfg), unit)
        self.pin_regs[unit] = words
        self.pin_written.add(unit)
        self.pins[unit].configure(now=self.cycle, **dataclasses.asdict(pinregs.decode(words, unit)))

    def own(self, pad, unit):
        """Output ownership (§7.1): only the owner's TX half drives the pad."""
        if pad in HOST_PADS or pad < PAD_UO:
            raise ValueError(f"pad {pad} is not drivable")
        self.owner[pad] = unit

    def load_sram(self, image, base=0):
        for i, w in enumerate(image):
            self.sram.mem[base + i] = w & 0xFFFF

    def run(self, lanes=None):
        selected = list(range(len(self.lanes)) if lanes is None else lanes)
        if selected:
            self.live = True
        for k in selected:
            self.lanes[k].running = True

    def halt(self, lanes=None):
        for k in (range(len(self.lanes)) if lanes is None else lanes):
            self.lanes[k].running = False

    def step_lane(self, k):
        """STEP (§14 H2): on a halted lane, one EVAL now and its EXEC in the next clock."""
        lane = self.lanes[k]
        if lane.running:
            raise RuntimeError("STEP needs a halted lane")
        self.live = True
        lane.stepping = True
        self.step()

    def settle_inputs(self, ui=None, uio=None):
        """Pads held stable through reset: set the inputs and both synchroniser stages."""
        if ui is not None:
            self.ui_in = ui
        if uio is not None:
            self.uio_in = uio
        self._sync = [(self.ui_in, self.uio_in)] * 2

    def host_push(self, data, tag=0):
        self.host_in.append((tag, data))

    def _map_block(self, name, address):
        base, words = _S.HOST_MAP[name]
        return address - base if base <= address < base + words else None

    def host_read(self, address):
        """Read one word through the D-046 register map."""
        address &= 0xFFFF
        if address == _S.HOST_MAP["time"][0]: return self.cycle & 0xFFFF
        if address == _S.HOST_MAP["id"][0]: return _S.HOST_ID
        if address == _S.HOST_MAP["version"][0]:
            major, minor = (int(v) for v in _S.VERSION.split("."))
            return (major << 8) | minor
        if address == _S.HOST_MAP["run"][0]:
            return (sum(int(l.running) << i for i, l in enumerate(self.lanes)) |
                    (int(self.live) << _S.HOST_RUN_LIVE_BIT))
        if address == _S.HOST_MAP["irq_en"][0]: return self.irq_en
        if address == _S.HOST_MAP["irq_status"][0]:
            status = sum(bool(u.flags["OVERRUN"] or u.flags["LATE"]) << i for i, u in enumerate(self.pins))
            status |= int(bool(self.host_out)) << _S.HOST_IRQ_BITS["host_out"]
            hin = self.fabric.producers["HOST_IN"]
            status |= int(hin.free() and hin._load is None) << _S.HOST_IRQ_BITS["host_in"]
            status |= int(any(c.dropped for c in self.fabric.ports.values())) << _S.HOST_IRQ_BITS["dropped"]
            return status
        i = self._map_block("unit_flags", address)
        if i is not None: return int(self.pins[i].flags["OVERRUN"]) | (int(self.pins[i].flags["LATE"]) << 1)
        i = self._map_block("ports", address)
        if i is not None:
            c = self.fabric.ports[self.port_names[i]]
            sel = getattr(c, "host_sel", 0)
            return int(c.en) | (int(not c.blocking) << 1) | (sel << 2) | ((c.accept & 15) << 6)
        i = self._map_block("dropped", address)
        if i is not None: return self.fabric.ports[self.port_names[i]].dropped
        i = self._map_block("lanes", address)
        if i is not None:
            lane, word = divmod(i, _S.HOST_LANE_STRIDE)
            l = self.lanes[lane]
            names = _S.HOST_LANE_WORDS
            name = names[word] if word < len(names) else None
            if name in ("r0", "r1", "r2", "r3"): return l.regs[int(name[1])]
            if name == "state": return l.state
            if name == "flags": return l._flags4() | (l._pend4() << 4)
            if name == "rpc": return l.rpc
            if name == "rir_status": return int(l.rir is not None) << 15 | int(l.rz) << 14
            if name == "rir":
                if l.rir is None: return 0
                return l.rir[1] if l.rir[0] == "instr" else l.rir[2]
            if name == "channels":
                return (int(l.inp[0].avail()) | (int(l.inp[1].avail()) << 1) |
                        ((l.out[0].seq & 1) << 2) | (int(bool(l.out[0].valid)) << 3) |
                        ((l.out[1].seq & 1) << 4) | (int(bool(l.out[1].valid)) << 5))
            if name.endswith("_tag") or name.endswith("_data"):
                key, field = name[:2], name[3:]
                p = l.inp[int(key[1])] if key[0] == "i" else l.out[int(key[1])]
                if key[0] == "i":
                    if not p.avail(): return 0
                    tag, data = p.head()
                else:
                    if not p.valid: return 0
                    tag, data = p.tag, p.data
                return tag if field == "tag" else data
        if address == _S.HOST_MAP["host_status"][0]:
            p = self.fabric.ports["HOST_OUT"]
            hin = self.fabric.producers["HOST_IN"]
            return (int(bool(self.host_out)) << 15) | (int(hin.free() and hin._load is None) << 14) | ((self.host_out[0][0] if self.host_out else 0) & 3)
        if address == _S.HOST_MAP["host_out"][0]:
            return self.host_out.popleft()[1] if self.host_out else 0
        i = self._map_block("owners", address)
        if i is not None: return 7 if self.owner[8 + i] is None else self.owner[8 + i]
        if _S.HOST_MAP["sram"][0] <= address < sum(_S.HOST_MAP["sram"]):
            return self.sram.mem[address - _S.HOST_MAP["sram"][0]]
        return 0

    def host_write(self, address, value):
        """Write one word through the D-046 register map; return whether accepted."""
        address &= 0xFFFF; value &= 0xFFFF
        if address == _S.HOST_MAP["run"][0]:
            self.run([i for i in range(len(self.lanes)) if value >> i & 1]); self.halt([i for i in range(len(self.lanes)) if not value >> i & 1]); return True
        if address == _S.HOST_MAP["step"][0]:
            stepping = [lane for i, lane in enumerate(self.lanes)
                        if value >> i & 1 and not lane.running]
            if stepping: self.live = True
            for lane in stepping: lane.stepping = True
            if stepping: self.step()
            return True
        if address == _S.HOST_MAP["irq_en"][0]: self.irq_en = value; return True
        i = self._map_block("slots", address)
        if i is not None:
            lane_id, slot_id, word_id = (i >> 8) & 3, (i >> 4) & 15, i & 3
            if i & 0xC or lane_id >= len(self.lanes) or self.lanes[lane_id].running: return False
            lane = self.lanes[lane_id]
            if slot_id == 12:
                lane.write_k(word_id, value)
            elif slot_id < lane.nslots:
                from .isa import encode_slot
                packed = encode_slot(lane.slots[slot_id])
                packed = (packed & ~(0xFFFF << (16 * word_id))) | (value << (16 * word_id))
                packed &= (1 << _S.SLOT_BITS) - 1
                lane.load_slot(slot_id, packed)
            else:
                return False
            return True
        i = self._map_block("pin_cfg", address)
        if i is not None:
            if any(l.running for l in self.lanes): return False
            unit, word = divmod(i, _S.PIN_CFG_STRIDE)
            words = self.pin_regs[unit]
            words[word] = value
            self.pin_written.add(unit)
            cfg = pinregs.decode(words, unit)
            self.pins[unit].configure(now=self.cycle, validate=False, **dataclasses.asdict(cfg))
            return True
        i = self._map_block("unit_flags", address)
        if i is not None:
            if value & 1: self.pins[i].flags["OVERRUN"] = 0
            if value & 2: self.pins[i].flags["LATE"] = 0
            return True
        i = self._map_block("ports", address)
        if i is not None:
            name = self.port_names[i]; port = self.fabric.ports[name]
            srcs = _S.LEGAL_SOURCES[name]; sel = (value >> 2) & 15
            port.host_sel = sel
            new_source = srcs[sel] if sel < len(srcs) else None
            port._take = False
            if port.src is not None: port.src.subs.remove(port)
            port.en = value & 1; port.blocking = int(not (value >> 1 & 1)); port.accept = (value >> 6) & 15
            port.src = self.fabric.producers.get(new_source) if new_source else None
            if port.src is not None:
                port.src.subs.append(port)
                port.last_seq = port.src.seq
            return True
        i = self._map_block("dropped", address)
        if i is not None: self.fabric.ports[self.port_names[i]].dropped = 0; return True
        i = self._map_block("lanes", address)
        if i is not None:
            lane, word = divmod(i, _S.HOST_LANE_STRIDE); l = self.lanes[lane]
            if l.running: return False
            if word < 4: l.write_reg(word, value); return True
            if word == 4: l.write_state(value); return True
            return False
        i = self._map_block("owners", address)
        if i is not None:
            pad = 8 + i
            if pad in HOST_PADS: return False
            owner = value & 7
            self.owner[pad] = owner if owner < len(self.pins) else None
            return True
        i = self._map_block("host_in", address)
        if i is not None:
            p = self.fabric.producers["HOST_IN"]
            if not p.free() or p._load is not None: return False
            p.load(i & 3, value); return True
        if _S.HOST_MAP["sram"][0] <= address < sum(_S.HOST_MAP["sram"]):
            self.sram.write(address - _S.HOST_MAP["sram"][0], value); return True
        return False

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
        if rot < len(self.lanes) and (self.lanes[rot].running or self.lanes[rot].stepping):
            self.lanes[rot].mem_access(self.sram)
        if self.live:
            for u in self.pins:
                sense = u.cfg.pin_a if u.cfg.pin_s is None else u.cfg.pin_s
                # §14 P42: an unattached pin A/S reads IDLE and pin B reads 0 (C: always selected)
                a = u.cfg.idle if sense is None else self.synced(sense)
                b = 0 if u.cfg.pin_b is None else self.synced(u.cfg.pin_b)
                u.compute_rx(now, a, b, self.synced(u.cfg.pin_c))
                u.compute_tx(now, b, a)
        hin = self.fabric.producers["HOST_IN"]
        if self.host_in and hin.free() and hin._load is None:
            hin.load(*self.host_in.popleft())
        hout = self.fabric.ports["HOST_OUT"]
        if hout.avail() and len(self.host_out) < self.host_fifo_depth:
            self.host_out.append(hout.head())
            hout.take()
        # clock edge
        self.fabric.commit()
        for lane in self.lanes:
            lane.commit()
        if self.live:
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
