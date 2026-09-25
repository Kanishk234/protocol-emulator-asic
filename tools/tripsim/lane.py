"""One TRIPWIRE lane: reflex slots, the EVAL/EXEC pipeline and the routine sequencer.

Written from ARCHITECTURE.md and ISA.md only (never from src/). Cycle semantics are in
ARCHITECTURE.md §14 (draft); the numbered rules below refer to it.

Per clock the chip calls, in order: compute_exec(), compute_eval(), mem_access() (on
this lane's SRAM rotation slot), then commit(). compute_* only read registered state
and record effects; commit() applies them at the clock edge.
"""

from . import isa
from .isa import A_I0, A_I1, A_TIME, A_ZERO, DST_NONE, DST_O0, DST_O1


class Lane:
    def __init__(self, idx, nslots, in_ports, out_prods, fire_period=1):
        self.idx = idx
        self.nslots = nslots
        self.inp = in_ports            # [I0, I1] ConsumerPorts
        self.out = out_prods           # [O0, O1] Producers
        self.fire_period = fire_period  # 1 = EVAL every clock; 2 = R1 fallback
        self.slots = [isa.Slot()] * nslots
        self.regs = [0] * 4
        self.k = [0] * 4
        self.state = 0
        self.flags = [0, 0, 0]          # f0..f2
        self.pend = [0, 0, 0]
        self.rb = 0                     # f3
        self.rz = 0
        self.reserved = [0, 0]
        self.exec_latch = None          # issued at EVAL, executed next clock
        # routine sequencer
        self.rpc = 0
        self.rir = None                 # ("instr", word) or ("ldwb", rd, value)
        self.rstep_inflight = False
        self.mem_req = None             # ("ENTRY", idx) | ("LD", addr, rd) | ("ST", addr, value)
        self.running = False
        self.stepping = False           # §14 H2: one EVAL (+ its EXEC) on a halted lane
        # effects recorded this clock
        self._x = {}
        self._e = {}
        self._m = {}
        # statistics
        self.stats = {"clocks": 0, "fired": [0] * nslots, "routine_steps": 0,
                      "routine_wait": 0, "idle": 0, "preempted": 0}

    # ------------------------------------------------------------------ host
    def load_slot(self, n, word):
        if self.running:
            raise RuntimeError("slots are writable only while the lane is halted")
        self.slots[n] = isa.decode_slot(word)

    def _halted(self, what):
        if self.running:
            raise RuntimeError(f"{what} are writable only while the lane is halted")

    def write_reg(self, i, value):
        """Host write of r0-r3 (§9 lane register block, D-035 E2)."""
        self._halted("registers")
        self.regs[i] = value & isa.MASK16

    def write_state(self, value):
        self._halted("STATE")
        self.state = value & 15

    def write_k(self, i, value):
        """Host write of K0-K3 (slot index 12, words 0-3; §14 H1)."""
        self._halted("constants")
        self.k[i] = value & isa.MASK16

    def flag_value(self, i):
        return self.rb if i == 3 else self.flags[i]

    def _flags4(self):
        return self.flags[0] | (self.flags[1] << 1) | (self.flags[2] << 2) | (self.rb << 3)

    def _pend4(self):
        return self.pend[0] | (self.pend[1] << 1) | (self.pend[2] << 2)

    # ---------------------------------------------------------------- EXEC
    def compute_exec(self, now):
        """Execute the action issued at the previous EVAL (§14 rule L3)."""
        x = self._x = {}
        latch = self.exec_latch
        if latch is None:
            return
        kind = latch["kind"]
        if kind == "reflex":
            self._exec_reflex(latch, x)
        elif kind == "routine":
            self._exec_routine(latch, x)
        elif kind == "ldwb":
            x["reg"] = (latch["rd"], latch["value"])
            x["routine_done"] = True

    def _exec_reflex(self, latch, x):
        s = latch["slot"]
        if s.ASRC < 4:
            a = self.regs[s.ASRC]
        elif s.ASRC in (A_I0, A_I1):
            a = latch["head"][1]
        elif s.ASRC == A_ZERO:
            a = 0
        else:
            a = latch["time"]
        if s.BSEL == isa.B_REG:
            b = self.regs[s.IMM & 3]
        elif s.BSEL == isa.B_K:
            b = self.k[s.IMM & 3]
        else:
            b = s.IMM
        if isa.OPS[s.OP] == "CALL":
            return                      # RB and the entry fetch were set at EVAL (rule L6)
        res = isa.alu(s.OP, a, b, s.IMM, self.regs, self.k)
        if s.DST < 4:
            x["reg"] = (s.DST, res.d)
        elif s.DST in (DST_O0, DST_O1):
            if res.ctrl:
                tag = isa.TAG_CTRL
            elif s.KT and s.ASRC in (A_I0, A_I1):
                tag = latch["head"][0]
            else:
                tag = s.OT
            o = s.DST - DST_O0
            self.out[o].load(tag, res.d)
            x["unreserve"] = o
        if s.DFE and s.DF < 3:
            x["flag"] = (s.DF, res.r)

    def _exec_routine(self, latch, x):
        w = isa.decode_routine(latch["word"])
        k = w["kind"]
        x["routine_done"] = True
        regs = self.regs
        if k == "ALU":
            name = isa.OPS[w["op"]]
            if name == "CALL":
                return                          # reserved in routines: no operation
            b = w["b"] if w["bs"] else regs[w["b"] & 3]
            f = w["b"] if w["bs"] else regs[w["b"] & 3] & 0xFF
            res = isa.alu(w["op"], regs[w["ra"]], b, f, regs, self.k)
            x["reg"] = (w["rd"], res.d)
            x["rz"] = res.r
        elif k == "LDI":
            x["reg"] = (w["rd"], w["imm"])
        elif k == "LDIH":
            x["reg"] = (w["rd"], ((w["imm"] & 0x3F) << 10) | (regs[w["rd"]] & 0x3FF))
        elif k == "BR":
            take = {isa.BR_ALWAYS: True, isa.BR_RZ: self.rz == 1,
                    isa.BR_NRZ: self.rz == 0}.get(w["cond"], False)
            if take:
                x["rpc"] = (self.rpc + w["off"]) & 0x3FF
        elif k == "DJNZ":
            v = (regs[w["rd"]] - 1) & isa.MASK16
            x["reg"] = (w["rd"], v)
            if v != 0:
                x["rpc"] = (self.rpc + w["off"]) & 0x3FF
        elif k in ("LD", "ST"):
            addr = (regs[w["ra"]] + w["off"]) & 0xFFFF
            if k == "LD":
                x["mem"] = ("LD", addr, w["rd"])
            else:
                x["mem"] = ("ST", addr, regs[w["rd"]])
        elif k == "OUT":
            self.out[w["port"]].load(w["tag"], regs[w["ra"]])
            x["unreserve"] = w["port"]
        else:  # SYS
            name, arg = isa.SYS_NAMES.get(w["fn"]), w["arg"]
            if name == "RET":
                x["ret"] = True
            elif name == "SETST":
                x["state"] = arg & 15
            elif name in ("SETF", "CLRF") and (arg & 3) < 3:
                x["flag"] = (arg & 3, int(name == "SETF"))
            elif name == "TSTF":
                x["rz"] = self.flag_value(arg & 3)
            elif name == "CPYF" and (arg & 3) < 3:
                x["flag"] = (arg & 3, self.rz)
            elif name == "GETT":
                x["reg"] = (arg & 3, latch["time"])
            elif name == "GETK":
                x["reg"] = (arg & 3, self.k[(arg >> 2) & 3])

    # ---------------------------------------------------------------- EVAL
    def _ready(self, s):
        """ISA.md §4.2: explicit condition plus the implicit readiness checks."""
        if not s.V:
            return False
        if s.SE and self.state != s.SV:
            return False
        if (self._flags4() ^ s.FV) & s.FM:
            return False
        if self._pend4() & s.FM:
            return False
        if s.ASRC in (A_I0, A_I1):
            port = self.inp[s.ASRC - A_I0]
            if not port.avail():
                return False
            tag, data = port.head()
            if s.TE and tag != s.TAG:
                return False
            if s.HE and ((data & 1) if s.HS else ((data >> 15) & 1)) != s.HV:
                return False
        call = isa.OPS[s.OP] == "CALL"
        if s.DST in (DST_O0, DST_O1) and not call and not self._out_free(s.DST - DST_O0):
            return False                # rule L10: CALL ignores DST
        if call and self.rb:
            return False
        return True

    def _out_free(self, o):
        return not self.reserved[o] and self.out[o].free()

    def _routine_candidate(self):
        """Is the waiting routine step issuable this clock? (OUT needs a free output.)"""
        if self.rir is None:
            return False
        if self.rir[0] == "instr":
            w = isa.decode_routine(self.rir[1])
            if w["kind"] == "OUT" and not self._out_free(w["port"]):
                return False
        return True

    def compute_eval(self, now):
        e = self._e = {}
        if not (self.running or self.stepping):
            return
        self.stats["clocks"] += 1
        if now % self.fire_period and not self.stepping:
            return
        ready = [n for n, s in enumerate(self.slots) if self._ready(s)]
        urgent = [n for n in ready if self.slots[n].U]
        routine_ok = self._routine_candidate()
        # ISA.md §4.3 / §5.3: urgent slots > waiting routine step > other slots
        if routine_ok and urgent:
            pick = urgent[0]
            self.stats["preempted"] += 1
        elif routine_ok:
            pick = "routine"
        elif ready:
            pick = ready[0]
        else:
            pick = None
            if self.rir is not None:
                self.stats["routine_wait"] += 1
            else:
                self.stats["idle"] += 1
        if pick is None:
            return
        if pick == "routine":
            self.stats["routine_steps"] += 1
            if self.rir[0] == "ldwb":
                e["latch"] = {"kind": "ldwb", "rd": self.rir[1], "value": self.rir[2]}
            else:
                word = self.rir[1]
                e["latch"] = {"kind": "routine", "word": word, "time": now & 0xFFFF}
                w = isa.decode_routine(word)
                if w["kind"] == "OUT":
                    e["reserve"] = w["port"]
            e["consume_rir"] = True
            return
        s = self.slots[pick]
        self.stats["fired"][pick] += 1
        latch = {"kind": "reflex", "slot": s, "time": now & 0xFFFF, "n": pick}
        if s.ASRC in (A_I0, A_I1):
            port = self.inp[s.ASRC - A_I0]
            latch["head"] = port.head()
            if s.DQ:
                port.take()
        e["latch"] = latch
        if s.NSE:
            e["state"] = s.NS
        if s.DST in (DST_O0, DST_O1) and isa.OPS[s.OP] != "CALL":
            e["reserve"] = s.DST - DST_O0
        if s.DFE and s.DF < 3 and isa.OPS[s.OP] != "CALL":
            e["pend"] = s.DF
        if isa.OPS[s.OP] == "CALL":
            e["call"] = s.IMM & 31

    # ------------------------------------------------------------- SRAM slot
    def mem_access(self, sram):
        """Called on this lane's rotation slot (cycle mod 4 == lane index)."""
        m = self._m = {}
        req = self.mem_req
        if req is not None:                     # rule R3: data access before fetch
            if req[0] == "ENTRY":
                m["rpc"] = sram.read(req[1])
            elif req[0] == "LD":
                m["rir"] = ("ldwb", req[2], sram.read(req[1]))
            else:
                sram.write(req[1], req[2])
            m["mem_done"] = True
        elif self.rb and self.rir is None and not self.rstep_inflight:
            # rule R2: fetch only when no step is waiting or executing, so RPC is final
            m["rir"] = ("instr", sram.read(self.rpc))
            m["rpc"] = (self.rpc + 1) & 0x3FF

    # -------------------------------------------------------------- commit
    def commit(self):
        x, e, m = self._x, self._e, self._m
        # EXEC effects (routine STATE writes first, so a reflex NS in the same clock wins)
        if "reg" in x:
            rd, v = x["reg"]
            self.regs[rd] = v & isa.MASK16
        if "flag" in x:
            f, v = x["flag"]
            self.flags[f] = v
            self.pend[f] = 0
        if "rz" in x:
            self.rz = x["rz"]
        if "state" in x:
            self.state = x["state"]
        if "unreserve" in x:
            self.reserved[x["unreserve"]] = 0
        if "rpc" in x:
            self.rpc = x["rpc"]
        if "mem" in x:
            self.mem_req = x["mem"]
        if x.get("ret"):
            self.rb = 0
        if x.get("routine_done"):
            self.rstep_inflight = False
        # SRAM slot
        if m.get("mem_done"):
            self.mem_req = None
        if "rpc" in m:
            self.rpc = m["rpc"] & 0x3FF
        if "rir" in m:
            self.rir = m["rir"]
        # EVAL effects
        self.exec_latch = e.get("latch")
        if "state" in e:
            self.state = e["state"]
        if "reserve" in e:
            self.reserved[e["reserve"]] = 1
        if "pend" in e:
            self.pend[e["pend"]] = 1
        if "call" in e:
            self.rb = 1
            self.mem_req = ("ENTRY", e["call"])
        if e.get("consume_rir"):
            self.rir = None
            self.rstep_inflight = True
        self.stepping = False
        self._x, self._e, self._m = {}, {}, {}
