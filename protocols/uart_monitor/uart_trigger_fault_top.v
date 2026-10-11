// Autonomous bounded fault window: protocol behavior stays in user logic.
`default_nettype none
module uart_trigger_fault_top #(
    parameter DIV = 16,
    parameter integer DELAY_CYCLES = 4,
    parameter integer WINDOW_CYCLES = 4,
    parameter integer COUNTER_BITS = 4
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
    localparam [1:0] IDLE = 2'd0, WAIT_DELAY = 2'd1, ACTIVE = 2'd2;
    reg trigger_previous;
    reg [1:0] state;
    reg [COUNTER_BITS-1:0] count;
    wire trigger_edge = fault_i && !trigger_previous;
    wire invert_line = (state == ACTIVE);
    uart_fault_monitor_top #(.DIV(DIV)) u_fault (
        .clk(clk), .rst_n(rst_n), .rx_i(rx_i), .event_i(event_i),
        .fault_i(invert_line), .tx_o(tx_o), .h_wdata(h_wdata),
        .h_wvalid(h_wvalid), .h_wready(h_wready), .h_rdata(h_rdata),
        .h_rvalid(h_rvalid), .h_rready(h_rready), .h_status(h_status));
    always @(posedge clk) begin
        if (!rst_n) begin
            trigger_previous <= 1'b0;
            state <= IDLE;
            count <= {COUNTER_BITS{1'b0}};
        end else begin
            trigger_previous <= fault_i;
            case (state)
                IDLE: begin
                    if (trigger_edge) begin
                        if (DELAY_CYCLES == 0) begin
                            state <= ACTIVE;
                            count <= WINDOW_CYCLES - 1;
                        end else begin
                            state <= WAIT_DELAY;
                            count <= DELAY_CYCLES - 1;
                        end
                    end
                end
                WAIT_DELAY: begin
                    if (count == 0) begin
                        state <= ACTIVE;
                        count <= WINDOW_CYCLES - 1;
                    end else count <= count - 1'b1;
                end
                ACTIVE: begin
                    if (count == 0) state <= IDLE;
                    else count <= count - 1'b1;
                end
                default: begin
                    state <= IDLE;
                    count <= {COUNTER_BITS{1'b0}};
                end
            endcase
        end
    end
endmodule
