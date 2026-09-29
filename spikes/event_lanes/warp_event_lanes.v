`default_nettype none

module warp_event_lanes #(
    parameter AW = 3
) (
    input wire clk,
    input wire rst_n,
    input wire start0,
    input wire start1,
    input wire [AW-1:0] start_pc0,
    input wire [AW-1:0] start_pc1,
    input wire [7:0] pins_in,
    input wire prog_we,
    input wire [AW-1:0] prog_addr,
    input wire [23:0] prog_wdata,
    output wire prog_ready,
    output wire [7:0] pins_out0,
    output wire [7:0] pins_out1,
    output wire [7:0] pins_oe0,
    output wire [7:0] pins_oe1,
    output wire [7:0] sample0,
    output wire [7:0] sample1,
    output wire busy0,
    output wire busy1,
    output wire irq0,
    output wire irq1
);
    localparam DEPTH = (1 << AW);
    reg [23:0] program_image [0:DEPTH-1];
    wire [AW-1:0] fetch_addr0;
    wire [AW-1:0] fetch_addr1;
    wire [23:0] instruction0 = program_image[fetch_addr0];
    wire [23:0] instruction1 = program_image[fetch_addr1];

    assign prog_ready = rst_n && !busy0 && !busy1;

    always @(posedge clk) begin
        if (prog_we && prog_ready)
            program_image[prog_addr] <= prog_wdata;
    end

    warp_event_lane #(.AW(AW)) lane0 (
        .clk(clk), .rst_n(rst_n), .start(start0), .start_pc(start_pc0),
        .instruction(instruction0), .pins_in(pins_in), .pins_out(pins_out0),
        .pins_oe(pins_oe0), .sample(sample0), .busy(busy0), .irq(irq0),
        .fetch_addr(fetch_addr0)
    );

    warp_event_lane #(.AW(AW)) lane1 (
        .clk(clk), .rst_n(rst_n), .start(start1), .start_pc(start_pc1),
        .instruction(instruction1), .pins_in(pins_in), .pins_out(pins_out1),
        .pins_oe(pins_oe1), .sample(sample1), .busy(busy1), .irq(irq1),
        .fetch_addr(fetch_addr1)
    );
endmodule

`default_nettype wire
