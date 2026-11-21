`include "trw_defs.vh"
module pad_open_drain #(parameter FULL = 1)(input wire clk);
    (* anyseq *) reg rst_n, restart, live, idle_next, bs_mode, carrier;
    (* anyseq *) reg [`TRW_PC_BITS-1:0] cfg;
    (* anyseq *) reg [24:0] sample_delta;
    (* anyseq *) reg [23:0] pads;
    (* anyseq *) reg tx_avail, rx_free;
    (* anyseq *) reg [1:0] tx_tag;
    (* anyseq *) reg [15:0] tx_data;
    (* anyseq *) reg [19:0] pin_a, pin_n;
    (* anyseq *) reg [2:0] other_a, other_ae, other_n, other_ne;
    (* anyseq *) reg own_we;
    (* anyseq *) reg [3:0] own_waddr;
    (* anyseq *) reg [2:0] own_wdata;
    (* anyconst *) reg [3:0] pad;
    wire a, ae, n, ne;
    wire [2:0] owner;
    wire [15:0] pad_out, pad_oe;
    trw_pin_unit #(.FULL(FULL), .USE_LEVEL_CACHE(1), .USE_SAMPLE_DELTA(1),
                   .USE_BITSYNC_ACTIVE(1)) unit (
        .clk(clk), .rst_n(rst_n), .restart(restart), .live(live), .idle_next(idle_next),
        .cfg(cfg), .carrier_active(carrier), .bitsync_active(bs_mode),
        .sample_delta(sample_delta), .pads(pads), .tx_avail(tx_avail), .tx_tag(tx_tag),
        .tx_data(tx_data), .rx_free(rx_free),
        .a_out(a), .a_oe(ae), .n_out(n), .n_oe(ne),
        .clr_late(1'b0), .clr_overrun(1'b0)
    );
    trw_pins #(.NU(4)) mux (
        .clk(clk), .rst_n(rst_n), .own_we(own_we),
        .own_waddr(own_waddr), .own_wdata(own_wdata), .own_raddr(pad),
        .own_q(owner), .a_out({other_a,a}), .a_oe({other_ae,ae}),
        .n_out({other_n,n}), .n_oe({other_ne,ne}), .pin_a(pin_a), .pin_n(pin_n),
        .pad_out(pad_out), .pad_oe(pad_oe)
    );
    reg initialized = 0;
    wire selected_a = owner == 0 && pin_a[4:0] == ({1'b0,pad} + 5'd8);
    always @(posedge clk) begin
        if (!initialized) assume(!rst_n);
        initialized <= 1;
        if (initialized && cfg[`TRW_PC_OD_LSB]) begin
            if (selected_a) assert(!pad_oe[pad] || !pad_out[pad]);
            cover(selected_a && pad_oe[pad]);
        end
    end
endmodule
