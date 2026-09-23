"""Channel fabric: producer registers and consumer ports (ARCHITECTURE.md §4).

Cycle semantics (ARCHITECTURE.md §14, draft):
- All decisions in a clock use registered state from the start of that clock.
- A consumer port sees a token when  en && src.valid && last_seq != src.seq.
- A producer is *free* (may load this clock) when !valid or every enabled
  blocking subscriber has last_seq == seq. Takes made in the same clock do not
  count (no combinational path from consumers back to producers).
- At the clock edge, takes are applied first (last_seq := seq), then loads
  (seq toggles, valid := 1). A tap that had the old token available and did not
  take it when the producer loads a new one counts a drop (8-bit, saturating),
  and the drop counts as a take (last_seq := old seq), so the new token is visible.
- valid stays set until the next load; a taken token is simply not available
  again because last_seq == seq.
"""


class Producer:
    def __init__(self, name):
        self.name = name
        self.valid = 0
        self.seq = 0
        self.tag = 0
        self.data = 0
        self.subs = []          # ConsumerPorts selecting this producer
        self._load = None       # (tag, data) requested this clock
        self.loads = 0

    def free(self) -> bool:
        if not self.valid:
            return True
        return all(p.last_seq == self.seq for p in self.subs if p.en and p.blocking)

    def load(self, tag, data):
        if self._load is not None:
            raise RuntimeError(f"{self.name}: two loads in one clock")
        if not self.free():
            raise RuntimeError(f"{self.name}: load while not free")
        self._load = (tag & 3, data & 0xFFFF)


class ConsumerPort:
    def __init__(self, name):
        self.name = name
        self.src = None
        self.en = 0
        self.blocking = 1
        self.last_seq = 0
        self.dropped = 0
        self.accept = 0xF       # tag mask (D-015): other tags are dropped at the port
        self.filtered = 0
        self._take = False
        self.takes = 0

    def _pending(self) -> bool:
        s = self.src
        return bool(self.en and s is not None and s.valid and self.last_seq != s.seq)

    def avail(self) -> bool:
        return self._pending() and bool((self.accept >> self.src.tag) & 1)

    def filtered_pending(self) -> bool:
        """A token this port does not accept is waiting: the fabric drops it (§14 F7)."""
        return self._pending() and not (self.accept >> self.src.tag) & 1

    def head(self):
        """(tag, data) of the available token."""
        return self.src.tag, self.src.data

    def take(self):
        if not self.avail():
            raise RuntimeError(f"{self.name}: take with no token available")
        self._take = True


class Fabric:
    def __init__(self, legal_sources=None):
        self.producers = {}
        self.ports = {}
        self.legal = legal_sources      # {port: set(producer names)} or None = any

    def producer(self, name):
        p = self.producers[name] = Producer(name)
        return p

    def port(self, name):
        c = self.ports[name] = ConsumerPort(name)
        return c

    def connect(self, port_name, producer_name, mode="blocking", accept=0xF):
        """Host configuration (only while the affected blocks are halted).

        accept: tag mask; tokens with other tags are dropped at this port (D-015)."""
        port, prod = self.ports[port_name], self.producers[producer_name]
        port.accept = accept
        if self.legal is not None and producer_name not in self.legal.get(port_name, ()):
            raise ValueError(f"{producer_name} is not a legal source for {port_name}")
        if port.src is not None:
            port.src.subs.remove(port)
        port.src = prod
        port.en = 1
        port.blocking = int(mode == "blocking")
        port.last_seq = prod.seq          # enabling never exposes a stale token
        prod.subs.append(port)

    def commit(self):
        for p in self.producers.values():
            new = p._load
            for c in p.subs:
                if c._take:
                    c.last_seq = p.seq
                    c.takes += 1
                elif c.filtered_pending():
                    c.last_seq = p.seq          # §14 F7: not for this port; dropped, never blocks
                    c.filtered += 1
                elif new is not None and not c.blocking and c.avail():
                    # A drop counts as a take (BUGS #2): with a 1-bit seq, a tap that
                    # missed two tokens would otherwise alias and lose the new one.
                    c.dropped = min(c.dropped + 1, 255)
                    c.last_seq = p.seq
                c._take = False
            if new is not None:
                p.tag, p.data = new
                p.seq ^= 1
                p.valid = 1
                p.loads += 1
                p._load = None
        for c in self.ports.values():
            if c._take:               # port with no producer registered above
                raise RuntimeError(f"{c.name}: take on unconnected port")
