`default_nettype none
module wp_lut_miter (
    input wire [3:0] I,
    input wire [15:0] INIT,
    output wire mismatch
);
    wire gold_out, native_out;
    LUTK #(.K(4)) gold (.I(I), .INIT(INIT), .O(gold_out));
    wp_lut4_mux_tree candidate (.I(I), .INIT(INIT), .O(native_out));
    assign mismatch = gold_out ^ native_out;
endmodule
