// UART plus bounded, soft event timestamp storage in the user bitstream.
`default_nettype none
module uart_capture_top #(
    parameter DIV = 16,
    parameter STAMP_BITS = 8,
    parameter STAMP_SHIFT = 0
) (
    input wire clk,
    input wire rst_n,
    input wire rx_i,
    input wire event_i,
    input wire capture_select_i,
    output wire tx_o,
    input wire [7:0] h_wdata,
    input wire h_wvalid,
    output wire h_wready,
    output wire [7:0] h_rdata,
    output wire h_rvalid,
    input wire h_rready,
    output wire [7:0] h_status
);
    wire [7:0] uart_data;
    wire uart_valid;
    wire [7:0] uart_status;
    wire tx_oe;
    reg [STAMP_BITS+STAMP_SHIFT-1:0] time_counter;
    wire [STAMP_BITS-1:0] timestamp = time_counter[STAMP_BITS+STAMP_SHIFT-1:STAMP_SHIFT];
    reg sample;
    reg previous;
    reg [STAMP_BITS-1:0] slot0;
    reg [STAMP_BITS-1:0] slot1;
    reg read_ptr;
    reg write_ptr;
    reg [1:0] count;
    reg overflow;
    wire pop = capture_select_i && h_rready && count != 0;
    wire edge_event = sample && !previous;
    wire push = edge_event && (count != 2 || pop);
    always @(posedge clk) begin
        if (!rst_n) begin
            time_counter <= 0;
            sample <= 0;
            previous <= 0;
            slot0 <= 0;
            slot1 <= 0;
            read_ptr <= 0;
            write_ptr <= 0;
            count <= 0;
            overflow <= 0;
        end else begin
            time_counter <= time_counter + 1'b1;
            sample <= event_i;
            previous <= sample;
            if (push) begin
                if (write_ptr) slot1 <= timestamp;
                else slot0 <= timestamp;
                write_ptr <= !write_ptr;
            end
            if (pop) read_ptr <= !read_ptr;
            case ({push, pop})
                2'b10: count <= count + 1'b1;
                2'b01: count <= count - 1'b1;
                default: count <= count;
            endcase
            if (edge_event && !push) overflow <= 1'b1;
        end
    end
    uart_top #(.DIV(DIV), .RUNTIME_DIV(0), .PRIMS(1)) u_uart (
        .clk(clk), .rst_n(rst_n), .rx_i(rx_i), .tx_o(tx_o), .tx_oe(tx_oe),
        .h_wdata(h_wdata), .h_wvalid(h_wvalid), .h_wready(h_wready),
        .h_rdata(uart_data), .h_rvalid(uart_valid),
        .h_rready(h_rready && !capture_select_i), .h_status(uart_status),
        .cfg_div(16'b0), .cfg_we(1'b0)
    );
    wire [7:0] capture_data = {{(8-STAMP_BITS){1'b0}}, (read_ptr ? slot1 : slot0)};
    assign h_rdata = capture_select_i ? capture_data : uart_data;
    assign h_rvalid = capture_select_i ? count != 0 : uart_valid;
    assign h_status = {overflow, count == 2, count != 0, 1'b0, uart_status[3:0]};
    wire _unused = &{tx_oe, uart_status[7:4], 1'b0};
endmodule
