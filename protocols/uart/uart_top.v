// UART user design (provisional user-design interface, DECISIONS D-014).
//
// Pins:      rx_i (input), tx_o (output; always driven, so tx_oe = 1).
// Host:      h_w*  host -> design: bytes to transmit.
//            h_r*  design -> host: received bytes (one-byte holding register).
//            h_status = {5'b0, overrun, ferr, tx_busy}; overrun and ferr are sticky until reset.
// Baud:      RUNTIME_DIV = 0: the divisor is the parameter DIV, fixed in the bitstream.
//            RUNTIME_DIV = 1: the divisor is a register loaded from cfg_div when cfg_we = 1.
//            Either way: clocks per bit, >= 4.
`default_nettype none

module uart_top #(
    parameter DIV         = 434,  // 115200 baud at 50 MHz
    parameter RUNTIME_DIV = 0,
    parameter DIV_W       = 16
) (
    input  wire             clk,
    input  wire             rst_n,
    // pins
    input  wire             rx_i,
    output wire             tx_o,
    output wire             tx_oe,
    // host -> design
    input  wire [7:0]       h_wdata,
    input  wire             h_wvalid,
    output wire             h_wready,
    // design -> host
    output reg  [7:0]       h_rdata,
    output reg              h_rvalid,
    input  wire             h_rready,
    output wire [7:0]       h_status,
    // runtime baud (RUNTIME_DIV = 1 only)
    input  wire [DIV_W-1:0] cfg_div,
    input  wire             cfg_we
);
    wire [DIV_W-1:0] div;

    generate
        if (RUNTIME_DIV != 0) begin : g_rt
            reg [DIV_W-1:0] div_q;
            always @(posedge clk) begin
                if (!rst_n)      div_q <= DIV;
                else if (cfg_we) div_q <= cfg_div;
            end
            assign div = div_q;
        end else begin : g_fixed
            assign div = DIV;
            wire _unused_cfg = &{cfg_div, cfg_we, 1'b0};
        end
    endgenerate

    wire tx_ready;
    uart_tx #(.DIV_W(DIV_W)) u_tx (
        .clk(clk), .rst_n(rst_n), .div(div),
        .data(h_wdata), .valid(h_wvalid), .ready(tx_ready), .tx(tx_o)
    );
    assign h_wready = tx_ready;
    assign tx_oe    = 1'b1;

    wire [7:0] rx_data;
    wire       rx_valid, rx_ferr;
    uart_rx #(.DIV_W(DIV_W)) u_rx (
        .clk(clk), .rst_n(rst_n), .div(div), .rx(rx_i),
        .data(rx_data), .valid(rx_valid), .ferr(rx_ferr)
    );

    reg ferr_q, overrun_q;
    always @(posedge clk) begin
        if (!rst_n) begin
            h_rdata   <= 8'h00;
            h_rvalid  <= 1'b0;
            ferr_q    <= 1'b0;
            overrun_q <= 1'b0;
        end else begin
            if (h_rvalid && h_rready) h_rvalid <= 1'b0;
            if (rx_valid) begin
                if (h_rvalid && !h_rready) overrun_q <= 1'b1;  // previous byte not taken: drop the new one
                else begin
                    h_rdata  <= rx_data;
                    h_rvalid <= 1'b1;
                end
                if (rx_ferr) ferr_q <= 1'b1;
            end
        end
    end

    assign h_status = {5'b0, overrun_q, ferr_q, !tx_ready};
endmodule
