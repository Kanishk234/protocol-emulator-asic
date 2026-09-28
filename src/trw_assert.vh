// RTL invariants (VERIFICATION.md L0-ASRT): written once, inside the modules, as
//     `TRW_ASSERT(cond, "message")
// checked at every rising edge of `clk` outside reset (`rst_n` high), on the values of the clock that edge ends.
//   - FORMAL:     an immediate `assert` in a clocked process, for SymbiYosys.
//   - SIM_ASSERT: a Verilog check that prints the instance and message and calls $fatal, so every simulation with
//                 SIM_ASSERT defined (test_internal/ Makefiles) checks it.
//   - otherwise (synthesis, LibreLane, lint): nothing.
// The module must have `clk` and `rst_n`. `cond` must not contain a top-level comma (use a wire).
`ifndef TRW_ASSERT_VH
`define TRW_ASSERT_VH
// TRW_ASSERT_ON is defined when checks are active: helper wires for a check go inside `ifdef TRW_ASSERT_ON.
`ifdef FORMAL
`define TRW_ASSERT_ON
`define TRW_ASSERT(cond, msg) always @(posedge clk) if (rst_n) assert (cond);
`elsif SIM_ASSERT
`define TRW_ASSERT_ON
`define TRW_ASSERT(cond, msg) always @(posedge clk) if (rst_n && !(cond)) begin $display("TRW_ASSERT %m: %s", msg); $fatal(1); end
`else
`define TRW_ASSERT(cond, msg)
`endif
`endif
