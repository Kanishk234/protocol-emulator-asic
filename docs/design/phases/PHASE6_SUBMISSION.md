# Phase 6: submission

| | |
|---|---|
| **Dates** | Jan 5 → Jan 11, 2027 (hard deadline Jan 18; the last week is buffer) |
| **Goal** | Prove the repository builds from scratch, tag the release and submit. |
| **Devices needed** | None |
| **References** | `../PHYSICAL_DESIGN_AND_CI.md` §6, §9 |

---

## 1. Entry criteria
- Phase 5 exit checklist passed.

## 2. Tasks
1. **Fresh-clone check** (someone other than the usual CI owner):
   - clone the repo into a new WSL directory;
   - follow only the README;
   - run `scripts/check_all.sh`;
   - compile one program with `tripc`;
   - run it on `tripsim` and in RTL simulation.
2. **Final CI run** on the release commit, by hand:
   - `test`
   - `docs`
   - `gds` (gds, precheck, gl_test, viewer)
   - `lint`
   - `unit`
   - `formal`
   - `fpga`
3. Confirm the **GitHub Pages** viewer shows the release design.
4. Check the repository hygiene:
   - licence present;
   - third-party code credited, with licences recorded;
   - no secrets;
   - `info.yaml` complete.
5. Tag **`v1.0`**; attach the gds artefacts, verification report (PDF export optional) and demo material to the GitHub release.
6. Submit through Jane Street's process (form or instructions from them), and through Tiny Tapeout if they ask for it. Keep a copy of the confirmation.
7. Post-submission: freeze `main`; further work goes on branches.

---

## 3. Deliverables
- `v1.0` release with artefacts; submission confirmation.

---

## 4. Phase exit checklist (all must pass)
- [ ] Fresh clone builds and tests green by following the README alone.
- [ ] Every workflow green on the release commit; Pages viewer live.
- [ ] Licence, credits and third-party licences in order.
- [ ] `v1.0` tag and GitHub release with the gds artefacts and reports.
- [ ] Submission made and confirmation saved (date recorded in `DECISIONS.md`).
- [ ] Submitted **on or before Jan 11**, leaving the buffer week unused.

## 5. Risks in this phase
| Risk | Response |
|---|---|
| A CI service change breaks the build | Pin action versions; keep the last green artefacts; use the buffer week |
| Submission process unclear | Ask Jane Street in December, not in January |