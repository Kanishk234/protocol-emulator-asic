// Concurrent UART and SPI, sharing the existing byte host channel.
`default_nettype none
module uart_spi_top #(
    parameter DIV = 434,
    parameter HALF = 25,
    parameter CPOL = 0,
    parameter CPHA = 0,
    parameter UART_PRIMS = 1,
    parameter SPI_PRIMS = 0
) (
    input wire clk, input wire rst_n,
    input wire rx_i, output wire tx_o,
    input wire miso_i, output wire sck_o,
    output wire mosi_o, output wire cs_n_o,
    input wire [7:0] h_wdata, input wire h_wvalid,
    output wire h_wready,
    output wire [7:0] h_rdata, output wire h_rvalid,
    input wire h_rready, output wire [7:0] h_status
);
    reg w_payload, w_lane, w_last;
    reg r_header, r_payload, r_lane, prefer_spi;
    wire uwready, swready, urvalid, srvalid;
    wire [7:0] urdata, srdata, ustatus, sstatus;
    wire chosen = (srvalid && (!urvalid || prefer_spi));
    assign h_wready = !w_payload || (w_lane ? swready : uwready);
    assign h_rvalid = r_payload ? (r_lane ? srvalid : urvalid) : r_header;
    assign h_rdata = r_payload ? (r_lane ? srdata : urdata) : {7'b0, r_lane};
    assign h_status = {ustatus[2:0], sstatus[1:0], 3'b0};
    always @(posedge clk) begin
        if (!rst_n) begin
            w_payload <= 1'b0; w_lane <= 1'b0; w_last <= 1'b0;
            r_header <= 1'b0; r_payload <= 1'b0; r_lane <= 1'b0; prefer_spi <= 1'b0;
        end else begin
            if (h_wvalid && h_wready) begin
                w_payload <= !w_payload;
                if (!w_payload) begin
                    w_lane <= h_wdata[0]; w_last <= h_wdata[1];
                end
            end
            if (!r_header && !r_payload && (urvalid || srvalid)) begin
                r_header <= 1'b1;
                r_lane <= chosen;
            end
            if (h_rvalid && h_rready) begin
                if (!r_payload) begin
                    r_header <= 1'b0;
                    r_payload <= 1'b1;
                end else begin
                    r_payload <= 1'b0;
                    prefer_spi <= !r_lane;
                end
            end
        end
    end
    uart_top #(.DIV(DIV), .RUNTIME_DIV(0), .PRIMS(UART_PRIMS)) u_uart (
        .clk(clk), .rst_n(rst_n), .rx_i(rx_i), .tx_o(tx_o), .tx_oe(),
        .h_wdata(h_wdata), .h_wvalid(h_wvalid && w_payload && !w_lane), .h_wready(uwready),
        .h_rdata(urdata), .h_rvalid(urvalid), .h_rready(h_rready && r_payload && !r_lane),
        .h_status(ustatus), .cfg_div(16'b0), .cfg_we(1'b0)
    );
    spi_ctrl_top #(.HALF(HALF), .CPOL(CPOL), .CPHA(CPHA), .PRIMS(SPI_PRIMS)) u_spi (
        .clk(clk), .rst_n(rst_n), .miso_i(miso_i), .sck_o(sck_o),
        .mosi_o(mosi_o), .cs_n_o(cs_n_o), .out_oe(),
        .h_wdata(h_wdata), .h_wlast(w_last), .h_wvalid(h_wvalid && w_payload && w_lane),
        .h_wready(swready), .h_rdata(srdata), .h_rvalid(srvalid),
        .h_rready(h_rready && r_payload && r_lane), .h_status(sstatus)
    );
endmodule
`default_nettype wire
