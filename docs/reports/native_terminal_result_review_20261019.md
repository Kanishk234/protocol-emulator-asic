# Independent actual terminal qualification review — October 19

Actual hosted run
[39367564921](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39367564921),
attempt1, exact source `8782e284e94706486f20f25248c7067eecdf0d70`.
`build/terminal112_identity.json` records completed SUCCESS on efpga at that
revision. Retained artifact root:
`build/terminal112_result/route_force_repair`. Result SHA256:
`8ac9ecbb64903a9296cd7cb6fd36633417933d9723e041537ea79091a1f73674`.
No EDA, source edits, commits or dispatch were performed by this review.

## Confirmed observations

Independently reran `native_terminals.audit_files` for all six initial/final
exports, compared each complete result object to its retained audit and found
exact equality. Independently reparsed/recomputed all six raw-resource ledger
audits and matched their retained objects; every raw H/V edge still reconciles
with weighted STEP multiplicity. Independently reran native_checkpoint.audit on
the six resource files and matched the retained checkpoint result, including
unchanged raw capacities/reductions/real capacities and four required unchanged
snapshots. Read the fourth patch bytes from the exact source Git object and
matched SHA256
`5ec2f809d784e5d81e59a1470bef566423f7a35cb1aea573564b35734396393b`.

Controls remain default calibrated121, legacy calibrated132 and membership
candidate139. Raw both-direction overflow remains121/134/139, including the
already diagnosed two nonpreferred legacy units. Collection success does not
change the native routing failures or promote either repair. Root separately
executes the complete portable three-mode control/witness/source audit; this
review independently recomputes the actual raw/terminal/checkpoint joins.

The terminal inventory is 3,693 database nets, 3,691 GlobalRouter nets,
3,659 native nets, 10,888 physical GlobalRouter pins, 10,856 membership rows and
10,678 tree nodes. Native empty-slot count is zero. All three initial terminal
files and the default final are byte-identical, SHA256
`90be2ecef64627ed67b1c4df920f86f673cac1bcdae4fef4db9587a3e79a18d3`.
Legacy final terminal SHA256:
`1da116af3d2f9e3239ae19ddd11988053d0500a072022114c2937962b5dc58bd`;
membership final:
`4a9b88a57958c2225155e9c3553becb26e496f1e1c6230c110fb8005a620f138`.

## Global gate remains false; reasons are explicit

Every snapshot correctly retains terminal `model_gate=FAIL` and
`terminal_join_verified=false` with exactly these diagnostics:

- 285 unsupported native tree-access observations. In the independently
  inspected initial snapshot, all285 are GlobalRouter-local with empty trees:
  278 have one native pin and seven have two native pins.
- 32 GlobalRouter nets with physical pins but no native FrNet. In the initial
  snapshot all32 are local one-pin nets.
- Two database nets outside the GlobalRouter map: VPWR and VGND, both special
  supply nets, each with3,606 ITerms and one BTerm in the initial snapshot.

These are measured classifications, not a waiver or proof that arbitrary
unexported access is irrelevant. No whole-design terminal/model gate is upgraded
by this review. The parser does not hide them to manufacture a global pass.

## Selected southern nets: scoped join supported

Neither `cell_pad\[31\]` nor `cell_val\[30\]` has **any** unsupported entry by
native slot or database ID in any of the six audited snapshots. Their observed
physical/native joins, root selection, node mappings and coarse access checks
succeed. Their native pin vectors are unchanged across all six snapshots:

| Net | Native slot / DB ID | Native pins (x,y,zero-based layer) | Driver index | Terminal mapping |
| --- | --- | --- | --- | --- |
| cell_pad[31] | 98 / 163 | (11,29,0), (10,24,0), (57,2,1) | 1 | 0→0, 1→1, 2→2 |
| cell_val[30] | 122 / 195 | (12,30,0), (55,2,1) | 1 | 0→0, 1→1 |

The former has three physical pins/three native terminals/four tree nodes; the
latter has two physical pins/two native terminals/two nodes. Every selected
physical pin has exactly one matching native MEMBER with the expected slot and
pin index. Both trees have `TREE_ACCESS_SUPPORTED=1` in every snapshot. No clock
classification, clamp, occurrence mapping or alias sentinel exception was waived.

At initial121, cell_pad's terminal alias layer ranges are0–3,0–3,1–1;
cell_val's are0–2,1–1. Each terminal's VIA_RANGE agrees with its native pin layer.
Cell_pad also has a Steiner node at(10,24) aliasing terminal1; its own bottom4/top−1
sentinel is correctly retained rather than treated as physical access. The
coincident terminal alias is valid. These are **coarse native node/access
observations**, not enclosure/spacing/obstruction or physical via-template proof.

The selected pair can therefore be investigated under its observed coarse
terminal contract without claiming a global terminal-model pass. An actual
corridor model still needs authenticated selected-net releases, fixed exterior
connectivity/boundary conditions, allowed arcs and multiplicity treatment, plus
native downstream validation. The initial121 raw ledger retains its separate
cfg_word[23] duplicate traversal and cannot be silently converted to Boolean
union consumption. Native-input authentication, physical/timing acceptance and
whole-chip solver-model readiness remain false.
