`timescale 1ns/1ps
`default_nettype none
// White-box diagnostic only: observes the SCC found in the frame-33 snapshot.
// Compile with reload_tb as an additional root; never forces/deposits state.
module reload_probe;
    wire result = reload_tb.dut.eFPGA_inst.Tile_X1Y8_LUT4AB.Inst_LC_LUT4c_frame_config_dffesr.inst_cus_mux161.cus_mux41_inst0.X;
    wire select_bit = reload_tb.dut.eFPGA_inst.Tile_X1Y8_LUT4AB.Inst_LC_LUT4c_frame_config_dffesr.inst_cus_mux161.cus_mux41_inst0.S1;
    wire input_a = reload_tb.dut.eFPGA_inst.Tile_X1Y8_LUT4AB.Inst_LC_LUT4c_frame_config_dffesr.inst_cus_mux161.cus_mux41_inst0.B0;
    wire input_b = reload_tb.dut.eFPGA_inst.Tile_X1Y8_LUT4AB.Inst_LC_LUT4c_frame_config_dffesr.inst_cus_mux161.cus_mux41_inst0.B1;
    time last_change = 0;
    integer changes = 0;
    always @(result) begin
        if ($time == last_change) changes = changes + 1;
        else begin last_change = $time; changes = 1; end
        if (changes == 64) begin
            $display("OSCILLATION: X1Y8 LC first LUT mux, t=%0t, 64 output transitions at same time; A=%b B=%b S=%b Y=%b", $time, input_a, input_b, select_bit, result);
            $fflush();
            $fatal(1, "White-box diagnostic: zero-time oscillation");
        end
    end
endmodule
`resetall
