# PDForge

PDForge is a backend-independent, evidence-first physical design engineering harness.
This release is an infrastructure implementation under active validation, **not a
validated Level 3 autonomous closure system**. It never changes production RTL or
relaxes qualification. Local EDA installations are optional.

Use the project venv (standard library only for PDForge):

```sh
source .venv/bin/activate
python -m unittest discover -s pdforge/tests -v
python -m pdforge doctor
python -m pdforge benchmark
python -m pdforge --help
```

State, report downloads, agent transcripts, copies and raw evidence belong in
`pdforge/.local/`, which is ignored. SQLite uses immediate transactions and a
unique content fingerprint. Each admitted experiment charges its entire declared
upper bound; failed and abandoned jobs do not refund reservations. Default caps:
one active experiment, two full flows, 12 hours elapsed and aggregate CPU,
720 remote runner minutes, $5 configured spend reservation, 10 GB disk reservation,
100,000 agent tokens. Spend reservations are user-configured bounds, not a provider
price estimate or a measured invoice. The remote validation bridge requires a
five-minute and $0.10 reservation, permits only static infrastructure validation,
and uses a five-minute GitHub job timeout. No expensive EDA job is enabled.

Commands emit JSON; malformed evidence returns a nonzero exit status. Examples:

```sh
python -m pdforge ingest /path/max.rpt --stage extracted --corner nom_slow_1p08V_125C --unit ns
python -m pdforge diagnose /path/max.rpt --stage extracted --corner nom_slow_1p08V_125C --unit ns
python -m pdforge ingest /path/metrics.json --stage global_route --metrics
python -m pdforge compare pdforge/.local/before.json pdforge/.local/after.json
python -m pdforge retrieve pdforge/.local/knowledge-manifest.json 'hold congestion'
python -m pdforge propose pdforge/examples/validation.json
python -m pdforge campaign pdforge/examples/validation.json --backend github --dry-run
python -m pdforge campaign pdforge/examples/validation.json --backend github --reserve
python -m pdforge status
python -m pdforge resume
python -m pdforge export
```

`--reserve` records a queued experiment but performs no remote action. `--dry-run`
performs neither. To actually submit an authorized PDForge validation job, use the
experiment UUID returned by reservation and the exact **published** revision:

```sh
python -m pdforge remote dispatch EXPERIMENT_UUID --revision PUBLISHED_40_HEX_SHA --authorize-remote
python -m pdforge remote poll EXPERIMENT_UUID
python -m pdforge remote download EXPERIMENT_UUID
python -m pdforge remote validate EXPERIMENT_UUID --artifact-dir pdforge/.local/artifact-RUN_ID
```

Dispatch is confined to the existing `repo-audit.yaml` workflow on `autonomous-pd`
or `pdforge/*`. It uses a token-specific infrastructure job; normal audits retain
their checks. No official jobs were edited. Existing push workflows run on every
branch: publication commits use `[skip ci]` and the intended job is dispatched
explicitly. The GDS workflow has branch-specific cancellation; PDForge does not
submit it. Do not remove skip markers without reviewing resource impact.

Intent and token are durable before dispatch. If the API response is lost, resume
searches for that token, branch and SHA instead of retrying submission. Ambiguous
matches require investigation. Success of a GitHub run alone is not experiment
success: matching downloaded test evidence is mandatory. Artifact bytes are bound
to GitHub's digest and source revision/run/attempt/token. Public reference reads
and authorized GitHub operations are the only network operations implemented.
Native/cloud dispatch remains disabled until a provider and isolation policy are
configured. The process supervisor is a trusted-adapter utility, not a sandbox.

Physical observations carry file/hash/line evidence, stage, corner and original
units. Explicit `--unit` is an operator attestation when a report omits units.
Reports are incomplete by default; no TNS is inferred from a limited path sample.
Metric mappings are explicit and unknown keys remain unknown. Geometry, SPEF
attribution, RTL mapping and causal certainty cannot be inferred from pin counts.
Independent candidate reviews must name collateral checks: improving setup while
breaking hold or routing is rejected. Synthetic policy benchmarks cover 13 PD
categories; they do not establish real root-cause accuracy or closure gains.

See [STATUS.md](STATUS.md), [WORKLOG.md](WORKLOG.md), and
[bootstrap/DESIGN.md](bootstrap/DESIGN.md) for gates and remaining work.
