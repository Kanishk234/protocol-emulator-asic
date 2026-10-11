# Routed delay C2: conditional internal timing clears examined paths

[38164099529](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38164099529), commit7a63257, completes six actual extracted STA cases. All examined register-to-register setup and hold paths have positive slack with zero native VIOLATED path labels. This is conditional UART-programmed C2 internal timing, not full-chip timing acceptance.

The exact routed candidate38114298036 previously reached seven zero native physical gates and exact external interfaces. Its real SPI-loaded functional validation38163199372 passes normal/USER_RESET UART stress/STOP, all9164 configuration latches known and matching the image. This timing run authenticates those actual results, the new mapped graph, all six candidate physical views and its own nominal SPEF. It does not reuse the old macro parasitics. Original20ns clock, .25ns uncertainty, .15ns transition and early.95/late1.05 derating remain.

| Actual tile position | Library corner | Worst setup slack, ns | Worst hold slack, ns | Paths per min/max report |
|---|---|---:|---:|---:|
| X2Y1 | fast | 17.891823 | 0.062141 | 28 |
| X2Y1 | slow | 15.207784 | 0.483093 | 28 |
| X2Y1 | typical | 16.899254 | 0.220627 | 28 |
| X2Y3 | fast | 17.961403 | 0.042992 | 26 |
| X2Y3 | slow | 15.370059 | 0.432373 | 26 |
| X2Y3 | typical | 17.000338 | 0.188731 | 26 |

Original no-delay precise extracted38112173902 has worst fast hold−0.032927ns atX2Y1 and−0.037383ns atX2Y3. The delayed candidate therefore clears this observed blocker under matched margins; routed geometry changes as well as the additional cells, so attribute the result to the complete candidate rather than asserting a pure cell-delay causal estimate. Every program pays the eight-cell delay/placement/routing cost. The tile footprint remains the original; no full-chip equal-area superiority claim follows.

Independent review verifies all42 report hashes, min/max report path counts and native slack/status labels, plus eight actual finite rise/fall propagated-clock arrivals per case (48 reported clock endpoints total). Result SHA bf46fc2769e697f21ebbd53ae6c91cde1868c020a17a7110a7e077530006c0fa. No loop warnings are observed in these stdout logs; this does not prove universal loop freedom.

Important coverage remains open. Every case reports152 inputs without I/O delays and529 unclocked configuration latch pins. X2Y1 has677 unconstrained endpoints;X2Y3 has679. Four unannotated drivers remain: N2END[1], S2END[5], W2END[3], TIE_ZERO_zero_/L_LO, with0 partially unannotated drivers. Their relation to active timing coverage needs auditing. Configuration Q is assumed stationary during this diagnostic; it is not an unbounded proof of every loader/RUN sequence. User state stays dynamic, no false paths or loop cuts are added, and the actual boundary clock is N_GBUF_END[3]. Upstream fabric/shell/intertile clock skew, I/O, loading mode, other tile types and other programs are excluded. Full-chip fanout-free placement still fails native routing (latest146→136 comparison38163542037).

The first candidate attempt38163818509 never reached STA because Docker rejected relative working directories (BUG71). The successful retry corrects paths only; no timing margins, source, libraries, cases or parasitics were changed.

Next: retain this as a qualified diagnostic candidate; audit active annotation/coverage and loading-mode constraints, harden/verify the other tile types with matched views, and solve the remaining full-chip routing before combining/promoting hardware.

### Read-only annotation follow-up

`audit_c2_unannotated_loads.py` authenticates actual loaded graph313a7c727a0105813daef7b12efa1b52b921663905089cc902a2450d882fb5a4 and mapped sourcea986a0864ab51f09f6157422ba7dff935585b6456e6accc7b64ac8228725e882 from38163199372/38114298036. All six actual annotation reports from38164099529 contain exactly the same four unannotated drivers and zero partial drivers. Graph connectivity independently shows N2END[1], S2END[5], W2END[3] and TIE_ZERO_zero_/L_LO have **zero cell input/inout loads and zero output/inout boundary aliases**. Therefore these four reported omissions do not feed a path in this exact tile graph. This removes one annotation concern for the examined tile; it does not cover intertile parasitics, other tile types, configuration loading, unconstrained endpoints or full-chip timing. No report or acceptance gate was altered.

Reproduce using the retained actual artifacts:
```sh
source .venv/bin/activate
python test_internal/audit_c2_unannotated_loads.py build/cloud_c2_delay_loaded_38163199372/hardened_final_c2/matched_native_cone.json build/cloud_c2_delay_sta_38164099529
```
