# R1 management-shell integration gate

The diagnostic candidate now has a test path through the unchanged production
management shell. G1 remains the selected chip. This gate does not establish
physical macro assembly, detailed routing, extracted timing or replacement
acceptance.

The adapter derives all fabric connections from the frozen candidate pin map.
It retains the production two-stage reset synchronizer, separate configuration
reset, synchronized user inputs, registered user outputs and parking gates after
the output registers. Both user-reset inputs have the production polarity.
The only candidate-specific shell parameter is diagnostic architecture `0x00fe`;
the frame loader uses the candidate's five rows and eight columns. Production
RTL, configuration and G1's architecture identifier are unchanged.

The traffic test uses only top ports with the existing `warp_host` SPI transport and independent
host protocol library. It checks READ_ID, wrong-architecture rejection, bad-CRC
rejection, refusal to RUN after either error, a complete 962-word primary image
load, LOADED parking and RUN. It sends commands through CH_WRITE and withholds
CH_READ until the UART and SPI producers complete, exercising the two-entry
response FIFO and fabric backpressure. UART TX `a5`, UART RX `69`, SPI mode-0
MOSI `3c` and MISO `ff` must pass, with a positive three-way activity overlap.
READ_STATUS acknowledges sticky errors, so subsequent refused RUN reports
BAD_COMMAND as specified.

It also checks USER_RESET leaves the shell RUNNING with idle protocol outputs,
STOP parking, restart without reload, then another complete load without chip
reset. A new SPI `5a` transaction and `ff` response must succeed after this reload.
The final state is LOADED with outputs parked.

All 40 leaf instances use the exact independently audited native exports from
40030916359 and 40033384495; the generated interconnect and shell remain RTL.
The adapter has a focused mapping/reset ownership guard. The simulation runner
hashes inputs before execution and refuses changed inputs afterward, retaining
strict XML, activity windows, generated wrapper and source/tool provenance.
The hosted workflow retains both the existing direct-frame/configuration-Q
observation and this new shell test as separate checks against the same inputs.

Read-only native configuration observation, when enabled, compares the complete
first-load and reloaded tile Q dictionaries. It is separate from the traffic
oracle and is not an independent expected-bit comparison.

## Actual results and open failure

The preceding direct-frame native gate 40066466677 at `e192b67` passed. Root
reauthentication checked all 48 inputs, both simulator binaries, one strict
functional case, five guards, 8,340 ns logical three-way overlap and the 8,736-Q
snapshot. All three loaded-RTL controls passed 40066466659 at the same source.

The full management-shell sequence passes generated RTL locally on Icarus 12
and 13 (`build/r1_shell_rtl_progress` and `build/r1_shell_rtl_icarus13`, one strict
case each, 8,500 ns logical overlap). Native leaves pass the first concurrent
traffic and response checks, but the new second-transfer test exposes BUG132.
Native full-shell completion is **not passed**. The full variant stalls during
the first postreload CH_WRITE at 10,712,400 ns; the restart-only control reproduces
without reloading at 5,460,560 ns. Both image observations contain the same
8,736 native configuration values. Evidence directories:
`build/r1_shell_reload_state` and `build/r1_shell_native_restart`; wall timeouts
are failures, not acceptance. A bare-mapped control timed out during the second
load and does not yet distinguish bare mapping from native placement/buffering.
Interactive scheduler inspection follows the upstream
[Icarus debugger documentation](https://steveicarus.github.io/iverilog/usage/vvp_debug.html).
The root cause and responsible event path remain open. The workflow requires
the complete sequence and never substitutes the restart-only diagnostic.

No SDF or extracted parasitics are used; activity windows are logical
simulation observations, not measured silicon performance.
