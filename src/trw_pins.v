// Pad outputs (ARCHITECTURE.md §7.1, §10): one 3-bit owner register per drivable pad and the output
// multiplexer. Only the owning unit can drive a pad, so two drivers are impossible by construction (A4).
//
// Pads 8..23 are uo_out[0..7] and uio[0..7] (spec/tripwire.yaml `pads`); owner register i is pad 8 + i
// (host address 0x30C0 + i, §7.2). Owner codes 0..NU-1 select a unit; any other code is none (7 after
// reset). The host pads (MISO uo3, IRQ uo6) ignore owner writes and are driven by the top.
//
// A pad owned by unit u shows that unit's pin A output if the unit's pin A is that pad, else its pin N
// output if pin N is that pad, else nothing (value 0, OE 0). Open drain (OD) and C_OE are applied inside
// the unit (trw_pin_unit), so `a_oe`/`n_oe` already carry them.
//
// Timing contract: owners are flops (reset: none) written at the edge of the host write clock and
// readable (`own_q`). The outputs are combinational from the owners, the units' registered pin outputs
// and their static pin configuration.
`default_nettype none
`include "trw_defs.vh"
`include "trw_assert.vh"

module trw_pins #(
    parameter NU = 6
) (
    input  wire          clk,
    input  wire          rst_n,
    // host: owner register write (index 0..15 = pad 8..23) and readback
    input  wire          own_we,
    input  wire [3:0]    own_waddr,
    input  wire [2:0]    own_wdata,
    input  wire [3:0]    own_raddr,
    output wire [2:0]    own_q,
    // units
    input  wire [NU-1:0]   a_out,
    input  wire [NU-1:0]   a_oe,
    input  wire [NU-1:0]   n_out,
    input  wire [NU-1:0]   n_oe,
    input  wire [5*NU-1:0] pin_a,        // pad numbers from each unit's configuration
    input  wire [5*NU-1:0] pin_n,
    // pads 8..23: {uio[7:0], uo[7:0]}
    output reg  [15:0]   pad_out,
    output reg  [15:0]   pad_oe
);
    localparam [15:0] HOSTPAD = 16'h0048;        // uo3 (MISO) and uo6 (IRQ): index 3 and 6

    reg [47:0] own;
    integer oi;
    always @(posedge clk) begin
        if (!rst_n)
            own <= {16{3'd7}};
        else if (own_we && !HOSTPAD[own_waddr])
            for (oi = 0; oi < 16; oi = oi + 1)
                if ({28'd0, own_waddr} == oi) own[3*oi +: 3] <= own_wdata;
    end
    assign own_q = own[3*own_raddr +: 3];

    integer i, u;
    always @* begin
        pad_out = 16'd0;
        pad_oe  = 16'd0;
        for (i = 0; i < 16; i = i + 1)
            for (u = 0; u < NU; u = u + 1)
                if ({29'd0, own[3*i +: 3]} == u) begin
                    if ({27'd0, pin_a[5*u +: 5]} == i + 8) begin
                        pad_out[i] = a_out[u];
                        pad_oe[i]  = a_oe[u];
                    end else if ({27'd0, pin_n[5*u +: 5]} == i + 8) begin
                        pad_out[i] = n_out[u];
                        pad_oe[i]  = n_oe[u];
                    end
                end
    end

`ifdef TRW_ASSERT_ON
    // at most one driver per pad: an enabled pad has a valid owner (the multiplexer picks only the owner)
    reg bad_drive;
    integer bi;
    always @* begin
        bad_drive = 1'b0;
        for (bi = 0; bi < 16; bi = bi + 1)
            if (pad_oe[bi] && ({29'd0, own[3*bi +: 3]} >= NU))
                bad_drive = 1'b1;
    end
    `TRW_ASSERT(!bad_drive, "a pad is driven without an owner")
`endif
endmodule
