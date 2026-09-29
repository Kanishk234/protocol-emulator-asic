`timescale 1ns/1ps
`default_nettype none
module small_cold_tb;
    reg clk=0;
    always #500 clk=~clk;
    reg resetn=0, strobe=0;
    reg [31:0] data=0;
    reg [3:0] pins_in=1;
    wire [3:0] pins_out, pins_t;
    wire [7:0] cfg_a, cfg_b;
    wire active, led;
    eFPGA_top dut(.CLK(clk), .resetn(resetn),
        .SelfWriteStrobe(strobe), .SelfWriteData(data),
        .O_top(pins_in), .I_top(pins_out), .T_top(pins_t),
        .A_config_C(cfg_a), .B_config_C(cfg_b),
        .Rx(1'b1), .s_clk(1'b0), .s_data(1'b0),
        .ComActive(active), .ReceiveLED(led));
    reg [31:0] words[0:125];
    reg [1:0] expected=0;
    reg [31:0] rng=32'h1248abcd;
    integer i, checks=0;
    string image_path;
    task tick(input reg rst, input reg en);
        reg [1:0] observed_expected;
        begin
            @(negedge clk); pins_in={2'b00,en,rst};
            if (rst) expected=0;
            else if (en) expected=expected+1'b1;
            @(posedge clk); #100;
            observed_expected=expected;
            if ($test$plusargs("wrong_expected")) observed_expected=expected^2'b01;
            if (pins_t !== 4'b1100 || pins_out[3:2] !== observed_expected)
                $fatal(1,"FAIL: pin oracle check=%0d output=%b oe=%b expected=%b",checks,pins_out,pins_t,observed_expected);
            checks=checks+1;
        end
    endtask
    initial begin
        if (!$value$plusargs("image=%s",image_path)) $fatal(1,"missing image");
        $readmemh(image_path,words);
        repeat(4) @(negedge clk);
        resetn=1;
        repeat(20) @(negedge clk);
        for(i=0;i<126;i=i+1) begin
            data=words[i]; strobe=1;
            @(negedge clk); strobe=0;
            repeat(3) @(negedge clk);
        end
        repeat(20) @(negedge clk);
        tick(1,0); tick(1,1);
        repeat(32) tick(0,1);
        repeat(16) tick(0,0);
        for(i=0;i<1024;i=i+1) begin
            rng=rng^(rng<<13); rng=rng^(rng>>17); rng=rng^(rng<<5);
            tick(rng[4:0]==0,rng[7]);
        end
        $display("PASS: small cold-load counter %0d pin checks",checks);
        $finish;
    end
    initial begin #100000000; $fatal(1,"FAIL: watchdog"); end
endmodule
`default_nettype wire
