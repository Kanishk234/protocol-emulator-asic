`timescale 1ns/1ps
`default_nettype none
// Deliberately nonsynthesizable diagnostic fixture; never part of chip sources.
module wp_delta_watchdog_fixture;
    parameter OSCILLATE = 1;
    reg a, b, enabled;
    initial begin
        a = 0; b = 0; enabled = 0;
        #2;
        enabled = OSCILLATE;
        b = 1;
        #20;
        $finish;
    end
    always @(a) if (enabled) b = ~a;
    always @(b) if (enabled) a = b;
endmodule
