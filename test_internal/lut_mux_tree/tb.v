`timescale 1ns/1ps
`default_nettype none
module tb;
    reg [3:0] index;
    reg [15:0] truth;
    wire out;
    integer pattern, partial, digit, value, tested;
    reg expected, seen_zero, seen_one;
    reg compatible;
    integer candidate, bit_index;
    wp_lut4_mux_tree dut (.I(index), .INIT(truth), .O(out));
    // Independent truth-table specification: try every binary index compatible
    // with the known input bits. No decomposition into the candidate mux tree.
    initial begin
        tested = 0;
        for (pattern = 0; pattern < 36; pattern = pattern + 1) begin
            if (pattern == 0) truth = 16'h0000;
            else if (pattern == 1) truth = 16'hffff;
            else if (pattern < 18) truth = 16'h0001 << (pattern - 2);
            else if (pattern < 34) truth = ~(16'h0001 << (pattern - 18));
            else if (pattern == 34) truth = 16'haaaa;
            else truth = 16'hcccc;
            for (partial = 0; partial < 81; partial = partial + 1) begin
                value = partial;
                for (digit = 0; digit < 4; digit = digit + 1) begin
                    case (value % 3)
                        0: index[digit] = 1'b0;
                        1: index[digit] = 1'b1;
                        2: index[digit] = 1'bx;
                    endcase
                    value = value / 3;
                end
                seen_zero = 1'b0;
                seen_one = 1'b0;
                for (candidate = 0; candidate < 16; candidate = candidate + 1) begin
                    compatible = 1'b1;
                    for (bit_index = 0; bit_index < 4; bit_index = bit_index + 1) begin
                        if ((index[bit_index] === 1'b0 && ((candidate >> bit_index) & 1) != 0) ||
                            (index[bit_index] === 1'b1 && ((candidate >> bit_index) & 1) != 1))
                            compatible = 1'b0;
                    end
                    if (compatible) begin
                        if (truth[candidate]) seen_one = 1'b1;
                        else seen_zero = 1'b1;
                    end
                end
                expected = seen_zero && seen_one ? 1'bx : seen_one;
                #1;
                if (out !== expected) begin
                    $display("FAIL INIT=%h I=%b expected=%b actual=%b", truth, index, expected, out);
                    $fatal(1);
                end
                tested = tested + 1;
            end
        end
        $display("PASS %0d partial-input cases with actual pinned cell models", tested);
        $finish;
    end
endmodule
