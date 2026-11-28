# R1 timing work, November 27

The current qualified program passes native UART/SPI/reset and full management
reload, but fails the original 20 ns / 0.25 ns macro condition: setup
−34.141884 ns, hold −1.226009 ns (46045747168 at32796d4a). This is measured
failure, not closure. G1 remains selected. See the independently checked
`r1_known_input_repair_native_timing_46045747168.json`.

| Priority | Action | Required evidence / decision |
|---|---|---|
| Now | Remove dynamic routes from proved-unused physical SPI capture inputs | D187: exactly twelve selector bits, actual-frame truth/mode/carry proofs, defined replacement sources, full reencoding. Local native/reset passes; hosted management reload and original RC must follow. Do not infer physical pin numbers from logical packed LUT ports. |
| Next | Investigate UART input hold using alternative routes carrying the identical signal | The active input really comes from UART input X7Y1/A; its immediate alternate is a different pin, so that alternate is rejected. Search upstream mux choices for the same terminal, exclude primitive/clock/control changes, preserve every affected consumer, and measure real minimum/maximum delay after fresh loading. |
| If no safe route exists | Insert an explicitly compiled combinational buffer on the affected data input | Prove binary identity, account for LC/routing capacity, require a fresh compile/native/reload/RC run. Use real fabric resources; no RTL delay statements, altered cell models or artificial input delays. This may help hold while costing setup/routing reserve. |
| After spare-input measurement | Target SPI read-capture enable decode and placement | Keep the qualified program as control. Investigate local mapping of just the affected enable group, predecoded/one-hot state or cycle-equivalent control retiming. Prove source behavior before compilation when RTL changes, and qualify each new image separately. |
| If paths remain dominated by distance | Constrain a small measured critical placement group | Check shared enable/reset legality and congestion, preserve total physical area and clock target. Avoid blind global seed sweeps; never copy an old image's selector repairs to the new mapping. |
| If software mapping cannot meet intrinsic delays | Evaluate a separate physical LC/clock implementation | Preserve the working chip and ABI. One hardware change per hardening; redo native equivalence, routing, strict geometry/LVS, extraction, functional loading and timing. Existing macro power/whole-chip integration gaps remain required work. |
| Before any closure claim | Integrate the actual shell, input launch paths, output loads and clock distribution | Keep the original conditional macro comparison intact. Measure full-chip behavior rather than changing macro input delays or adding path exceptions to hide negative slack. Complete power/PVT/loading checks and submission gates. |

The global MIN_CTRL16 experiment (46047728814 at4009f0bb) did not complete
routing within 600 seconds: 60 arcs remained despite a 104/128 LC pre-routing
inventory. The original MIN_CTRL4 compiler control reproduced exactly. This
fixed experiment is rejected; a smaller cell count did not make it routable.
See `r1_local_enable_compile_46047728814.json`.

November 28 update: D18746061527240 at41638e9e passes native/reset/full
management reload and qualified RC measurement, but both worst slacks are
unchanged. The spare-input changes do not fix the current worst paths. Two
separate D188compiles now target selective eight-FF capture-control mapping
and a four-LUT UART input delay chain at the existing capture site. Their
binary netlist checks pass; fit and physical delay remain unmeasured.

Each experiment keeps the original 20 ns period, 0.25 ns uncertainty, real
configuration loading, active annotation and both loop policies. Source-only
proofs, compiler frequency estimates and successful workflow execution cannot
substitute for nonnegative qualified setup and hold. Keep the original path
policies and real state observations, leave held-out protocols sealed, and keep
G1 selected until the complete replacement gates pass.


November 28 measured update: UART-buffer46175928642 passes native,
restart and full management reload; qualified setup/hold are -23.209684/
-1.567830ns. Targeted UART sync[0] hold is +2.093250ns, but other boundary
inputs fail. The whole mapping differs; this is not an isolated delay estimate.
Selective capture controls46175430185 fail native ready definedness and do
not reach timing. D191four freshly proved spare selectors on the UART-buffer
image pass local native/restart; hosted reload/extracted timing remain required.
G1 stays selected. No constraints or phase gates have been relaxed.


D19146177440003 confirms the four-selector setup improvement in CI:
-6.517231ns setup/-1.567830ns hold, native/reset/full reload PASS,
14497active pins annotated and no loops/policy differences. No closure.
D192requests one response-lane placement near the measured host read-data
endpoint. Preserve D191and reject inherited selector repairs after re-routing.


Remaining hold work, measured from46177440003: an independent read-only
query finds105failing endpoint minima:23boundary launches and82self-feedback
Q-to-D paths. A full-clock-expanded primitive query reproduces -0.047458ns
(arrival2.369029ns, required2.416486ns) with the original0.25nsuncertainty.
See `r1_hold_inventory_46177440003.json`. These are worst paths per endpoint,
not all paths. Input buffering alone cannot address the internal primitive
feedback. Replacing user placement alone cannot change that native leaf path.

The next physical investigation should reproduce one primitive feedback path
at its actual loaded configuration, then test native hold repair on a separate
derived leaf: preserve every original cell/configuration latch and only insert
real noninverting delay on a proved feedback branch. Check logical equivalence,
added cell area and native routing/DRC/antenna/LVS before re-extraction. Cover
all affected physical contexts and rerun actual native/reload/configured timing;
keep original macro/control and both loop policies. This physical repair is
planned, not implemented or accepted. Boundary holds also need the real shell
launch/clock context plus any measured physical buffering; retain the original
zero-I/O boundary result separately and do not waive failures or lower uncertainty.
