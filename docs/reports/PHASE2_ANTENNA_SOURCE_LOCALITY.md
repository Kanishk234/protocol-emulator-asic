# Antenna source-locality investigation

Reference: minimum-buffer screen41569397169, four final cumulative antenna failures. This investigation introduces no RTL or physical-flow changes.

| Failing sink | Driver after tracing upstream through physical buffer/delay chains |
|---|---|
| wire13568/A | mux _48371_, one input lane1 rpc[0]; corresponds to lane SRAM address selection between acc_addr and rpc |
| wire12579/A | and4 _31257_, including shared port_state[30] |
| _38673_/A | nand2 _31775_ after intermediate buffer chain |
| hold7969/A | and2 _37504_ |

The candidate lane source assigns mem_addr = do_acc ? acc_addr : rpc. First prototype direction: evaluate factoring this selection with the downstream SRAM arbitration so the selected-address logic can be implemented near its consumer. This must preserve arbitration, enabled-address values, routine/data access priority and cycle behavior. Exposing both address buses can increase routing; no area or timing benefit is assumed. A direct equivalent mux spelling is likely to map identically and is not a useful experiment by itself. More source-cone tracing is needed before rewriting the other three paths.

The pinned standard-cell model includes sg13cmos5l_antennanp, a single input with no functional output. An RTL diode instantiation alone does not establish physical protection: synthesis preservation, net splitting, diode-to-gate connectivity and native resizer treatment must be checked. Direct technology primitives require a portable simulation/mapping wrapper and explicit physical connectivity evidence before considering adoption. No custom official-flow stage or hardcoded mapped-instance ECO is proposed.

Working raw driver trace is build/minbuf2-residual-driver-trace.json (ignored). Physical netlist evidence is bound in minimum_buffer_result.json. No new passing claim, screen dispatch or phase completion.


## Parallel address-selection prototype result

Actual edited SRAM selection block extracted from reference/trial passes combinational SAT equivalence for NL2andNL3,including enable,write-enable,address and write-data outputs. Source outside that block is byte-identical. A wrong unused-slot fallback mutant was previously rejected. This is a named combinational-block proof,not whole-chip sequential formal.

Paired local mapping with identical sorted sources/library and buf_1 ABC exclusion: reference595129.5126µm²/47919cells;trial592800.201µm²/47544cells;sequential area118356.9408µm²unchanged. These are local mapping figures,not native synthesis or routed area. SRAM address cone grows55→58cells and its unweighted depth remains5on all9address bits. The total area reduction (~0.39%) does not establish a locality/antenna improvement. Do not publish this prototype as a selected physical candidate or spend a full screen on it without stronger evidence. Complete source/patch/proof/mapping receipts remain ignored under build/address-selection-prototype.


## Protected relay synthesis probe

An ignored scratch design instantiates two kept buf_2 cells with a kept antenna diode on their shared internal node. Local Yosys synthesis/flatten/clean retains all three cells and the named node; JSON connectivity checks pass and a deliberately wrong-node diode connection is rejected. Nominal library cell area23.5872µm²,excluding physical overhead. No registers are added,but two buffer propagation delays are real.

This only proves local synthesis preservation. Native resizer stress,post-route diode effectiveness and timing/electrical effects remain untested. The relay protects its own buffer input; it is not a demonstrated solution for the original NAND/delay-cell endpoints. Stock RSZ_DONT_TOUCH_RX can select named nets/instances during repair,but those protections are later unset and do not establish fixed placement or antenna-repair behavior. Do not adopt or launch a full-design candidate from this probe. Raw design/netlist/receipt:build/protected-endpoint-probe. Next feasibility check requires the pinned native physical engine,which is not installed locally.


## Actual routing topology and targeted capacity experiment

The reference's stage41pre-antenna and stage44final guide comparison shows net12579envelope129.6→381.6µm;_10511_144→158.4;_19518_561.6→424.8;net11878_374.4unchanged. These are global-guide bounding spans,not detailed wire lengths or antenna areas. Stage41is before antenna repair,not the independently audited stage43post-antenna source. All four final sink cell connections remain unchanged across the audited late interval. The mixed changes argue against a single distance threshold.

D-142tests Metal3reserve8%with other signal layers retaining global16%on identical minbuf2RTL. Pinned router source verifies nonzero layer overrides;actual per-layer resource checks are mandatory.194focused checks and exact clean preparation/pinned TT merge pass. This targets detour opportunity,but reducing modeled reserve can hurt DRT and all final gates remain required. No more toy distance-only sweep;no hardware or official-flow change.
