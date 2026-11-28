# Submission readiness — 2026-11-28

WARP's R1 successor remains experimental. G1 remains the selected fallback;
its historical physical/protocol evidence does not qualify a changed R1 macro.

| Item | Current evidence | Remaining work |
|---|---|---|
| R1 real loading and primary traffic | 46177440003: UART/SPI, reset/restart, management reload; three actual8736-bit observations | Repeat on any changed physical artifact; establish all advertised protocol/rate evidence |
| R1 configured timing | Same run: setup-6.517231ns, hold-1.567830ns, zero loops and complete14497-pin annotation | Both slacks nonnegative, real shell/boundary context, required corners/modes |
| Internal hold diagnosis | r1_hold_inventory_46177440003.json:82self-feedback minima and23boundary-launch minima | Physical feedback repair plus boundary/input work; input buffers alone do not address both |
| New physical experiment | D193:58data buffers in original primitive1footprint;17local guard checks | First fit/global-route screen, then detailed route/extraction, native/reload, all affected contexts and complete integration |
| Selected G1 fallback | Phase2/3 historical GDS/precheck/GL and UART/SPI/I2C evidence; see phase summaries | Reproduce release build with current submission template and accurate supported-capability documentation |
| Release | Phase6final GDS/release/tag/submission checkboxes remain open | Final release CI, public evidence/package, submission and receipt |

Official rules checked again at
[Jane Street's FAQ](https://blog.janestreet.com/protocol-emulator-asic-competition/#faq).
They specify 8x4 and template main for CMOS5L, January18,2027 deadline;
eFPGA entries are permitted. There is no mandated clock target. A public repo,
passing TT GDS/precheck, architecture/toolchain/examples and verification
write-up are requested. This does not turn a negative timing result into closure.
The agreed engineering target remains20ns/0.25ns; any target/spec change needs
its own review and protocol-rate evidence.

The local info.yaml still says6x4. The October19rules report is historical,
not current submission guidance. The current upstream main commit is
`1b6c4c79c9f29510ba8bfe4a61c7dfcc9f202063` (2026-11-25). Its GDS jobs
use `ttihp27a`, while local jobs use `ihp-cmos5l`. Trigger/concurrency differences
are intentional WARP policy. No template job, selected geometry or production
config has been changed during the isolated timing experiment. Release migration
requires a separate controlled integration and fresh hardening; repository rules
prohibit casually editing template jobs or changing the architecture contract.

There is no justified completion percentage or completion date yet. The physical
probe is intended to resolve a specific uncertainty: whether the additional
real cells fit and route at the fixed primitive footprint. Passing that screen
would still leave extraction, actual timing and integration gates.

Upstream file receipts (GitHub API contents at that exact commit):

- `info.yaml`: SHA256 `183c4b9bc7dde9f0ee335f61e5654664f2cb5ba6df204eeff2cbdbac750c1d2e`.
- `gds.yaml`: SHA256 `72b449d7e552a92814f3adba428550a84b88aa4373b9f5d9743d2080876eb729`.
