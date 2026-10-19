# Submission rule check, October19

Checked the [official competition page](https://blog.janestreet.com/protocol-emulator-asic-competition/) after phase5 closure. It still specifies IHP130nmCMOS5L, a6x4 tile allocation and January18,2027 submission deadline. Possible8x4 is described as future expansion, not an approved current allocation. WARP retains6x4; no geometry or clock/spec change follows.

The page currently links a registration/update form and says the final submission form will be added closer to the deadline. A final submission link is not yet available there. Registration is not final submission; nothing was sent.

The linked [CMOS5L template](https://github.com/TinyTapeout/ttihp-verilog-template/tree/cmos5l) resolves through GitHub API to231f26a58b8d2efbab25bef24b29c94362a431a3, committer date2026-10-19T10:52:36Z. This records current upstream identity; it does not claim our frozen branch already incorporates every newer template change. Do not blindly merge upstream or edit template jobs. Before a final release, compare any relevant upstream changes and run release-commit GDS/precheck/gl_test and applicable CI.

This completes the current page/rules check, not submission readiness or phase6. The release commit/tag, release evidence and final form/receipt remain separate unchecked tasks. No email, form, release or external message was submitted by this check.
