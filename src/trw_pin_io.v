// Pin unit, input side: selects pins A (or S), B and C from the pad vector, keeps each one's value from
// the previous clock (edge detection), and computes "selected" (§14 P15).
//
// Timing contract:
//   - `pads` is what a unit sees in clock n: synchronised inputs (§14 P1: the pad of clock n-2) and,
//     for `uo` output pads, the driven value directly (P7). Pads 24..30 do not exist and act as 31
//     (not attached).
//   - `a_in` is pin S if attached, else pin A, else IDLE; `b_in` is pin B, else 0. `sel` is 1 while
//     pin C equals C_ACTIVE, and always 1 without a pin C.
//   - `*_prev` and `sel_q` are the same values one clock earlier. They are plain delay registers with
//     no reset (they are known one clock after the pads are), so neither reset nor a configuration
//     restart ever creates an edge. `sel_fall` = 1 in the clock pin C becomes inactive (P15).
`default_nettype none

module trw_pin_io (
    input  wire        clk,
    input  wire [23:0] pads,
    input  wire [4:0]  pin_a,
    input  wire [4:0]  pin_s,
    input  wire [4:0]  pin_b,
    input  wire [4:0]  pin_c,
    input  wire        idle,
    input  wire        c_active,
    output wire        a_in,
    output reg         a_prev,
    output wire        b_in,
    output reg         b_prev,
    output wire        c_in,
    output reg         c_prev,
    output wire        sel,
    output reg         sel_q,
    output wire        sel_fall
);
    wire       s_on  = (pin_s < 5'd24);
    wire [4:0] a_idx = s_on ? pin_s : pin_a;
    wire       a_on  = (a_idx < 5'd24);
    wire       b_on  = (pin_b < 5'd24);
    wire       c_on  = (pin_c < 5'd24);

    // Index the pad vector only with in-range values (the `*_on` checks pick the default otherwise).
    wire       a_pad = pads[a_on ? a_idx : 5'd0];
    wire       b_pad = pads[b_on ? pin_b : 5'd0];
    wire       c_pad = pads[c_on ? pin_c : 5'd0];

    assign a_in = a_on ? a_pad : idle;
    assign b_in = b_on && b_pad;
    assign c_in = c_on ? c_pad : c_active;
    assign sel  = (c_in == c_active);
    assign sel_fall = sel_q && !sel;

    always @(posedge clk) begin
        a_prev <= a_in;
        b_prev <= b_in;
        c_prev <= c_in;
        sel_q  <= sel;
    end
endmodule
