# Autonomous triggered UART fault window

This user bitstream wraps the existing UART plus independent rising-edge event monitor. FAB_IN2 (`fault_i`) becomes a trigger instead of a level-controlled inverter. A rising edge accepted while idle schedules one delayed, bounded inversion of the UART transmit line. Timing after acceptance is handled entirely by fabric logic; the host does not need to issue a precisely timed inversion-off command. UART receive/transmit and event counting continue concurrently.

This is an electrical line-corruption demonstration, not a protocol-aware detector or protection mechanism. It can invert idle, start, data, or stop levels depending on when triggered. It does not choose which byte or bit is affected, ensure a receiver detects the fault, or synchronize its schedule to a UART frame. The independent event counter remains modulo 16 in `h_status[7:4]`; UART flags remain in `h_status[3:0]`.

## Interface and cycle contract

Pins and host streaming match `fault.yaml`: FAB_IN0=UART RX, FAB_IN1=event monitor, FAB_IN2=fault trigger, FAB_OUT0=UART TX. Shell inputs are already synchronized; schedule times below start at the edge where the user logic accepts the synchronized rising trigger, rather than at the external pin transition.

Let E be that acceptance edge. With DELAY_CYCLES=D, inversion begins just after E+D and ends just after E+D+WINDOW_CYCLES. D=0 starts immediately after E. WINDOW_CYCLES must be positive. The defaults wait four fabric clocks, invert for four clocks, then return to transparent transmission. All counters use fabric clocks, not UART bit periods. Divider DIV=16 is inherited from the existing UART implementation; physical rate still depends on the separately qualified chip clock.

Only one operation is outstanding. Rising edges during waiting or inversion are discarded, not queued. A trigger on the edge that ends the window is also discarded. Holding the trigger high produces a single window; after returning idle, drive it low and raise it again to retrigger. Reset cancels waiting or active windows and restores transparent transmission. A trigger held high through reset is accepted on the first user clock after reset release because trigger history resets to zero. STOP parks chip outputs through the shell.

Supported compile-time parameter domain:

- COUNTER_BITS: 1–16.
- DELAY_CYCLES: 0–2**COUNTER_BITS.
- WINDOW_CYCLES: 1–2**COUNTER_BITS.
- DIV: use the existing UART's supported divider domain.

Invalid values are unsupported and can truncate; synthesis HDL deliberately contains no initial assertions. Check parameters before compiling. One counter is reused for delay and duration. This consumes soft logic only: it adds no hard timer or shift resources beyond the two timers and two shifters already used by UART. Area/fit and behavior require cloud evidence; no achieved rate, physical timing, or loaded-fabric pass is claimed here.

## Compile

Activate the project venv and provision the pinned compiler tools in cloud CI:

```sh
PYTHONPATH=tools python -m compile.compile --pins protocols/uart_monitor/trigger.yaml \
  -o build/uart-trigger-fault protocols/uart_monitor/uart_trigger_fault_top.v \
  protocols/uart_monitor/uart_fault_monitor_top.v \
  protocols/uart_monitor/uart_monitor_top.v protocols/uart/uart_top.v \
  protocols/uart/uart_tx.v protocols/uart/uart_rx.v \
  protocols/uart/uart_tx_p.v protocols/uart/uart_rx_p.v
```

The wrappers are regular Verilog sources supplied to the unchanged compiler.
