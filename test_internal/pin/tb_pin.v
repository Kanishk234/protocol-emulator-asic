// L1 pin-unit harness (white-box, test_internal/): one trw_pin_cfg + trw_pin_unit, a stand-in fabric
// producer with one subscriber, and a pad model.
//   - Config words are written through the real latch block (we/waddr/wdata), as the host would.
//   - Pads: `pads_ext` is what the outside world drives. A pad the unit drives (pin A or N with its OE
//     on) shows the unit's value; otherwise it shows `pads_ext` (so an open-drain release reads the
//     external level). `line` is the resulting pad level. ui/uio pads reach the unit through 2-FF
//     synchronisers (§14 P1); uo pads directly (P7).
//   - Producer: valid/seq/tok, loaded with the unit's rx_load; one subscriber (blocking when sub_en)
//     that takes whenever sub_ready (§14 F1-F4).
`default_nettype none
`timescale 1ns / 1ps
`include "trw_defs.vh"

module tb_pin #(
    parameter FULL = 0
) (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        live,
    input  wire        we,
    input  wire [4:0]  waddr,
    input  wire [15:0] wdata,
    input  wire [23:0] pads_ext,
    input  wire        tx_avail,
    input  wire [1:0]  tx_tag,
    input  wire [15:0] tx_data,
    output wire        tx_take,
    input  wire        sub_en,
    input  wire        sub_ready,
    output reg         p_valid,
    output reg         p_seq,
    output reg  [17:0] p_tok,
    output wire        rx_ld,        // loaded at this edge
    output wire [17:0] rx_tok,
    output wire        a_out,
    output wire        a_oe,
    output wire        n_out,
    output wire        n_oe,
    output wire        late,
    output wire        overrun,
    input  wire        clr_late,
    input  wire        clr_overrun,
    output wire [23:0] line
);
    initial begin
        $dumpfile("tb_pin.fst");
        $dumpvars(0, tb_pin);
    end

    wire [`TRW_PC_BITS-1:0] cfg;
    wire restart;
    trw_pin_cfg #(.FULL (FULL)) u_cfg (
        .clk (clk), .rst_n (rst_n), .we (we), .waddr (waddr), .wdata (wdata), .cfg (cfg), .restart (restart)
    );

    wire [4:0] pin_a = cfg[`TRW_PC_PIN_A_MSB:`TRW_PC_PIN_A_LSB];
    wire [4:0] pin_n = cfg[`TRW_PC_PIN_N_MSB:`TRW_PC_PIN_N_LSB];
    genvar p;
    generate
        for (p = 0; p < 24; p = p + 1) begin : g_pad
            wire da = (p >= 8) && (pin_a == p) && (a_oe || (p < 16));   // ui pads are input-only
            wire dn = (p >= 8) && (pin_n == p) && (n_oe || (p < 16));
            assign line[p] = da ? a_out : dn ? n_out : pads_ext[p];
        end
    endgenerate
    reg [23:0] s1, s2;
    always @(posedge clk) begin
        s1 <= line;
        s2 <= s1;
    end
    wire [23:0] pads = {s2[23:16], line[15:8], s2[7:0]};

    reg  last_seq;
    wire all_taken = !sub_en || (last_seq == p_seq);
    wire free = !p_valid || all_taken;
    wire sub_take = sub_en && sub_ready && p_valid && (last_seq != p_seq);
    wire [1:0]  rtag;
    wire [15:0] rdata;
    wire        rload;
    assign rx_ld  = rload;
    assign rx_tok = {rtag, rdata};
    always @(posedge clk) begin
        if (!rst_n) begin
            p_valid <= 1'b0; p_seq <= 1'b0; p_tok <= 18'd0; last_seq <= 1'b0;
        end else begin
            if (sub_take) last_seq <= p_seq;
            if (rload) begin
                p_valid <= 1'b1; p_seq <= !p_seq; p_tok <= {rtag, rdata};
            end
        end
    end

    trw_pin_unit #(.FULL (FULL)) u_unit (
        .clk (clk), .rst_n (rst_n), .restart (restart), .live (live), .cfg (cfg), .pads (pads),
        .tx_avail (tx_avail), .tx_tag (tx_tag), .tx_data (tx_data), .tx_take (tx_take),
        .rx_free (free), .rx_load (rload), .rx_tag (rtag), .rx_data (rdata),
        .a_out (a_out), .a_oe (a_oe), .n_out (n_out), .n_oe (n_oe),
        .late (late), .overrun (overrun), .clr_late (clr_late), .clr_overrun (clr_overrun)
    );
endmodule
