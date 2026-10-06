// Measurement-only regression for cached pin selection, not synthesizable RTL.
`default_nettype none
`include "trw_defs.vh"
module tb_cached_input;
    parameter FULL = 0;
    reg clk = 0;
    always #5 clk = !clk;
    reg rst_n = 0, we = 0, idle = 0;
    reg [4:0] waddr = 0;
    reg [15:0] wdata = 0;
    reg [23:0] pads = 24'ha53c69;
    wire [`TRW_PC_BITS-1:0] cfg;
    wire [23:0] a_mask, s_mask;
    wire a_in;
    trw_pin_cfg #(.FULL(FULL), .INPUT_PREDECODE(1)) u_cfg (
        .clk(clk), .rst_n(rst_n), .we(we), .waddr(waddr), .wdata(wdata),
        .cfg(cfg), .pin_a_mask(a_mask), .pin_s_mask(s_mask), .carrier_active(), .restart()
    );
    trw_pin_io #(.INPUT_PREDECODE(1)) u_io (
        .clk(clk), .pads(pads),
        .pin_a(cfg[`TRW_PC_PIN_A_MSB:`TRW_PC_PIN_A_LSB]),
        .pin_s(cfg[`TRW_PC_PIN_S_MSB:`TRW_PC_PIN_S_LSB]),
        .pin_b(5'd31), .pin_c(5'd31), .idle(idle), .c_active(1'b0),
        .pin_a_mask(a_mask), .pin_s_mask(s_mask), .a_in(a_in), .a_prev(),
        .b_in(), .b_prev(), .c_in(), .c_prev(), .sel(), .sel_q(), .sel_fall()
    );
    task write_word;
        input [4:0] address;
        input [15:0] data;
        begin
            @(negedge clk); we = 1; waddr = address; wdata = data;
            @(posedge clk); #1;
            @(negedge clk); we = 0;
            @(posedge clk); #1;
        end
    endtask
    integer a, s;
    reg expected;
    initial begin
        repeat (2) @(negedge clk);
        rst_n = 1;
        write_word(1, 0);
        write_word(2, 0);
        for (a = 0; a < 32; a = a + 1) begin
            write_word(1, a);
            for (s = 0; s < 32; s = s + 1) begin
                write_word(2, s << 7);
                idle = (a ^ s) & 1;
                pads = pads ^ 24'h719b25;
                #1;
                expected = (s < 24) ? pads[s] : ((a < 24) ? pads[a] : idle);
                if (a_mask !== (24'd1 << a) || s_mask !== (24'd1 << s))
                    $fatal(1, "Mask mismatch at A=%0d S=%0d", a, s);
                if (a_in !== expected)
                    $fatal(1, "Input/default/priority mismatch at A=%0d S=%0d", a, s);
                // Unrelated live configuration must not corrupt selection masks.
                write_word(0, a ^ s);
                if (a_mask !== (24'd1 << a) || s_mask !== (24'd1 << s))
                    $fatal(1, "Unrelated write corrupted masks");
            end
        end
        $display("cached input: 1024 pin pairs passed; FULL=%0d", FULL);
        $finish;
    end
endmodule
