# Organizer update and TRIPWIRE implications

Source: organizer email supplied by the user on2026-10-09. This records its implications, not new hardware verification.

- Retain6x4 as baseline. Planned maximum8x4 is an upgrade once the official CMOS5L template is released; expected around mid-October is not proof of availability. Keep the2-lane/4-unit candidate until official closure before considering the previously requested3-lane/6-unit expansion.
- Competition has no required clock frequency or fixed protocol speeds. Our50MHz/20ns target remains a project requirement. Changing it would need an explicit project decision; this update does not relax current timing gates.
- UART/SPI/I2C come first. Common settings, modes0–3, concurrent operation and controller/target roles are encouraged, with concurrency/dual roles explicitly optional. Existing claims must still distinguish demonstrated cases from unimplemented modes.
- SRAM macros, including multiple macros, are allowed within area and Tiny Tapeout precheck. No capacity expansion proposed before Phase2 exit.
- CMOS5L pad timing is not yet characterized. Corrected the older66MHz pad claim in overview/physical docs; internal STA does not establish measured external-pad performance.
- Submission needs a public RTL/test/toolchain/documentation repository and passing Tiny Tapeout GDS/precheck. Flexibility is the main judging emphasis. Deadline remains2027-01-18; our earlier target remains unchanged. Document AI use.
- Same Tiny Tapeout flow may run locally if GitHub's6h job limit is hit. That provides a runtime fallback, not permission to substitute a different physical flow or skip official checks.
- Board deselection loses state; document reloading after re-selection. External pull-ups/transceivers/level shifting are permitted and should be documented for exercised protocols.

## SRAM walkthrough cross-check

Read the organizer-linked [IHP SRAM integration walkthrough](https://kdp1965.github.io/ihp-um-janestreet-prism/ihp_sram_macro.html). Its worked example uses different macro geometry and an8x4 floorplan. Useful review points are pin-face placement, macro halo, Metal4 supply-column/grid alignment, explicit macro power connections, antenna loading and signoff/precheck. Do not copy its PDN dimensions, custom hooks or waivers without matching our512×16 macro views and accepted flow. No configuration or checking gate was changed from this reference.

Our existing output-buffer relocation directly addresses the placement point; actual relocation screen37978260010 passes, but detailed extraction and electrical closure remain pending. Antenna-aware data fanout repair and exact signoff evidence remain active work.
