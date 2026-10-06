// User-programmable UART fault injection beside independent event monitoring.
`default_nettype none
module uart_fault_monitor_top #(
    parameter DIV = 16
) (
    input wire clk,
    input wire rst_n,
    input wire rx_i,
    input wire event_i,
    input wire fault_i,
    output wire tx_o,
    input wire [7:0] h_wdata,
    input wire h_wvalid,
    output wire h_wready,
    output wire [7:0] h_rdata,
    output wire h_rvalid,
    input wire h_rready,
    output wire [7:0] h_status
);
    wire uart_tx;
    uart_monitor_top #(.DIV(DIV)) u_monitor (
        .clk(clk), .rst_n(rst_n), .rx_i(rx_i), .event_i(event_i),
        .tx_o(uart_tx), .h_wdata(h_wdata), .h_wvalid(h_wvalid),
        .h_wready(h_wready), .h_rdata(h_rdata), .h_rvalid(h_rvalid),
        .h_rready(h_rready), .h_status(h_status)
    );
    // External synchronized control inverts the transmitted line. A timed
    // pulse can corrupt selected data/stop bits; high while idle forces low.
    assign tx_o = uart_tx ^ fault_i;
endmodule
