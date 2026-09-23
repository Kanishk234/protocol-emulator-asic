# Phase 5: evidence and documentation

| | |
|---|---|
| **Dates** | Dec 7, 2026 → Jan 4, 2027 (reduced pace through finals and holidays) |
| **Goal** | Turn the verification work into evidence a judge can read and trust, and write the documentation that makes the chip usable by others. No RTL work unless a bug is found. |
| **Devices needed** | None |
| **References** | `../VERIFICATION.md` §6 (L4-IMP, L7, L8), §8, §12 |

---

## 1. Entry criteria
- Phase 4 exit checklist passed; `freeze-rtl` tagged.

## 2. Tasks

### 2.1 Remaining measurements (owner: verification)
1. **L7 mutation testing** on lane, fabric and pin units. Report the kill rate per block. For every survivor, write a new test or record why it is equivalent.
2. **L4-IMP impairment sweeps**: clock mismatch (ppm), jitter, glitches shorter than one sample, slow open-drain rise. Produce a **tolerance-envelope plot per receiver** (UART RX, I2C target, SPI target, 1-Wire), labelled "simulation".
3. **L8-SDF**: if the gds artefacts include SDF, run the pin-level suite with timing annotation at the typical corner. Otherwise record that it wasn't possible.
4. Rerun `tools/vplan_status.py`: every check ID has a passing test or proof, or an explanation.

### 2.2 Reports (owner: verification + all)
5. `docs/reports/VERIFICATION_REPORT.md`:
   - method and independence rules;
   - results per layer with numbers;
   - coverage;
   - mutation table;
   - tolerance envelopes;
   - formal results with their bounded/unbounded status;
   - bug-ledger summary (how many bugs, which layer caught them);
   - AI-assistance log and what it did or didn't find;
   - honest limits (no hardware; bounded proofs; simulation-only robustness).
6. `docs/CLAIMS.md` complete: every README claim → its evidence → its blind spot.
7. `docs/BUGS.md` complete and cross-referenced.

### 2.3 User documentation (owner: tools + architecture)
8. `docs/info.md` (the Tiny Tapeout datasheet page that the `docs` workflow builds):
   - what the chip is;
   - pinout;
   - how to load a program over the host SPI port;
   - a minimal UART example;
   - where the toolchain lives.
9. `README.md`:
   - the one-paragraph idea;
   - **novelties** in architecture and verification, with honesty labels;
   - results table (area, clock, protocols, proofs, coverage, mutation);
   - how to build, test and program;
   - honest limits.
10. `programs/README.md`: each protocol program, its slot/SRAM usage, its compiler-reported bounds, and how to run it.
11. Toolchain docs: `tripc` language reference; `tripsim` usage; the host library API.

### 2.4 Demo material
12. Waveform screenshots with sigrok decode overlays:
    - I2C target ACK timing at 1 MHz;
    - multicast capture running alongside a live protocol;
    - UART loopback.
13. A short walkthrough of the example `tripc` reports, showing the static guarantees.
14. Optional: a short screen-recorded video of compile → simulate → decode.

---

## 3. Deliverables
- `VERIFICATION_REPORT.md`, `CLAIMS.md`, `BUGS.md`, `info.md`, `README.md`, program and tool docs, demo material.

---

## 4. Phase exit checklist (all must pass)
- [ ] Mutation kill rate reported per block; every surviving mutant explained or killed.
- [ ] Tolerance envelopes produced for at least UART RX, I2C target, SPI target and 1-Wire.
- [ ] SDF gate-level run done, or its absence explained.
- [ ] `vplan_status.py`: 100% of check IDs have evidence or a written explanation.
- [ ] `VERIFICATION_REPORT.md` complete, including the honest-limits section.
- [ ] `CLAIMS.md` covers every claim in the README; no claim without evidence.
- [ ] `docs/info.md` complete; the `docs` workflow is green and the datasheet renders.
- [ ] README has the novelties, results table, build/test instructions and limits.
- [ ] Demo material committed under `docs/reports/demo/`.
- [ ] All workflows still green on `main`.

## 5. Risks in this phase
| Risk | Response |
|---|---|
| Holidays reduce availability | Do the long-running jobs (mutation, sweeps) first; they run unattended |
| Verification finds a late RTL bug | Fix it, re-harden, log it in `BUGS.md` and `AREA.md`; the freeze procedure applies |