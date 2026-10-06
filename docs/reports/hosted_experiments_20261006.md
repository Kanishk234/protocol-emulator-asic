# Hosted experiments — October 6, 2026

## Verified software result

[Compact experiments37512249763](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37512249763)
at f671c1b: **g1_demos job passes**. Four freshly compiled and hash-audited
G1 images are loaded through real SPI and tested on shell/fabric RTL:

| Case | Hosted test seconds | XML |
|---|---:|---|
| UART monitor |21.8674|monitor_rtl_results.xml|
| UART fault monitor |19.9550|fault_rtl_results.xml|
| Two-entry capture |24.7824|capture_rtl_results.xml|
| Prescaled capture |24.9997|prescaled_rtl_results.xml|

Downloaded17,476-byte artifact `g1-demos-37512249763` to ignored
`build/cloud_evidence_37512249763_g1/`. Independently parsed all four XMLs:
exactly one case each, no failures/errors/skips. Compile reports/logs retained
in that artifact. This proves fresh hosted compile/audit and loaded RTL behavior;
it is not native gates, SDF, physical timing or silicon evidence.

First attempt37511778394 passed monitor in22.72s, then omitted the intermediate
monitor module from fault synthesis. Fix c76de70 adds the documented dependency;
the four-case hosted pass verifies it (BUG31).

## Missing checkpoint is not a design result

Both attempts' route/native jobs fail at release-asset download, **before EDA**.
No new compact routing marker count, antenna result, native functionality or
timing result is produced. Public checkpoint publication was rejected by
automatic approval review because public egress/licensing scope was not
established; specific user approval was requested and is pending. The archive
and explicit122-file inventory are complete and hash-verified. It includes
generated RTL/netlists, macro GDS, OpenDB design geometry, the UART image,
native marker report and supporting design inputs. Text/filename scanning finds
no credential/key/token patterns; that is not a blanket licensing assertion.

Follow-up harness writes `blocked_before_eda` metadata and an explicit setup
error when the asset is absent. It continues to fail rather than present an
untested design as accepted. After publication, rerun failed jobs on the
corrected experiment; no laptop EDA is needed.

## Other CI

At a284f4c, lint37511778680, docs37511778312, idle-chip test37511778469 and
unit37511778471 pass. Fabric37511778167 and G1 gds37511778153 are still running
when this report is written. These do not validate the compact successor.
No phase checklist is closed. See
[compact acceptance plan](compact_acceptance_and_competitors.md).

## Additional failed-workflow review

Read recent failures across both branches after the user's status report.
On main (TRIPWIRE), critical-branch37380322860 fails in its custom OpenROAD
wrapper because awk is absent from its command path. Routed-GL37375683211
fails setup with KeyError:PL_OPTIMIZE_MIRRORING. Unit37375675116's RTL job has
a cancellation annotation, while its pytest and Verilator jobs pass. Read the
plain job logs and annotations; no main files or runs were modified. These are
not WARP compact closure results and WARP uses no TRIPWIRE custom wrapper.

At WARP4146abd, test37512885377, lint37512885326, docs37512885423 and
unit37512885345 all pass. Compact experiments37512885358 is in progress at
this review; no asset approval or new routing/native result yet. The original
G1 fabric and gds runs remain separately in progress. Historical red badges
remain historical; no checks were waived or hidden.
