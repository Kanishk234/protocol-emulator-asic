# Selector candidate closure pipeline

The selected storage follow-up has passing functional evidence in regression
43946078700, but it has **not** reached extracted timing closure or signoff.
The original candidate's -1.982448040 ns failure remains a real failed result.

The cloud sequence now continues through qualified dependencies:

1. [Physical screen 43951998125](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/43951998125)
   runs the stock 8x4 flow at 20 ns, requiring setup/hold, electrical, antenna
   and global-overflow gates. It is still in physical execution when checked.
2. [Route/extraction 43956306270](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/43956306270)
   waits for that exact screen/1258879/attempt1 to pass. It verifies the complete
   archive digest and independently reconstructed hardware, preserves saved
   physical paths, repeats timing/antenna checks, then performs detailed routing,
   topology/DRC/connectivity/antenna checks and extracted three-corner STA.
   Fast hold must remain at least50ps; no timing/electrical violations allowed.
3. [Final replay43957253552](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/43957253552)
   at5c73590 waits for that exact route/29c0e63/attempt1
   to pass. It independently authenticates both screen and route archives,
   reconciles all six frozen source views, requires passing extracted gates,
   selects the actual extracted-state netlist and compares its logical cells
   and connections with the routed export. Only then does it replay all22
   protocol cases using pinned native cells/Icarus13 and real sigrok.

Each source identity is fixed; a failed predecessor stops the next job.
There is no local watcher, repair loop, automatic clock reduction, source
promotion or acceptance relaxation. Fresh reconstruction of all170 replay
inputs matches the passing functional artifact. Before/after source hashing
and strict actual XML inspection protect the final replay.

The final replay has no SDF annotation and uses pinned SRAM behavioral models.
It establishes scoped native-cell functionality if it passes, not pin timing,
full GDS/LVS/DRC/precheck qualification or hardware testing. Production source
integration and unchanged official-flow reproduction remain separate phase2
requirements. Phase2 remains open.
