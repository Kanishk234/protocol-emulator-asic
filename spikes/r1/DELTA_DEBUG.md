# Observing a non-advancing native simulation

`delta_watchdog.c` is the read-only VPI diagnostic used to narrow BUG132.
It registers value-change observers on module nets/registers, counts changes
at one simulation timestamp and prints the busiest signals before terminating
the experiment if one exceeds1,000changes. It does not force values, insert
delays or repair the design. Its stop is a **failed diagnostic**, never a passing
test; continue to require strict cocotb XML and authenticated inputs.

Build with the same Icarus headers/runtime as the failing experiment:

```sh
gcc -shared -fPIC -O2 \
  -I "$ICARUS_ROOT/usr/include/iverilog" \
  spikes/r1/delta_watchdog.c -o build/r1_delta_watchdog.vpi
```

Load with `vvp -m "$PWD/build/r1_delta_watchdog" ...`, preserving the original
cocotb VPI library and runtime arguments. In a diagnostic `cocotb_tools` runner,
append `['-m', str(module_path_without_suffix)]` to `test_args`. Record the
additional module's source/binary hashes and identify the result as instrumented;
do not substitute it for an uninstrumented acceptance run.

`WARP_DELTA_START_TICKS` selects the observer start time, default0. Its unit is
the simulator's global precision tick, **not nanoseconds**. In the1ps BUG132
short reproducer,212059999starts observation just before the failing212060ns
edge. Arming late avoids observing irrelevant configuration transients and
reduces overhead. The tool observes module scopes; it is not a complete
oscillation proof or a universal scheduler watchdog.

The adjacent fixture has an intentional zero-delay loop when `OSCILLATE=1`
and a finite control when0. Compile it with the same Icarus runtime and verify
the former prints `DELTA_WATCHDOG stuck` and exits2, while the latter reaches
`$finish` without that marker and exits0. The observer flushes its diagnosis and
aborts the experiment immediately: a deferred simulator finish can itself wait
for the nonconverging timestamp. Missing XML is a failure. Inspect the diagnostic
and strict test results, not only the process status.

Interactive scheduler inspection uses the upstream
[Icarus debugger](https://steveicarus.github.io/iverilog/usage/vvp_debug.html).
Compile instrumentation with `-pfileline=1` before using `trace on`; `step`
executes one scheduled event. Repeated activity at one timestamp narrows a
simulation nonconvergence; it does not by itself establish physical oscillation.
