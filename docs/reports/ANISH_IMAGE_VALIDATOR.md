# Reference image validator — 2026-09-27

The isolated validator and reload guard pass 41 transaction cases in RTL
and on a mapped CMOS5L netlist. This closes the trusted-validity assumption
at the **word-transaction boundary only**. The existing full-fabric
`reference_guarded_top.v` still takes trusted `ImageValid`; connecting the
new boundary to that loader is covered by the subsequent separate
[validated-fabric wrapper experiment](ANISH_VALIDATED_FABRIC.md). The
trusted wrapper remains available as the historical baseline.

## Experimental contract (ANISH-D4)

`wp_image_validator.v` accepts synchronous words after begin. Its companion
`wp_validated_reload.v` combines it with the existing guard, suppresses
writes outside LOAD, after completion/error, and on a begin/abort/reset edge.
A word with invalid structure can already have reached the fabric before
the registered error appears. The safety mechanism is continued hold and
output parking, not rollback of partially written configuration.

Begin latches the expected checksum and checks sideband metadata:
architecture ID `0x46524231` ("FRB1"), format version 1, and length 12,024
bytes. These values describe this pinned reference experiment only. They
are not FABulous-standard metadata or the eventual chip's host ABI.
Later metadata changes cannot change the pending transaction.

The image is exactly 3,006 big-endian bus words: five canonical header
words, 200 records in column/frame order (one select plus fourteen row
words each), then desync `0x00100000`. Frame selects must match exactly;
duplicate, swapped, multi-frame or reserved-bit addresses are not allowed.
Partial/selective frame loading and reordered experiments are outside
this validator's contract.

CRC covers all 12,024 bytes, including header, addresses and desync, in
binary-file order. It uses reflected polynomial `0xEDB88320`, initial
state `0xFFFFFFFF`, and final XOR `0xFFFFFFFF`, following the
[W3C CRC algorithm](https://www.w3.org/TR/PNG-CRCAppendix.html).
The independent test oracle is Python's zlib implementation, checked
against `123456789 -> 0xCBF43926`. The 16,384-byte simulation memory padding
is excluded: sending even one padding word before commit invalidates the
transaction. A CRC provides corruption detection, not authentication or
proof that a user circuit is safe or implements the intended protocol.

Completion and checksum agreement produce validity. A commit with a write
on the same edge cannot release the guard, including the final word or an
extra word. A later idle commit is required. Early commits are ignored;
the transaction can continue. Detected errors are sticky until begin,
abort or reset. Truncation leaves the transaction incomplete, held and
parked; it has no timeout/error escalation yet. Abort/reset clear validity.
A fresh begin can replace a failed or interrupted transaction.

The interface is synchronous: each asserted `word_valid` sampling edge is
one word. It is not a CDC interface or an arbitrary-width host pulse.
Out-of-LOAD words cannot write the fabric. Integration must prove the
validator and FABulous loader consume exactly the same words, coordinate
loader reset, and drain final frame writes before release.

## Validation and retained evidence

Successful run: `build/warp-validator.x2xpdWlS/`.

- RTL and mapped-netlist tests each pass **41 cases / 116,831 steps**.
- Real counter/LFSR images, three seeded random canonical payloads and
  subsequent valid transactions are accepted.
- Seven truncation lengths remain parked/incomplete. Single-word and full
  memory padding are rejected.
- Nine malformed header/select/desync cases and duplicate/swapped frames
  use recomputed CRCs, proving checksum agreement alone cannot pass them.
- Four payload bit flips retain the original checksum and are rejected.
- Wrong architecture, version, declared lengths and checksum are rejected.
- Early/final-word/extra-word commit races, idle gaps, metadata latching,
  abort/reset midstream, begin/write coincidence, RUN-state writes and
  abort/reset priority are checked through public ports.
- Verilog-2005 parse and Yosys pre/post-mapping `check -assert` pass.
  GL uses pinned CMOS5L cell/UDP models and Tiny Tapeout Icarus 13.
  Model warnings about unsupported edge-sensitive `ifnone` paths remain
  in the compile log; these are functional checks without SDF.

The random payloads test parser/CRC behavior only: they are not loaded into
a live fabric and are not claimed to be useful or safe user designs.
A structurally valid wrong-function image can pass this validator; retain
the independent functional wrong-image control in full-fabric tests.

Mapped validator **plus guard**: **904 cells, 14,123.7054 µm²**, using the
same pinned IHP PDK `2bbec755dc67ca3db0261c3d6163e15735d66710`,
typical 1.20 V / 25 C Liberty, and Yosys 0.66+179.
This is a sum of cell areas, excluding fabric, configuration storage,
host interface, output muxes, clock/control buffers, placement and wires.
No timing or full-chip fit conclusion follows. The word-parallel CRC is
a throughput-first baseline; a byte/bit-serial version may be a better
tradeoff for a slow host and requires measurement.

First attempt `warp-validator.RbPFjlt3` passed RTL but stopped at mapped
Yosys checking because library port directions were not loaded. The runner
now reads Liberty blackbox definitions before mapping/checking; the rerun
reports zero problems. No design fix was needed (ANISH-FAB-5).

Reproduce with the project venv and supported tool PATH:

```bash
bash scripts/fabric_validator.sh build/fabric-reference-warp-reference.OBUfXfus
```

The runner reuses images, PDK and simulator caches; it snapshots its sources,
runner, hashes, test manifest, tool versions, mapped netlist and logs under
ignored `build/`. It does not rebuild or simulate the large fabric.

## Next gates

The subsequent [byte CRC comparison](ANISH_BYTE_CRC.md) adds an optional
ready/busy-aware implementation and reruns the same rejection suite in
RTL and GL. The historical measurements above remain snapshot-specific.

1. The separate validated full-fabric mode now covers both reload directions,
   selected interrupted/corrupt loads and word agreement in RTL (linked
   above). Extend its handshake/reset corner cases and mapped/physical
   validation; this does not establish arbitrary-image safety.
2. Measure a serial CRC at the required host throughput before allocating
   production shell area.
3. Broader isolation coverage, physical control skew/timing, generator
   integration, organizer/CI requirements and phase-0 exit remain open.
