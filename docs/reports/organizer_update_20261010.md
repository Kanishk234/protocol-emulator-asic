# Organizer email: implications for WARP

Source: the complete Ben/Anish competition update supplied by the user on
October10,2026. This is organizer correspondence, not a new measured result.

## Design priorities

Reprogrammability and flexibility remain central. UART/SPI/I2C are baseline
demonstrations, not the architecture's boundary. The user's explicit goal is
the broadest practical protocol coverage. Keep generic programmable resources
and the real Verilog-to-bitstream toolchain; avoid dedicated protocol silicon.
Support claims remain limited by demonstrated capacity, timing, pins and
electrical requirements. Universal support cannot be inferred from three tests.
Independent evaluation still follows the held-out policy; opened G1 workloads
cannot become fresh independent evidence for a successor.

Continue designing to6×4. The email expects8×4 around mid-October and says to
treat it as an upgrade until released. More area could supply routing whitespace
or additional resources, but an upgrade needs the actual template, matching
flow and an equal-area comparison. Do not assume it fixes existing errors.

There is no required core clock or protocol speed. Choose eventual rates from
extracted timing and demonstrated operation. Our existing20ns experiments stay
matched; changing a timing target requires a separate documented decision,
not relabeling a failing experiment as passing. Pad characterization is pending,
so core timing alone does not establish external signal performance.

## SRAM research path

The email explicitly permits multiple IHP SRAM macros when they fit and pass
precheck. It links [Ken Pettit's walkthrough](https://kdp1965.github.io/ihp-um-janestreet-prism/ihp_sram_macro.html)
for RTL, LibreLane configuration, Metal4 power and sign-off. The browser could
not access the page, but its complete public HTML source was subsequently
read through GitHub at site/ihp_sram_macro.html.

The [walkthrough source](https://github.com/kdp1965/ihp-um-janestreet-prism/blob/main/site/ihp_sram_macro.html)
describes explicit SRAM instantiation, separate synthesis black boxes and
functional RTL/GL models, registered reads, mask/enable semantics, corner
libraries and CDL. Its Metal4 grid must align with both supply groups and
avoid signal pins; full-height stripes can collide with another macro.
It also documents antenna repair and project-specific Magic overlap waivers.
These are useful integration lessons, not validated WARP settings. We will
retain WARP's checks, inspect real conductor geometry and use unmodified
official precheck rather than copy waivers or whitelist patches. Its PDK pin
matches spikes/cloud/fetch_pdk.sh, but macro details still need authentication.

Useful hypotheses include generic sample/capture storage, queues and larger
user state. SRAM cannot directly replace all distributed configuration latch
outputs: the fabric needs many simultaneous control signals, while a macro
has a limited number of read ports. A configuration backing store still needs
distribution/shadow storage and a loading architecture. Measure complete area,
power access, routing obstructions, latency, tool mapping and real loaded tests.
Metal4 power competes with routing resources and merits a physical screen.
No SRAM or architecture change is authorized by this research note alone.

## Submission and board behavior

The submission needs public RTL/tests, a passing Tiny Tapeout GDS/precheck,
architecture/toolchain/examples and verification documentation. The email's
GDS-action installation fix is not evidence that our native placement or
congestion failures are setup errors; preserve their actual diagnostics.
Stick to the Tiny Tapeout flow. Hosted jobs retain the six-hour limit.

Digital-only pins permit external pull-ups, transceivers and level shifting;
document required Pmods and pin assignments. Internal mixed-signal options are
allowed, but PLL/analog additions would require new design and sign-off evidence.
Reset must establish known state. Deselection powers the chip down and loses
state, so the host must reload after reselection. Test/document this lifecycle;
do not rely on FPGA initialization or retained configuration.

Document AI-assisted research, RTL/tool development, diagnosis and verification
honestly in the submission write-up. A video is optional. Registration is
confirmed by receipt of this email; no further registration action is needed.
The January18,2027 deadline remains, with planned selection in early February
and a March shuttle. Hardware and future flow changes still need validation.
