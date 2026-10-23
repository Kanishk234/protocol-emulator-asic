# R1 all-mapped configured primary

D109 replaces all40fabric tile instances with frozen exported IHP mapped-cell netlists (16LUT,2PRIM,22border/I/O). The configuration frame FSM remains RTL. All ten exact netlist hashes and unchanged pinned PDK model bytes are checked before compilation; Icarus13version and both executable hashes recorded.

Local build/r1_full_mapped_smoke_v3/results.xml executes1PASS, with47input hashes rechecked, covering real frame-FSM loading, concurrent UART TX A5/RX69, SPI mode0 3C/FF, host-response backpressure and compiled timing ratios. First attempt failed only an RTL-internal debug-name lookup (BUG127); all traffic assertions remain intact. Source was the39c656a working tree with D109changes captured by input hashes; hosted committed-source replay pending.

No management SPI shell/CRC/parking, post-route netlist/SDF, configured timing or whole-chip acceptance is established. Other protocol cases and secondary UART+I2C compiler timeout remain open.
