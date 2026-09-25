# Verification

Status: stub. Version 1 is written in phase 1.

## Layers
| ID | Layer | What it checks | Tools | CI workflow |
|---|---|---|---|---|
| V1 | Primitive | Hard blocks, loader, FIFOs: corner cases | cocotb, formal | unit, formal |
| V2 | Configuration mapping | Bits land in the right place | cocotb | fabric |
| V3 | Source vs. fabric | User RTL and configured fabric match | cocotb, bounded equivalence | fabric |
| V4 | Protocol peer | Independent models and sigrok decoders | cocotb, sigrok-cli | test |
| V5 | Reconfiguration | Stop, bad loads, reload, restart | cocotb | test |
| V6 | Gate level | Real bitstreams on the netlist | gl_test | gds |
| V7 | Fault injection | Checks catch deliberate faults | scripts | nightly |

## Formal properties (name, property, bound)
## Coverage goals
