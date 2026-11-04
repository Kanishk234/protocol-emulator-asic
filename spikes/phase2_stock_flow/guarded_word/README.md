# Guarded mask word selector: preservation probe

This is a general stateless masked-word OR reduction. It pairs rows in native A22OI gates, with small local buffer/diode groups on the shared mask inputs. It adds no registers, instruction semantics or protocol-specific hardware. Buffer and gate propagation delays still require timing measurement. Data inputs and final reduction gates are **not** claimed to be antenna-protected.

The isolated lane patch replaces only selection of action fields from the existing reflex slots. Main hardware is unchanged. This is not a selected full-design candidate: local full-design mapping rises from 595129.5126 to 613237.7916 µm² (about 3.04%) and 47919 to 49846 cells; sequential area is unchanged. Source mapping has 144 mask diodes protecting 396 gate instances; each mask node has at most seven input loads including its diode. A first version protecting every data input too cost about 5.15% area and was rejected locally. Physical repair can add more cost or fail timing/congestion.

## Logical evidence

The actual original and trial lane selector blocks pass SAT equivalence on retained action fields for arbitrary mask/data values, using the pinned PDK BUF2/A22OI function models. Passive no-output diode cells are omitted only from the SAT model. Small/odd shapes (1×1,7×3,7×2) also pass. A wrong mask-gate connection is rejected, as is an edit outside the selected source block. This is a combinational block proof, not whole-chip sequential formal or protocol replay. The unchanged source surrounding that block and generated definitions are hash-bound in preflight.json.

Reproduce against the matched prepared reference and installed pinned PDK:

```bash
source .venv/bin/activate
python scripts/ci/prove_guarded_word.py \
  --reference-src build/stock-minbuf2-ci-prep-20261103-final/src \
  --trial-lane build/guarded-word-prototype/trw_lane.v \
  --primitive spikes/phase2_stock_flow/guarded_word/trw_guarded_reduce.v \
  --pdk-cells ~/.cache/tripwire/pdk-2bbec755dc67ca3db0261c3d6163e15735d66710/ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/verilog/sg13cmos5l_stdcell.v \
  --output build/guarded-word-proof
```

The prepared reference/trial paths refer to this session's local reproduction. Another checkout must recover the reference source from screen41569397169 and apply lane_guard.patch in a separate copy first. Proof logs/build views are not committed.

## Native physical question

The manual guarded-word-preservation workflow uses a tiny two-row,seven-bit selector with a counter load. Both cases use identical RTL and stock tools/stage order. The only configuration difference is native RSZ_DONT_TOUCH_RX,disabled/enabled. A20µm wire-repair target stresses preservation. The protected regex selects only mask nodes/diodes; **upstream drivers and A22OI sink instances remain repairable**. Freezing sink instances would also freeze their data inputs and could recreate the earlier RSZ-3006 probe failure.

Protection is temporary during repair and does not fix placement. The final audit requires all seven gates to retain direct diode/driver-to-mask-pin connections on four named nodes,and requires every protected object to appear in all four native repair-stage logs. Removed gates,wrong functions,detached diodes,split mask nets or missing protection evidence reject. The disabled case records whether preservation survives without the constraint; survival in both cases would limit the inference. Typical timing/electrical and fresh antenna reports remain measurements,not full-design qualification. No DRT,extraction,GL,LVS or official GDS claim.

RSZ_DONT_TOUCH_RX is a stock option but is outside the current main-config whitelist. This isolated experiment does not approve main adoption or alter official jobs. Even successful preservation does not establish antenna efficacy on the full layout,closure of its other three original failures,or sufficient area/timing reserve. The completed real-endpoint diode intervention41714141900supplies separate actual-checkpoint mechanism evidence,not proof that this new layout reproduces it.

210focused checks,actual local mapped-probe connectivity,both exact ephemeral CI preparations,pinned TT merges and embedded shell syntax pass. Native physical result is pending.
