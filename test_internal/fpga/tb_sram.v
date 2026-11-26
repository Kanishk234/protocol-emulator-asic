`timescale 1ns/1ps
module tb_sram;
    reg clk = 0, rst_n = 1, en = 0, we = 0;
    reg [8:0] addr = 0;
    reg [15:0] wdata = 0;
    wire [15:0] asic, fpga;
    reg [15:0] expected [0:511];
    reg [15:0] read_hold;
    reg read_valid = 0;
    reg [31:0] rng = 32'h61ca6b25;
    integer checks = 0, i;
    trw_sram u_asic(clk, rst_n, en, we, addr, wdata, asic);
    trw_sram_fpga u_fpga(clk, rst_n, en, we, addr, wdata, fpga);

    task cycle;
        input reset_n, enable, write_en;
        input [8:0] address;
        input [15:0] drive;
        begin
            rst_n = reset_n;
            en = enable;
            we = write_en;
            addr = address;
            wdata = drive;
            #10;
            if (read_valid && (asic !== read_hold || fpga !== read_hold))
                $fatal(1, "Output changed before edge, addr=%0d", addr);
            if (rst_n && en) begin
                if (we)
                    expected[addr] = wdata;
                else begin
                    read_hold = expected[addr];
                    read_valid = 1;
                end
            end
            clk = 1;
            #10;
            if (read_valid) begin
                if (asic !== read_hold || fpga !== read_hold)
                    $fatal(1, "Case %0d: FPGA=%h ASIC=%h ref=%h", checks, fpga, asic, read_hold);
                checks = checks + 1;
            end
            clk = 0;
        end
    endtask

    initial begin
        cycle(0, 0, 0, 0, 0);
        for (i = 0; i < 512; i = i + 1)
            cycle(1, 1, 1, i, i ^ 16'ha63b);
        for (i = 0; i < 512; i = i + 1)
            cycle(1, 1, 0, i, 0);
        for (i = 0; i < 10000; i = i + 1) begin
            rng = rng ^ (rng << 13);
            rng = rng ^ (rng >> 17);
            rng = rng ^ (rng << 5);
            cycle(|rng[31:28], rng[26], rng[25], rng[24:16], rng[15:0]);
        end
        for (i = 0; i < 512; i = i + 1)
            cycle(1, 1, 0, i, 0);
        if (checks != 11024) $fatal(1, "Missing checks: %0d", checks);
        $display("PASS: %0d read/hold observations across all 512 addresses", checks);
        $finish;
    end
endmodule
