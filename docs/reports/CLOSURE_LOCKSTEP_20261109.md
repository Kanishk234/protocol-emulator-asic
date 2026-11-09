# Current-candidate RTL/model lockstep evidence

[Run 42697037494](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42697037494)
at `d65498520d9f99005469e76c2a082fdabc931851` is SUCCESS.
This prepares the exact current two-lane/four-unit closure candidate and uses
the existing directed L2 bench and independent `tripsim` model.

- One million comparison clocks pass with zero divergences. Downloaded
  `million.xml` contains one executed passing case, without skips/errors, and
  the actual simulator log records all 1,000,000 compared clocks.
- Clean RX and cursor controls each pass one executed case.
- Reversed-priority RTL produces a scoreboard assertion at compared clock 99.
- The cursor increment fault produces a directed mismatch at clock 326.
- Both mutants contain the expected single failing XML case, without skips or
  infrastructure errors. Their raw logs and source copies are retained.

Independently reconciled all 170 input hashes: 141 against source Git objects,
29 against the independently prepared candidate. Checked all 25 files in
each retained mutant tree: every file is unchanged except the one exact
intended source edit. XML hashes and compact classification are retained in
[`closure_lockstep_42697037494.json`](closure_lockstep_42697037494.json).

This refreshes the named directed lane/channel/pin workload. It is not formal
proof, arbitrary-program coverage, exhaustive architectural equivalence,
physical timing, or a silicon result. Two detected planted faults do not
establish a broad mutation score.

The baseline unit workflow 42692486070 also finishes SUCCESS. That is baseline
source CI, not a substitute for this candidate-specific result or the separate
protocol and physical jobs. No Phase 2 completion is claimed.
