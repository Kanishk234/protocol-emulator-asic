"""tripc v0: compile a .trw program into a TRIPWIRE image plus a static report.

Language (line oriented; '#' starts a comment; blocks are indented under a 'name:' header):

    program NAME
    param NAME = EXPR            # overridable at compile time
    const NAME = EXPR
    pin U<n>: key=value ...      # pin-unit configuration (values: pads like uio0, names, EXPR)
    own <pad> U<n>               # output ownership
    connect <port> <- <producer> [tap] [accept=TAG|TAG]
    lane L<n>:
        K<i> = EXPR              # per-lane constants
        r<i> = EXPR              # initial register values
        states NAME NAME ...     # STATE names, numbered from 0
        slot [urgent]: [when COND, ...] do ACTION [then STATE]
    routine NAME:
        <instruction> | label:
    table NAME:                  # constant words in SRAM (lookup tables); NAME = its address
        EXPR, EXPR, ...          # placed after the entry table, before the routines

Slot conditions:  STATE | fN == V | rb == V | I0 is TAG | head15 == V | head0 == V
Slot action:      OP DST <- A [, B] [, mask X val Y] [, f=EXPR] [, deq] [, keep] [, tag TAG] [-> fN]
                  CALL routine [<- A] [, deq]
    B is rN, KN or an immediate EXPR; DST is r0-r3, O0, O1 or none; A is r0-r3, I0, I1, zero, time.
    ('#' always starts a comment.)

Routine instructions: ldi/ldih/load16 rX, EXPR | OP rd, ra, (rN | EXPR) | br LABEL [if rz|nrz]
    | djnz rX, LABEL | ld rd, ra, OFF | st rd, ra, OFF | out Ox, rX, TAG | ret | nop
    | setst STATE | setf N | clrf N | tstf N | cpyf N | gett rX | getk rX, KN
"""

import dataclasses
import pathlib
import re

import tripwire_spec as S
from tripsim import asm, isa
from tripsim.pinunit import PinConfig

from .expr import ExprError, evaluate

LANE_SLOTS = 12
SRAM_WORDS = 512
_PIN_KEYS = {f.name for f in dataclasses.fields(PinConfig)}
_PAD_KEYS = {"pin_a", "pin_b", "pin_c", "pin_s", "pin_n"}


class TrwError(Exception):
    def __init__(self, msg, line=None, file=None):
        loc = f"{file or '<trw>'}:{line}: " if line else ""
        super().__init__(loc + msg)


@dataclasses.dataclass
class Lane:
    name: str
    k: list = dataclasses.field(default_factory=lambda: [0] * 4)
    regs: list = dataclasses.field(default_factory=lambda: [0] * 4)
    states: dict = dataclasses.field(default_factory=dict)
    slots: list = dataclasses.field(default_factory=list)      # (lineno, urgent, text)
    words: list = dataclasses.field(default_factory=list)
    info: list = dataclasses.field(default_factory=list)


class Compiler:
    def __init__(self, text, params=None, file=None):
        self.file = file
        self.lines = text.splitlines()
        self.overrides = dict(params or {})
        self.names = {}
        self.params = []
        self.program = None
        self.pins, self.owns, self.connects = {}, [], []
        self.lanes, self.routines = {}, {}        # routines: name -> (lineno, [lines])
        self.tables = []                           # SRAM words of all tables, from address 32
        self.warnings = []

    # -------------------------------------------------------------- helpers
    def err(self, msg, n):
        raise TrwError(msg, n, self.file)

    def ev(self, text, n):
        try:
            return evaluate(text, self.names)
        except ExprError as e:
            self.err(str(e), n)

    def int16(self, text, n, what):
        v = self.ev(text, n)
        if not isinstance(v, int) or not 0 <= v <= 0xFFFF:
            self.err(f"{what} = {v!r} is not a 16-bit unsigned integer", n)
        return v

    # -------------------------------------------------------------- parsing
    def parse(self):
        i = 0
        while i < len(self.lines):
            n, line = i + 1, self._strip(self.lines[i])
            i += 1
            if not line:
                continue
            if self.lines[i - 1][:1].isspace():
                self.err("unexpected indented line", n)
            head = line.split()[0]
            if head == "program":
                self.program = line.split()[1]
            elif head in ("param", "const"):
                m = re.fullmatch(r"(param|const)\s+(\w+)\s*=\s*(.+)", line)
                if not m:
                    self.err(f"expected '{head} NAME = EXPR'", n)
                kind, name, expr = m.groups()
                self.names[name] = self.overrides.pop(name) if kind == "param" and name in self.overrides \
                    else self.ev(expr, n)
                if kind == "param":
                    self.params.append(name)
            elif head == "pin":
                self._pin(line, n)
            elif head == "own":
                parts = line.split()
                if len(parts) != 3:
                    self.err("expected 'own <pad> U<n>'", n)
                self.owns.append((self._pad(parts[1], n), self._unit(parts[2], n)))
            elif head == "connect":
                self._connect(line, n)
            elif head in ("lane", "routine", "table"):
                m = re.fullmatch(rf"{head}\s+(\w+)\s*:", line)
                if not m:
                    self.err(f"expected '{head} NAME:'", n)
                body = []
                while i < len(self.lines) and (not self.lines[i].strip() or self.lines[i][:1].isspace()):
                    if self._strip(self.lines[i]):
                        body.append((i + 1, self._strip(self.lines[i])))
                    i += 1
                if head == "lane":
                    self._lane(m.group(1), body, n)
                elif head == "table":
                    if m.group(1) in self.names:
                        self.err(f"{m.group(1)} is already defined", n)
                    self.names[m.group(1)] = 32 + len(self.tables)
                    for ln, text in body:
                        for item in filter(None, (x.strip() for x in text.split(","))):
                            self.tables.append(self.int16(item, ln, "table word"))
                else:
                    if m.group(1) in self.routines:
                        self.err(f"routine {m.group(1)} defined twice", n)
                    self.routines[m.group(1)] = (n, body)
            else:
                self.err(f"unknown statement {head!r}", n)
        if self.overrides:
            raise TrwError(f"unknown params: {sorted(self.overrides)}", file=self.file)
        if self.program is None:
            raise TrwError("missing 'program NAME'", file=self.file)

    @staticmethod
    def _strip(line):
        return line.split("#", 1)[0].strip()

    def _pad(self, text, n):
        if text not in S.PADS:
            self.err(f"unknown pad {text!r} (ui0-7, uo0-7, uio0-7)", n)
        pad = S.PADS[text]
        if pad in S.HOST_PADS:
            self.err(f"pad {text} belongs to the host port", n)
        return pad

    def _unit(self, text, n):
        m = re.fullmatch(r"U(\d)", text)
        if not m:
            self.err(f"expected a pin unit U<n>, got {text!r}", n)
        return int(m.group(1))

    def _pin(self, line, n):
        m = re.fullmatch(r"pin\s+(U\d)\s*:\s*(.*)", line)
        if not m:
            self.err("expected 'pin U<n>: key=value ...'", n)
        unit, cfg = self._unit(m.group(1), n), {}
        for item in m.group(2).split():
            if "=" not in item:
                self.err(f"expected key=value, got {item!r}", n)
            key, val = item.split("=", 1)
            if key not in _PIN_KEYS:
                self.err(f"unknown pin setting {key!r}", n)
            if key in _PAD_KEYS:
                cfg[key] = self._pad(val, n)
            elif val in ("true", "false"):
                cfg[key] = val == "true"
            elif re.fullmatch(r"[A-Za-z_]\w*", val) and val not in self.names:
                cfg[key] = val                        # a mode name: rise, msb, linked_rx, ...
            else:
                cfg[key] = self.ev(val, n)
        if unit in self.pins:
            self.err(f"U{unit} configured twice", n)
        self.pins[unit] = cfg

    def _connect(self, line, n):
        m = re.fullmatch(r"connect\s+(\S+)\s*<-\s*(\S+)((?:\s+\S+)*)", line)
        if not m:
            self.err("expected 'connect <port> <- <producer> [tap] [accept=TAG|TAG]'", n)
        port, prod, rest = m.groups()
        mode, accept = "blocking", 0xF
        for opt in rest.split():
            if opt == "tap":
                mode = "tap"
            elif opt.startswith("accept="):
                accept = 0
                for tag in opt[7:].split("|"):
                    if tag not in S.TAGS:
                        self.err(f"unknown tag {tag!r}", n)
                    accept |= 1 << S.TAGS[tag]
            else:
                self.err(f"unknown connect option {opt!r}", n)
        self.connects.append((port, prod, mode, accept))

    def _lane(self, name, body, n):
        m = re.fullmatch(r"L(\d)", name)
        if not m:
            self.err("lanes are named L0, L1, L2", n)
        lane = self.lanes.setdefault(int(m.group(1)), Lane(name))
        for ln, line in body:
            if m2 := re.fullmatch(r"K([0-3])\s*=\s*(.+)", line):
                lane.k[int(m2.group(1))] = self.int16(m2.group(2), ln, f"K{m2.group(1)}")
            elif m2 := re.fullmatch(r"r([0-3])\s*=\s*(.+)", line):
                lane.regs[int(m2.group(1))] = self.int16(m2.group(2), ln, f"r{m2.group(1)}")
            elif line.startswith("states "):
                for s in line.split()[1:]:
                    if s in lane.states:
                        self.err(f"state {s} declared twice", ln)
                    lane.states[s] = len(lane.states)
                if len(lane.states) > 16:
                    self.err("at most 16 states (STATE is 4 bits)", ln)
            elif m2 := re.fullmatch(r"slot(\s+urgent)?\s*:\s*(.*)", line):
                lane.slots.append((ln, bool(m2.group(1)), m2.group(2)))
            else:
                self.err(f"unknown lane statement {line!r}", ln)

    # -------------------------------------------------------------- slots
    def _slot(self, lane, n, urgent, text):
        m = re.fullmatch(r"(?:when\s+(.*?)\s+)?do\s+(.*?)(?:\s+then\s+(\w+))?", text)
        if not m:
            self.err("expected 'slot: [when CONDS] do ACTION [then STATE]'", n)
        conds, action, then = m.groups()
        kw = {"urgent": urgent}
        cond_input = None
        for c in [c.strip() for c in (conds or "").split(",") if c.strip()]:
            if c in lane.states:
                if "state" in kw:
                    self.err("a slot tests one STATE", n)
                kw["state"] = lane.states[c]
            elif m2 := re.fullmatch(r"(f[0-2]|rb)\s*==\s*([01])", c):
                idx = 3 if m2.group(1) == "rb" else int(m2.group(1)[1])
                kw.setdefault("flags", {})[idx] = int(m2.group(2))
            elif m2 := re.fullmatch(r"(I[01])\s+is\s+(\w+)", c):
                if m2.group(2) not in S.TAGS:
                    self.err(f"unknown tag {m2.group(2)!r}", n)
                cond_input, kw["tag"] = m2.group(1), m2.group(2)
            elif m2 := re.fullmatch(r"head(15|0)\s*==\s*([01])", c):
                kw["head15" if m2.group(1) == "15" else "head0"] = int(m2.group(2))
            else:
                self.err(f"unknown condition {c!r} (is the state declared?)", n)
        self._action(action, kw, n)
        if cond_input and kw.get("a") != cond_input:
            self.err(f"condition tests {cond_input}, but the action reads A = {kw.get('a')} "
                     f"(tag and head tests apply to the A input, ISA.md §4.2)", n)
        if ("head15" in kw or "head0" in kw) and kw.get("a") not in ("I0", "I1"):
            self.err("head-bit tests need the action to read I0 or I1 as A", n)
        if then is not None:
            if then not in lane.states:
                self.err(f"unknown state {then!r}", n)
            kw["ns"] = lane.states[then]
        try:
            return asm.reflex(**kw), kw
        except (ValueError, KeyError) as e:
            self.err(f"bad slot: {e}", n)

    def _action(self, text, kw, n):
        flag = re.search(r"\s*->\s*f([0-2])\s*$", text)
        if flag:
            kw["flag"] = int(flag.group(1))
            text = text[:flag.start()]
        elif re.search(r"->\s*f3", text):
            self.err("f3 is RB, read-only", n)
        items = [t.strip() for t in text.split(",")]
        head = items[0].split()
        op = head[0]
        if op not in isa.OP:
            self.err(f"unknown operation {op!r}", n)
        kw["op"] = op
        if op == "CALL":
            if len(head) < 2 or head[1] not in self.routines:
                self.err(f"CALL needs a defined routine, got {head[1:]}", n)
            kw["f"] = list(self.routines).index(head[1])
            if len(head) == 4 and head[2] == "<-":
                kw["a"] = head[3]
            elif len(head) != 2:
                self.err("expected 'CALL routine [<- A]'", n)
        else:
            if len(head) != 4 or head[2] != "<-":
                self.err(f"expected '{op} DST <- A', got {items[0]!r}", n)
            kw["dst"], kw["a"] = head[1], head[3]
            if kw["dst"] not in S.DST or kw["a"] not in S.ASRC:
                self.err(f"bad destination {kw['dst']!r} or source {kw['a']!r}", n)
        for it in items[1:]:
            if it == "deq":
                kw["deq"] = True
            elif it == "keep":
                kw["keep_tag"] = True
            elif m := re.fullmatch(r"tag\s+(\w+)", it):
                if m.group(1) not in S.TAGS:
                    self.err(f"unknown tag {m.group(1)!r}", n)
                kw["ot"] = m.group(1)
            elif m := re.fullmatch(r"mask\s+(\w+)\s+val\s+(\w+)", it):
                kw["f"] = asm.cmpm_field(m.group(1), m.group(2))
            elif m := re.fullmatch(r"f\s*=\s*(.+)", it):
                kw["f"] = self.ev(m.group(1), n)
            elif re.fullmatch(r"[rK][0-3]", it):
                kw["b"] = it
            else:                                    # anything else is an immediate B
                kw["b"] = self.ev(it, n)

    # -------------------------------------------------------------- routines
    def _routine(self, name, n, body, lane_states):
        r = asm.Routine()
        for ln, line in body:
            if m := re.fullmatch(r"(\w+)\s*:", line):
                r.label(m.group(1))
                continue
            parts = line.replace(",", " ").split()
            op, a = parts[0], parts[1:]
            try:
                if op in ("ldi", "ldih", "load16"):
                    getattr(r, op)(a[0], self.ev(" ".join(a[1:]), ln))
                elif op.upper() in isa.OP and op.upper() != "CALL":
                    b = a[2] if re.fullmatch(r"r[0-3]", a[2]) else self.ev(" ".join(a[2:]), ln)
                    r.alu(op.upper(), a[0], a[1], b)
                elif op == "br":
                    r.br(a[0], a[2] if len(a) == 3 and a[1] == "if" else "always")
                elif op == "djnz":
                    r.djnz(a[0], a[1])
                elif op in ("ld", "st"):
                    getattr(r, op)(a[0], a[1], self.ev(" ".join(a[2:]), ln) if len(a) > 2 else 0)
                elif op == "out":
                    r.out(a[0], a[1], a[2] if len(a) > 2 else "DATA")
                elif op in ("ret", "nop"):
                    r.sys(op.upper())
                elif op == "setst":
                    if a[0] not in lane_states:
                        self.err(f"unknown state {a[0]!r}", ln)
                    r.setst(lane_states[a[0]])
                elif op in ("setf", "clrf", "tstf", "cpyf"):
                    getattr(r, op)(self.ev(a[0], ln))
                elif op == "gett":
                    r.gett(a[0])
                elif op == "getk":
                    r.getk(a[0], a[1])
                else:
                    self.err(f"unknown routine instruction {op!r}", ln)
            except (ValueError, IndexError, KeyError) as e:
                self.err(f"bad instruction {line!r}: {e}", ln)
        try:
            words = r.assemble()
        except KeyError as e:
            self.err(f"routine {name}: unknown label {e}", n)
        return words

    # -------------------------------------------------------------- analysis
    @staticmethod
    def routine_bound(words):
        """Worst-case steps over every path: forward branches and non-nested DJNZ loops with a
        constant count. Returns (steps, None) or (None, reason). LD counts 2 steps (its write-back
        is a step). The bound is the longest path through the routine's branch graph, so early
        RETs never hide a longer path (BUGS #17)."""
        dec = [isa.decode_routine(w) for w in words]
        n = len(dec)
        cost = [2 if w["kind"] == "LD" else 1 for w in dec]
        consts = {}                                 # register -> constant (straight-line order)
        for pc, w in enumerate(dec):
            k = w["kind"]
            if k == "LDI":
                consts[w["rd"]] = w["imm"]
            elif k in ("ALU", "LDIH", "LD", "SYS") and "rd" in w:
                consts.pop(w["rd"], None)
            if k == "BR" and w["off"] < 0:
                return None, f"backward branch at word {pc} (only DJNZ loops are bounded)"
            if k == "DJNZ":
                if w["off"] >= 0:
                    return None, f"DJNZ at word {pc} jumps forward"
                count = consts.get(w["rd"])
                if count is None:
                    return None, f"loop count of r{w['rd']} at word {pc} is not a known constant"
                start = pc + 1 + w["off"]
                if any(dec[j]["kind"] == "DJNZ" for j in range(start, pc)):
                    return None, f"nested loops at word {pc}"
                cost[pc] += sum(cost[j] for j in range(start, pc + 1)) * (max(count, 1) - 1)
        best = [None] * (n + 1)                     # longest path from pc to a RET; None = invalid
        for pc in range(n - 1, -1, -1):
            w = dec[pc]
            k = w["kind"]
            if k == "SYS" and isa.SYS_NAMES.get(w["fn"]) == "RET":
                best[pc] = cost[pc]
                continue
            if k == "BR":
                target = pc + 1 + w["off"]
                succ = [target] if w["cond"] == isa.BR_ALWAYS else [target, pc + 1]
            else:
                succ = [pc + 1]
            if any(t > n or best[t] is None for t in succ):
                best[pc] = None                     # some path falls off the end
                continue
            best[pc] = cost[pc] + max(best[t] for t in succ)
        if best[0] is None:
            return None, "a path falls off the end without RET"
        return best[0], None

    # -------------------------------------------------------------- build
    def build(self):
        self.parse()
        if len(self.routines) > 32:
            raise TrwError("at most 32 routines", file=self.file)
        all_states = {}
        for lane in self.lanes.values():
            all_states.update(lane.states)
        rwords, rinfo = [], []
        for name, (n, body) in self.routines.items():
            words = self._routine(name, n, body, all_states)
            steps, why = self.routine_bound(words)
            if steps is None:
                self.warnings.append(f"routine {name}: no static bound ({why})")
            rinfo.append((name, len(words), steps))
            rwords.append(words)
        sram = [0] * 32 + self.tables                # entry table (ISA.md §5.2), tables, routines
        for i, words in enumerate(rwords):
            sram[i] = len(sram)
            sram.extend(words)
        if len(sram) > SRAM_WORDS:
            raise TrwError(f"SRAM image is {len(sram)} words, more than {SRAM_WORDS}", file=self.file)
        for lane in self.lanes.values():
            if len(lane.slots) > LANE_SLOTS:
                n = lane.slots[LANE_SLOTS][0]
                self.err(f"lane {lane.name} uses {len(lane.slots)} slots, more than {LANE_SLOTS}", n)
            for n, urgent, text in lane.slots:
                word, kw = self._slot(lane, n, urgent, text)
                lane.words.append(word)
                lane.info.append((n, urgent, text))
        image = {
            "program": self.program, "params": {k: self.names[k] for k in self.params},
            "pins": {f"U{u}": cfg for u, cfg in sorted(self.pins.items())},
            "own": [[pad, u] for pad, u in self.owns],
            "connect": [list(c) for c in self.connects],
            "lanes": {f"L{i}": {"slots": [f"0x{w:014x}" for w in l.words], "k": l.k, "regs": l.regs,
                                "states": l.states} for i, l in sorted(self.lanes.items())},
            "sram": sram,
            "routines": {name: {"index": i, "words": nw, "max_steps": st}
                         for i, (name, nw, st) in enumerate(rinfo)},
        }
        return image, self.report(image, rinfo)

    def report(self, image, rinfo):
        L = [f"# tripc report: {self.program}", "",
             f"Spec {S.VERSION} ({S.STATUS}). Parameters: " +
             (", ".join(f"{k} = {v}" for k, v in image["params"].items()) or "none") + ".", "",
             "## Lanes", "", "| Lane | Slots | Urgent | States | K used |", "|---|---|---|---|---|"]
        for i, l in sorted(self.lanes.items()):
            L.append(f"| {l.name} | {len(l.words)} / {LANE_SLOTS} | {sum(u for _, u, _ in l.info)} | "
                     f"{len(l.states)} | {sum(1 for v in l.k if v)} |")
        if rinfo:
            L += ["", "## Routines", "",
                  "Steps exclude waits on a full output (`out`), which depend on the consumer.", "",
                  "| Routine | Words | Worst-case steps | Time if not pre-empted |", "|---|---|---|---|"]
            for name, nw, st in rinfo:
                t = f"≤ {4 * st + 8} clocks" if st is not None else "unbounded"
                L.append(f"| {name} | {nw} | {st if st is not None else '—'} | {t} |")
            L.append(f"\nSRAM: {len(image['sram'])} of {SRAM_WORDS} words (entry table 32"
                     + (f" + tables {len(self.tables)}" if self.tables else "") + " + routines).")
        L += ["", "## Pins", "", "| Unit | Settings |", "|---|---|"]
        L += [f"| {u} | " + ", ".join(f"{k}={v}" for k, v in cfg.items()) + " |" for u, cfg in image["pins"].items()]
        L += ["", "## Reaction", "",
              "An urgent slot reacts pin to pin in 7 clocks (ARCHITECTURE.md §5.5) when it is the "
              "lowest-index ready slot and its output is free. Lower-index slots that are ready at "
              "the same time fire first and delay it. Per-slot bounds need the phase 3 analysis "
              "(VERIFICATION.md L6); v0 lists the slots that can pre-empt each urgent slot."]
        for i, l in sorted(self.lanes.items()):
            urg = [k for k, (_, u, _) in enumerate(l.info) if u]
            for k in urg:
                before = [j for j in urg if j < k]
                if before:
                    L.append(f"- {l.name} slot {k}: can be pre-empted by urgent slots {before}")
        if self.warnings:
            L += ["", "## Warnings", ""] + [f"- {w}" for w in self.warnings]
        return "\n".join(L) + "\n"


def compile_text(text, params=None, file=None):
    return Compiler(text, params, file).build()


def compile_file(path, params=None):
    path = pathlib.Path(path)
    return compile_text(path.read_text(), params, file=str(path))
