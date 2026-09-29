`default_nettype none

// Area probe for an instruction image held in ordinary eFPGA configuration latches.
// The configuration-latch area is external to this module and must be added to synthesis area.
module warp_event_lanes_static #(
    parameter AW = 3
) (
    input wire clk,
    input wire rst_n,
    input wire start0,
    input wire start1,
    input wire [AW-1:0] start_pc0,
    input wire [AW-1:0] start_pc1,
    input wire [7:0] pins_in,
    input wire tx_valid0,
    input wire [7:0] tx_data0,
    input wire rx_ready0,
    input wire tx_valid1,
    input wire [7:0] tx_data1,
    input wire rx_ready1,
    input wire [24*(1<<AW)-1:0] program_image,
    output wire [7:0] pins_out0,
    output wire [7:0] pins_out1,
    output wire [7:0] pins_oe0,
    output wire [7:0] pins_oe1,
    output wire [7:0] sample0,
    output wire [7:0] sample1,
    output wire tx_ready0,
    output wire [7:0] rx_data0,
    output wire rx_valid0,
    output wire tx_ready1,
    output wire [7:0] rx_data1,
    output wire rx_valid1,
    output wire busy0,
    output wire busy1,
    output wire irq0,
    output wire irq1
);
    wire [AW-1:0] fetch_addr0;
    wire [AW-1:0] fetch_addr1;
    wire [23:0] instruction0 = program_image[(24*fetch_addr0) +: 24];
    wire [23:0] instruction1 = program_image[(24*fetch_addr1) +: 24];

    warp_event_lane #(.AW(AW)) lane0 (
        .clk(clk), .rst_n(rst_n), .start(start0), .start_pc(start_pc0),
        .instruction(instruction0), .pins_in(pins_in), .tx_valid(tx_valid0),
        .tx_data(tx_data0), .rx_ready(rx_ready0), .pins_out(pins_out0),
        .pins_oe(pins_oe0), .sample(sample0), .tx_ready(tx_ready0),
        .rx_valid(rx_valid0), .rx_data(rx_data0), .busy(busy0), .irq(irq0),
        .fetch_addr(fetch_addr0)
    );

    warp_event_lane #(.AW(AW)) lane1 (
        .clk(clk), .rst_n(rst_n), .start(start1), .start_pc(start_pc1),
        .instruction(instruction1), .pins_in(pins_in), .tx_valid(tx_valid1),
        .tx_data(tx_data1), .rx_ready(rx_ready1), .pins_out(pins_out1),
        .pins_oe(pins_oe1), .sample(sample1), .tx_ready(tx_ready1),
        .rx_valid(rx_valid1), .rx_data(rx_data1), .busy(busy1), .irq(irq1),
        .fetch_addr(fetch_addr1)
    );
endmodule

`default_nettype wire
