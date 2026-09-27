`timescale 1ns/1ps
`default_nettype none
// Primitive-port check for the reference-only ANISH-D2 candidate.
module hold_cell_tb;
    reg clk = 0, hold = 1, carry = 0;
    reg [3:0] inputs = 0;
    reg [18:0] config_bits = 0;
    wire value, carry_out;
    reg [31:0] random_bits = 32'h371cb992;
    reg [3:0] address;
    reg expected;
    integer i, ones;
    LUT4c_frame_config_dffesr dut (
        .ReloadHold(hold), .UserCLK(clk), .I(inputs), .Ci(carry),
        .O(value), .Co(carry_out), .EN(1'b1), .SR(1'b1), .ConfigBits(config_bits)
    );
    initial begin
        for (i = 0; i < 256; i = i + 1) begin
            random_bits = (random_bits << 1) ^ (random_bits[31] ? 32'h04c11db7 : 32'b0);
            hold = 1; config_bits = random_bits[18:0];
            inputs = random_bits[22:19]; carry = random_bits[23];
            #1;
            if (value !== 1'b0 || carry_out !== 1'b0) $fatal(1, "Hold failed");
            clk = 1; #1; clk = 0; hold = 0; #1;
            address = inputs;
            if (config_bits[17]) address[0] = carry;
            expected = config_bits[16] ? config_bits[18] : config_bits[address];
            ones = (carry ? 1 : 0) + (inputs[1] ? 1 : 0) + (inputs[2] ? 1 : 0);
            if (value !== expected || carry_out !== (ones >= 2)) $fatal(1, "Released cell behavior changed");
        end
        hold = 1; inputs = 4'bx; carry = 1'bx; config_bits = 19'bx; #1;
        if (value !== 1'b0 || carry_out !== 1'b0) $fatal(1, "Unknown configuration escaped hold");
        $display("PASS: held/released primitive, 256 vectors plus unknown configuration");
        $finish;
    end
endmodule
`resetall
