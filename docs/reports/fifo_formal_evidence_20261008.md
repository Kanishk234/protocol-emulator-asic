# F3 FIFO CI evidence recovered

[Formal36491754401](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36491754401),
commit ee259cb48dbbb82b233bc6ac68e558cd8942beab, succeeds. Downloaded
formal-f3_fifo artifact contains separate d2/d4 logs. Both report
Property proved, engine abc pdr returned PASS and DONE(PASS,rc=0).

F3 checks FIFO behavior against the shadow queue in formal/f3_fifo.sv at
depth2 and depth4. formal/f3_fifo.sby uses mode prove and abc pdr; its depth12
setting is not a bounded-proof ceiling. These are unbounded PDR results for
the named FIFO properties, not whole-chip or physical/timing verification.
The FIFO overflow status in the shell remains a separate transaction check.

git diff of that commit against current HEAD for formal/f3_fifo.sby,
formal/f3_fifo.sv and src/wp_fifo.v is empty. No new proof was executed
locally or claimed from a changed implementation. This replaces stale
local-only wording in EVIDENCE; the broader numerical evidence audit and
phase5 exit remain open.
