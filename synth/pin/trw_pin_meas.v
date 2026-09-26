// Measurement wrapper (not chip RTL): one pin unit with its configuration block and a minimal fabric
// producer register, so the unit can be synthesized and timed alone (docs/reports/PIN_UNIT_RTL.md).
// The producer stands in for the fabric's trw_chan_prod (§4.2, §14 F3-F6) and is counted separately:
// valid/tag/data/seq, free when !valid or every blocking subscriber has taken it (`all_taken`, from the
// fabric). The consumer-port head arrives on primary inputs.
`default_nettype none
`include "trw_defs.vh"

module meas_prod (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        all_taken,
    input  wire        load,
    input  wire [1:0]  tag,
    input  wire [15:0] data,
    output wire        free,
    output reg         valid,
    output reg         seq,
    output reg  [17:0] tok
);
    assign free = !valid || all_taken;
    always @(posedge clk) begin
        if (!rst_n) begin
            valid <= 1'b0;
            seq   <= 1'b0;
            tok   <= 18'd0;
        end else if (load) begin
            valid <= 1'b1;
            seq   <= !seq;
            tok   <= {tag, data};
        end
    end
endmodule

module trw_pin_meas #(
    parameter FULL = 0
) (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        live,
    input  wire        we,
    input  wire [4:0]  waddr,
    input  wire [15:0] wdata,
    input  wire [23:0] pads,
    input  wire        tx_avail,
    input  wire [1:0]  tx_tag,
    input  wire [15:0] tx_data,
    output wire        tx_take,
    input  wire        all_taken,
    output wire        p_valid,
    output wire        p_seq,
    output wire [17:0] p_tok,
    output wire        a_out,
    output wire        a_oe,
    output wire        n_out,
    output wire        n_oe,
    output wire        late,
    output wire        overrun,
    input  wire        clr_late,
    input  wire        clr_overrun
);
    wire [`TRW_PC_BITS-1:0] cfg;
    wire restart, free, load;
    wire [1:0]  tag;
    wire [15:0] data;

    trw_pin_cfg #(.FULL (FULL)) u_cfg (
        .clk (clk), .rst_n (rst_n), .we (we), .waddr (waddr), .wdata (wdata), .cfg (cfg), .restart (restart)
    );
    trw_pin_unit #(.FULL (FULL)) u_unit (
        .clk (clk), .rst_n (rst_n), .restart (restart), .live (live), .cfg (cfg), .pads (pads),
        .tx_avail (tx_avail), .tx_tag (tx_tag), .tx_data (tx_data), .tx_take (tx_take),
        .rx_free (free), .rx_load (load), .rx_tag (tag), .rx_data (data),
        .a_out (a_out), .a_oe (a_oe), .n_out (n_out), .n_oe (n_oe),
        .late (late), .overrun (overrun), .clr_late (clr_late), .clr_overrun (clr_overrun)
    );
    meas_prod u_prod (
        .clk (clk), .rst_n (rst_n), .all_taken (all_taken), .load (load), .tag (tag), .data (data),
        .free (free), .valid (p_valid), .seq (p_seq), .tok (p_tok)
    );
endmodule
