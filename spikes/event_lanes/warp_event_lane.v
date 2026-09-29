`default_nettype none

module warp_event_lane #(
    parameter AW = 3
) (
    input wire clk,
    input wire rst_n,
    input wire start,
    input wire [AW-1:0] start_pc,
    input wire [23:0] instruction,
    input wire [7:0] pins_in,
    input wire tx_valid,
    input wire [7:0] tx_data,
    input wire rx_ready,
    output reg [7:0] pins_out,
    output reg [7:0] pins_oe,
    output reg [7:0] sample,
    output wire tx_ready,
    output reg rx_valid,
    output wire [7:0] rx_data,
    output reg busy,
    output reg irq,
    output wire [AW-1:0] fetch_addr
);
    localparam [3:0] OP_NOP = 4'd0;
    localparam [3:0] OP_DRIVE = 4'd1;
    localparam [3:0] OP_RELEASE = 4'd2;
    localparam [3:0] OP_WAIT_PINS = 4'd3;
    localparam [3:0] OP_DELAY = 4'd4;
    localparam [3:0] OP_SAMPLE = 4'd5;
    localparam [3:0] OP_BRANCH_SAMPLE = 4'd6;
    localparam [3:0] OP_JUMP = 4'd7;
    localparam [3:0] OP_HALT = 4'd8;
    localparam [3:0] OP_SHIFT_OUT = 4'd9;
    localparam [3:0] OP_SHIFT_IN = 4'd10;
    localparam [3:0] OP_TX_SHIFT = 4'd11;

    reg [AW-1:0] pc;
    reg [15:0] delay_count;
    reg delay_active;
    reg [7:0] shift_data;
    reg [7:0] shift_mask;
    reg [3:0] shift_count;
    reg shift_active;
    reg shift_is_input;
    reg shift_msb_first;
    reg shift_to_channel;

    wire [3:0] opcode = instruction[23:20];
    wire [7:0] arg0 = instruction[19:12];
    wire [7:0] arg1 = instruction[11:4];
    wire [AW-1:0] target = instruction[AW-1:0];
    wire target_valid = (AW == 4) || !instruction[3];
    wire serial_sample = |(pins_in & shift_mask);
    wire serial_out = shift_msb_first ? shift_data[7] : shift_data[0];
    wire [7:0] shift_next_data = shift_is_input
        ? (shift_msb_first ? {shift_data[6:0], serial_sample}
                           : {serial_sample, shift_data[7:1]})
                           : (shift_msb_first ? {shift_data[6:0], 1'b0}
                           : {1'b0, shift_data[7:1]});
    assign tx_ready = busy && !delay_active && !shift_active && !rx_valid
        && (opcode == OP_TX_SHIFT);
    assign rx_data = sample;
    assign fetch_addr = pc;

    always @(posedge clk) begin
        if (!rst_n) begin
            pc <= {AW{1'b0}};
            delay_count <= 16'd0;
            delay_active <= 1'b0;
            shift_data <= 8'd0;
            shift_mask <= 8'd0;
            shift_count <= 4'd0;
            shift_active <= 1'b0;
            shift_is_input <= 1'b0;
            shift_msb_first <= 1'b0;
            shift_to_channel <= 1'b0;
            pins_out <= 8'd0;
            pins_oe <= 8'd0;
            sample <= 8'd0;
            busy <= 1'b0;
            irq <= 1'b0;
            rx_valid <= 1'b0;
        end else begin
            irq <= 1'b0;
            if (start && !busy) begin
                pc <= start_pc;
                delay_count <= 16'd0;
                delay_active <= 1'b0;
                shift_active <= 1'b0;
                shift_to_channel <= 1'b0;
                rx_valid <= 1'b0;
                busy <= 1'b1;
            end else if (busy) begin
                if (delay_active) begin
                    if (delay_count == 16'd0 || delay_count == 16'd1) begin
                        delay_count <= 16'd0;
                        delay_active <= 1'b0;
                        pc <= pc + {{(AW-1){1'b0}}, 1'b1};
                    end else begin
                        delay_count <= delay_count - 16'd1;
                    end
                end else if (rx_valid) begin
                    if (rx_ready) begin
                        rx_valid <= 1'b0;
                        pc <= pc + {{(AW-1){1'b0}}, 1'b1};
                    end
                end else if (shift_active) begin
                    if (!shift_is_input) begin
                        pins_out <= (pins_out & ~shift_mask) | (shift_mask & {8{serial_out}});
                        pins_oe <= pins_oe | shift_mask;
                    end
                    shift_data <= shift_next_data;
                    if (shift_count == 4'd1) begin
                        shift_active <= 1'b0;
                        if (shift_is_input)
                            sample <= shift_next_data;
                        if (shift_is_input && shift_to_channel)
                            rx_valid <= 1'b1;
                        else
                            pc <= pc + {{(AW-1){1'b0}}, 1'b1};
                    end else begin
                        shift_count <= shift_count - 4'd1;
                    end
                end else begin
                    case (opcode)
                        OP_NOP: pc <= pc + {{(AW-1){1'b0}}, 1'b1};
                        OP_DRIVE: begin
                            pins_out <= (pins_out & ~arg0) | (arg1 & arg0);
                            pins_oe <= pins_oe | arg0;
                            pc <= pc + {{(AW-1){1'b0}}, 1'b1};
                        end
                        OP_RELEASE: begin
                            pins_oe <= pins_oe & ~arg0;
                            pc <= pc + {{(AW-1){1'b0}}, 1'b1};
                        end
                        OP_WAIT_PINS: begin
                            if ((pins_in & arg0) == (arg1 & arg0))
                                pc <= pc + {{(AW-1){1'b0}}, 1'b1};
                        end
                        OP_DELAY: begin
                            delay_count <= {arg0, arg1};
                            delay_active <= 1'b1;
                        end
                        OP_SAMPLE: begin
                            sample <= pins_in;
                            pc <= pc + {{(AW-1){1'b0}}, 1'b1};
                        end
                        OP_BRANCH_SAMPLE: begin
                            if ((sample & arg0) == (arg1 & arg0) && target_valid)
                                pc <= target;
                            else
                                pc <= pc + {{(AW-1){1'b0}}, 1'b1};
                        end
                        OP_JUMP: begin
                            if (target_valid)
                                pc <= target;
                            else
                                pc <= pc + {{(AW-1){1'b0}}, 1'b1};
                        end
                        OP_HALT: begin
                            busy <= 1'b0;
                            irq <= 1'b1;
                        end
                        OP_SHIFT_OUT, OP_SHIFT_IN: begin
                            shift_data <= (opcode == OP_SHIFT_OUT) ? arg1 : 8'd0;
                            shift_mask <= 8'b1 << arg0[2:0];
                            shift_count <= (instruction[2:0] == 3'd0)
                                ? 4'd8 : {1'b0, instruction[2:0]};
                            shift_is_input <= (opcode == OP_SHIFT_IN);
                            shift_to_channel <= (opcode == OP_SHIFT_IN);
                            shift_msb_first <= arg0[3];
                            shift_active <= 1'b1;
                        end
                        OP_TX_SHIFT: begin
                            if (tx_valid) begin
                                shift_data <= tx_data;
                                shift_mask <= 8'b1 << arg0[2:0];
                                shift_count <= (instruction[2:0] == 3'd0)
                                    ? 4'd8 : {1'b0, instruction[2:0]};
                                shift_is_input <= 1'b0;
                                shift_to_channel <= 1'b0;
                                shift_msb_first <= arg0[3];
                                shift_active <= 1'b1;
                            end
                        end
                        default: pc <= pc + {{(AW-1){1'b0}}, 1'b1};
                    endcase
                end
            end
        end
    end
endmodule

`default_nettype wire
