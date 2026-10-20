// Concurrent UART and I2C, sharing the existing byte host channel.
`default_nettype none
module uart_i2c_top #(
    parameter DIV = 434,
    parameter Q = 125,
    parameter UART_PRIMS = 1,
    parameter I2C_PRIMS = 0
) (
    input wire clk, input wire rst_n,
    input wire rx_i, output wire tx_o,
    input wire sda_i, input wire scl_i,
    output wire sda_oe, output wire scl_oe,
    input wire [7:0] h_wdata, input wire h_wvalid,
    output wire h_wready,
    output wire [7:0] h_rdata, output wire h_rvalid,
    input wire h_rready, output wire [7:0] h_status
);
    reg w_payload, w_lane, w_last;
    reg r_header, r_payload, r_lane, prefer_i2c;
    wire uwready, swready, urvalid, srvalid;
    wire [7:0] urdata, srdata, ustatus, sstatus;
    wire chosen = (srvalid && (!urvalid || prefer_i2c));
    assign h_wready = !w_payload || (w_lane ? swready : uwready);
    assign h_rvalid = r_payload ? (r_lane ? srvalid : urvalid) : r_header;
    assign h_rdata = r_payload ? (r_lane ? srdata : urdata) : {7'b0, r_lane};
    assign h_status = {ustatus[2:0], 1'b0, sstatus[3:0]};
    always @(posedge clk) begin
        if (!rst_n) begin
            w_payload <= 1'b0; w_lane <= 1'b0; w_last <= 1'b0;
            r_header <= 1'b0; r_payload <= 1'b0; r_lane <= 1'b0; prefer_i2c <= 1'b0;
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
                    prefer_i2c <= !r_lane;
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
    i2c_ctrl_top #(.Q(Q), .PRIMS(I2C_PRIMS)) u_i2c (
        .clk(clk), .rst_n(rst_n), .sda_i(sda_i), .scl_i(scl_i),
        .sda_oe(sda_oe), .scl_oe(scl_oe), .out_o(),
        .h_wdata(h_wdata), .h_wlast(w_last), .h_wvalid(h_wvalid && w_payload && w_lane),
        .h_wready(swready), .h_rdata(srdata), .h_rvalid(srvalid),
        .h_rready(h_rready && r_payload && r_lane), .h_status(sstatus)
    );
endmodule
`default_nettype wire
