# Antenna source-locality investigation

Reference: minimum-buffer screen41569397169, four final cumulative antenna failures. This investigation introduces no RTL or physical-flow changes.

| Failing sink | Driver after tracing upstream through physical buffer/delay chains |
|---|---|
| wire13568/A | mux _48371_, lane0/lane1 rpc[0] selected by host lk[0]; host debug readback (corrected attribution) |
| wire12579/A | and4 _31257_, including shared port_state[30] |
| _38673_/A | nand2 _31775_ after intermediate buffer chain |
| hold7969/A | and2 _37504_ |

Earlier source attribution incorrectly identified the RPC mux as SRAM selection. Final and synthesis netlists instead show lane0/lane1 RPC selected by u_chip.u_host.lk[0], matching trw_host lane debug selection. The earlier SRAM experiment below therefore does not target this failing mux. The candidate lane source does assign mem_addr = do_acc ? acc_addr : rpc. Earlier prototype direction: evaluate factoring this selection with the downstream SRAM arbitration so the selected-address logic can be implemented near its consumer. This must preserve arbitration, enabled-address values, routine/data access priority and cycle behavior. Exposing both address buses can increase routing; no area or timing benefit is assumed. A direct equivalent mux spelling is likely to map identically and is not a useful experiment by itself. More source-cone tracing is needed before rewriting the other three paths.

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

## Corrected host readback prototype — 2026-11-03

Final stage44 connectivity confirms _48371_ selects lane0/lane1 RPC bit0 using host lk[0] (with inserted physical buffers on some inputs). Synthesis stage06 has the same direct named inputs. trw_host selects the full180-bit lane debug bus before decoding its16-bit word; trw_chip packs RPC into bits83:75. This is host observation logic,not SRAM arbitration. Build/endpoint-source-attribution/fanin.json records hash-bound final fanin traces for all four sinks,limited to12cell levels; depth stops are explicitly incomplete.

Prepared an isolated source prototype that decodes a16-bit word independently for each lane and then selects that lane's word. No new state,cycles,ISA or protocol-specific primitive. Actual reference/trial source blocks pass combinational SAT equivalence for NL2andNL3 across arbitrary debug data and all7-bit read addresses,including the existing out-of-range read guard. Wrong RPC-slice mutant is rejected. This is block equivalence,not whole-chip sequential proof or gate-level replay.

Paired isolated-block local mapping with the same typical library/buf1 exclusion:372→323cells,4119.1794→3565.2204µm² (−13.45% for this block only); sequential area0both. This establishes a smaller local mapping,not physical locality,antenna immunity or positive setup margin. Main source remains unchanged. Source/patch/SAT logs/mapping outputs are under ignored build/host-readback-prototype. Full-design mapping is now measured below; preservation of the other three failed endpoint gates remains to be assessed before any full screen.

Full-design local mapping on the matched full2/4source:47919→47868cells;595129.5126→595240.947µm² (+111.4344µm²,about0.019%);sequential area118356.9408µm²unchanged. Tracing through inserted identity buffers finds one mux directly selecting lane0/lane1 RPC bit0 in reference and zero in trial. This removes the implicated mux topology in local mapping; no claim that native synthesis/placement reproduces it or fixes all antennas. Earlier isolated-block area savings do not translate to full-chip area savings.

Local replay preparation initially omitted programs/,so all22cases failed to load; corrected the scratch copy. The next attempt reached the optional sigrok UART decode and received empty decoder stdout; it was stopped. Restarted full22caseRTL protocol-model replay with TRIPWIRE_SKIP_SIGROK=1,retaining all model assertions. This excludes independent sigrok decode evidence. Replay result remains pending;do not count interrupted attempts as protocol passes.

## Independent channel availability factoring prototype

Buffer-collapsed final fanin places the wire12579 branch after _31257_,whose inputs include channel3 enable/accept state,selected producer tag/sequence and last_seq. The hold7969 driver cone selects between lane1 register bits7/23/39/55. The _38673_ input traces through seven physical buffers to the shared slot-selection cone _31775_. These are bounded mapped-cone observations,not proofs of complete RTL signal attribution.

Prepared an independent trw_chan_port source prototype: combine per-producer selected/valid/sequence-new/tag-accepted terms to compute availability,keeping the original token head and state updates. It adds no state or cycles. Actual availability-cone SAT equivalence passes N9andN13 under zero/onehot select_mask. The actual reset/update transition is separately proved to establish/preserve that invariant;wrong tag-slice mutant is rejected. No equivalence is claimed for arbitrary illegal multihot states.

Full local mapping compared separately with unchanged reference:47919→48114cells;595129.5126→599029.074µm² (+3899.5614µm²,about0.655%);sequential area unchanged. Proofs/source patch/mapping receipts:ignored build/channel-availability-prototype. This is a possible timing/locality tradeoff,not established improvement;no physical timing or antenna result. Keep this separate and on hold rather than launching another full screen without evidence of benefit. It is not combined with the host prototype and has no protocol replay claim.

Host replay update: the model-only Icarus attempt passed UART TX/RX then was interrupted to use faster Verilator for the long suite. Verilator replay is active;first three cases passed at the last check. No complete22case claim yet. Main unit workflow41714123695has passed Python and Verilator jobs;its Icarus chip/L3/rotation step remains active.

## Host prototype verification completed and screen prepared

Verilator full2/4RTL replay completes22/22cases,0failures,about411seconds;optional sigrok was skipped. Outside the sandbox,the saved finalUART trace independently decodes54a5at9600baud,matching its testcase. Empty decoder output inside the sandbox is reproduced by --version/libusb initialization;it is an environment limitation,not evidence of an RTL defect. No all-protocol independent-decoder or finalGLclaim.

Packaged host_word_select.patch/evidence.json and optional rtl_shared_minbuf2_host_words profile in our existing diagnostic workflow. D-144records scope/cost. Exact archived CI preparation passes all source/patch hashes;only trw_host.vdiffers from the matched prepared reference. Pinned TTmerge yields identical merged config;201focused tests and embedded shell syntax pass. Existing default and official gds.yaml remain unchanged. Ready for user publication under AGENTS Git rule;not launched. Fresh stock screening must still pass all timing/electrical/antenna/overflow gates before DRT.
