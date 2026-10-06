// User bitstream: UART and an independent modulo-16 rising-edge monitor.
`default_nettype none
module uart_monitor_top #(
    parameter DIV = 16
) (
    input wire clk,
    input wire rst_n,
    input wire rx_i,
    input wire event_i,
    output wire tx_o,
    input wire [7:0] h_wdata,
    input wire h_wvalid,
    output wire h_wready,
    output wire [7:0] h_rdata,
    output wire h_rvalid,
    input wire h_rready,
    output wire [7:0] h_status
);
    wire [7:0] uart_status;
    wire tx_oe;
    reg event_sample;
    reg event_previous;
    reg [3:0] event_count;
    // Sample the synchronized shell input into the fabric clock domain before
    // forming an edge enable. This adds one cycle of observation latency.
    always @(posedge clk) begin
        if (!rst_n) begin
            event_sample <= 1'b0;
            event_previous <= 1'b0;
            event_count <= 4'b0000;
        end else begin
            event_sample <= event_i;
            event_previous <= event_sample;
            if (event_sample && !event_previous)
                event_count <= event_count + 1'b1;
        end
    end
    uart_top #(.DIV(DIV), .RUNTIME_DIV(0), .PRIMS(1)) u_uart (
        .clk(clk), .rst_n(rst_n), .rx_i(rx_i), .tx_o(tx_o), .tx_oe(tx_oe),
        .h_wdata(h_wdata), .h_wvalid(h_wvalid), .h_wready(h_wready),
        .h_rdata(h_rdata), .h_rvalid(h_rvalid), .h_rready(h_rready),
        .h_status(uart_status), .cfg_div(16'b0), .cfg_we(1'b0)
    );
    assign h_status = {event_count, uart_status[3:0]};
    wire _unused = &{tx_oe, uart_status[7:4], 1'b0};
endmodule
