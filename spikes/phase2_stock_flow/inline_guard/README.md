# Inline guarded mask term

A general stateless masked-word AND primitive preserves the lane's original wide selector loop and replaces only its last-row term. The physical guard covers the action-field mask inputs in small buffer/diode groups; the data inputs remain repairable. No new state,clock cycles,ISA behavior or protocol-specific unit. Buffers add propagation delay that must be measured physically.

## Why this version

Matched local controls show the earlier selector-wide reorganization increases full mapped area even with guards disabled:595129.5126→607474.728µm². An unchanged design with an unused guard module exactly reproduces the reference. Keeping the original selection loop instead gives:

| Local mapped full design | Cells | Area µm² |
|---|---:|---:|
| Reference | 47919 | 595129.5126 |
| Inline term,guard disabled | 47705 | 594473.9094 |
| Inline term,guard enabled | 48124 | 597273.0372 |

Enabled is about0.36%above reference;the matched inline protection cost is about2799.13µm². Sequential area118356.9408µm²is unchanged. These are local synthesis/mapping numbers,not native routed area or timing. Source changes can change global logic factoring,so the disabled control matters.

The patched source guards slot row11in both lanes,action fields20through51(the call uses generated OP/KT bounds),with12mask diodes and64NAND gate inputs. The unused selected HS field is not physically guarded. Source topology links the original failing branch with last-slot action data,but complete equivalence of the old mapped coefficient with a named source signal is not claimed. New placement can move or create failures;this doesnotclaim to fix the other three original antennas.

## Verification before physical use

The actual action-field block passes SAT equivalence for arbitrary masks/data using pinned PDK BUF2/NAND2 functions. A wrong physical mask input is rejected. Full2lane/4unit/U0fullRTL replay passes22/22existing protocol cases under Verilator,with optional sigrok decoder checks enabled outside the sandbox. Local final mapped audit finds all64gate inputs directly connected to their12mask diodes/drivers. No whole-chip sequential formal,final GL,extracted timing or officialGDSclaim.

The existing guarded-word-preservation workflow now offers a mask variant. It tests the exact NAND/guard primitive on a tiny seven-bit example,comparing identical RTL/config except native RSZ_DONT_TOUCH_RX. The original paired-A22OI default remains unchanged. Data gates and upstream drivers stay repairable. The new audit permits only equivalent NAND2strengths1/2,and requires all intended direct connections and every protected object in all four repair logs.227focused checks,both kinds' exact preparations/pinned TTmerges,shell syntax and local actual mapped probe audits pass. Native NAND preservation result follows below.

Source/function/replay hashes and controls:preflight.json. Hardware remains isolated in spikes/ and ignored build/;main source/config and official GDS jobs are unchanged. The extra native protection option requires a separate main-config policy review before adoption. Full strict timing/electrical/antenna/overflow gates must pass before DRT.

## Exact NAND preservation and full-screen preparation

41758305742passes both native jobs. Raw final connections/logs/metrics were independently matched:enabled retains7/7mask-gate connections;disabled loses4/7. Typical setup11.1257ns/hold0.436704ns,electrical0andfresh antennas0both. Only protectionRXdiffers in actual resolved config. Both cases being antenna-clean limits this to preservation evidence;it is not a full-layout diode-efficacy claim.

Prepare optional rtl_shared_minbuf2_inline_guard in the separate stock screen. Its hardware is the verified inline source patch plus one primitive file;info.yaml and both simulation source lists include that file. Physical settings are the minimum-buffer reference41569397169plus exact native mask protectionRX;20ns/SDC,clock clustering,early/late hold targets,wire repair,stage order and all final gates stay fixed. Actual archived preparation and pinned TTmerge pass;merged config differs only in protectionRXand the extra source file.229focused checks pass. A final audit additionally requires64guard gates/12mask nodes and all intended protected objects in all four repair logs. No detailed routing unless all final screening gates pass together. Main hardware/config/official jobs remain unchanged.
