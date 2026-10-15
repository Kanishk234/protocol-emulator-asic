# Loaded active fault-window cancellation

The original four-clock autonomous fault window cannot remain active through an80-clock one-byte host command. Existing loaded evidence therefore covered idle reset only. This test compiles the existing parameterized user program with COUNTER_BITS=9 and WINDOW_CYCLES=256 on frozenG1, keeping DELAY_CYCLES=4. No shell, fabric or protocol contract changes.

Load the same-job bitstream through actual SPI; trigger a window, observe idle UART inverted, issue USER_RESET while the window is active, require prompt high output and no resumed fault for300clocks. Repeat with STOP, require parked pins and LOADED, RUN again, and require no stale fault. Finally a new trigger must produce exactly256low output cycles at expected synchronized indices7–262, showing functional recovery rather than permanent suppression.

Local validation: Python syntax and parsed workflow inputs pass. Actual compiler fit and loaded simulation are pending cloud execution. Scope remains D023 configured-fabric RTL, not extracted/native timing or real hardware. No pass claim before authenticated XML and compiled-image provenance.

First cloud38676021166 failed its final waveform check:16low cycles rather than256. Root workflow invoked --set twice, dropping COUNTER_BITS override. This is test invocation BUG85, not evidence of hardware failure or active cancellation. Corrected to one parameter group; report.json must match counter9/window256/delay4 before loaded simulation. Cloud retry pending.
