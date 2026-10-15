# Autonomous development integration, October 15

Integrated source: `77edd2dfdc12184a9b69c98cfa5041e9137ac016`. The active coordinator and three specialists built and exercised the development loop. G1 remains the fallback; compact native routing remains133 overflow. No hardware/spec changes or phase exit boxes.

## Actual hosted evidence

| Check | Run / attempt | Independently inspected outcome |
|---|---|---|
| Supervisor and observer |38777137622 /1 |63 hosted tests pass; read-only campaign discovery and artifact upload pass. |
| active-cancel |[38777137304 /1](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38777137304) |verified: test_active_window_cancel_loaded; actual artifact/image/XML checks pass. |
| c-host |[38777137259 /1](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38777137259) |verified: test_portable_c_host_loaded; actual artifact/image/XML checks pass. |
| compiler-seeds |[38777137439 /1](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38777137439) |verified: 9 compiler builds; actual artifact/image/XML checks pass. |
| uart-phase |[38777137234 /1](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38777137234) |verified: uart_phase_and_read_delay; actual artifact/image/XML checks pass. |

All four campaign results were downloaded, hashed and checked independently after workflow completion. Stronger phase-row and exact-fixture validation also accepts the actual phase artifact. Tests retain D-023 loaded-RTL scope; neither this supervisor nor a green workflow establishes physical/timing acceptance or board operation.

## Artifact provenance

* active-cancel: artifact ID `11994306858`, GitHub archive digest `sha256:03cafe5b28a925d8dd7d0263126a11863956ce5be3b80f63a78b6359f12a9598`.
  Compiled image SHA256 `8c8fc69166214361260d759073529c1e58fc0ebf59daa36734a59c3006606fc5`.
* c-host: artifact ID `11994481624`, GitHub archive digest `sha256:2e0993e2d3df4641f247bae6cde6201d69b905f5870306f6b00791302a49cbe3`.
  Compiled image SHA256 `14b61127da67dbb37d68e746f5720675a809b03ce315c4a6090bbcf1bcf1d8ed`.
* compiler-seeds: artifact ID `11993154782`, GitHub archive digest `sha256:40f0095aad86858d86b5311f0c497a9555bf3fce5798d229087ca383c5177865`.
* uart-phase: artifact ID `11994242038`, GitHub archive digest `sha256:045229c37347bd5d16e2e3148bcc4479cf4e12d0f2da1f6c26cb86b46461c7b7`.

GitHub archive digests are API-reported identities; the supervisor computes per-file SHA256 fingerprints after download. Local state, XML, logs and images remain under ignored `build/autonomy/`; raw evidence is not committed. Source workflow artifacts expire October18; reproduce with the pinned workflows and record new run identities rather than pretending they are historical artifacts.

## Failure found and corrected

Unit38777137520 correctly fails after strict XML validation encounters the inapplicable runtime-divisor test in fixed-divisor variants. BUG89 corrects discovery rather than relaxing evidence checks. The corrected UART matrix requires seven fixed/eight runtime cases. Hosted corrected result is recorded in WORKLOG after the follow-up push.

**Actual correction:** unit38778082137 succeeds on
`6370e1f5ae71a2d768fbe6cb87a062b2c1d21134`; all protocol matrix steps run with
strict XML checks. Test38778081786/lint38778081814/docs38778082198 and
autonomy38778081816 also succeed on this revision. See
[UART discovery evidence](unit_xml_discovery_20261015.md) for the actual census.

**Real supervisor dispatch:** a separate bounded campaign was launched with
`--tasks c-host --launch --max-launches 1`. Its persisted state reports exactly
one launch, then independently verifies run38778194236 attempt1 on6370e1f.
The workflow's requested-SHA guard passes before provisioning. Actual C image
SHA256 remains `14b61127da67dbb37d68e746f5720675a809b03ce315c4a6090bbcf1bcf1d8ed`.
Artifact ID11993564422 has GitHub API archive digest
`sha256:1c79f001bcdc8ff7a65c46167de5fe89964e28dc0d4c9359d16e8b2d70e162a0`;
downloaded XML/report/image and per-file fingerprints pass. This validates
real dispatch, persistent discovery and artifact acceptance, not only mocks.
Both bounded local campaigns finish naturally after their checks are verified.

The same checker now covers fabric loaded/cosim and local default protocol runs. The shell-only idle suite intentionally skips real-fabric cases and remains a distinct check. Broader tools locally reported785PASS/9SKIP before follow-up tests; the skipped cloud-only HDL and unavailable Tcl checks were never counted as passes.

## Continue the engineering loop

The routing specialist authenticated grid-to-segment indexing, accounted for blockage encoding and tested per-net own-allocation release. Each target still faces a saturated cut; arbitrary seed42 is withdrawn in view of rejected seed41. The next useful step is staged topology observation on the exact133 control, with unchanged final markers/segments required. See [route analysis](route_trace_analysis_20261015.md).

The scalar observation has now run successfully in38778082059: all source,
marker and full/selected segment hashes match the133 control. Actual cached
2D overflow and assigned3D overflow are both133. Pinned source skips3Dmaze
calls when unresolved2D congestion remains, so the later stage label is not
proof that3D repair executed. This supports investigating actual2D negotiation
and tree restoration before a physical intervention; it does not establish
selected-net topology or feasible capacity.

Use the [active-session playbook](../design/AUTONOMOUS_DEVELOPMENT.md) and [backlog](../autonomy/backlog.json). Agents perform research and implementation in the live session. The bounded supervisor automates test dispatch/collection; no continuing AI process after chat closure is claimed.
