// Cell library for synthesis (synth_fabulous -extra-plib): the WARP hard primitives as the BELs
// the fabric has (bel.v2.txt), kept as black-box cells that nextpnr places on the BELs of the
// same type. Behaviour: arch/prims/*.v (ARCHITECTURE §8).
(* blackbox, keep *)
module wp_timer #(
    parameter RELOAD0 = 1'b0, parameter RELOAD1 = 1'b0, parameter RELOAD2 = 1'b0,
    parameter RELOAD3 = 1'b0, parameter RELOAD4 = 1'b0, parameter RELOAD5 = 1'b0,
    parameter RELOAD6 = 1'b0, parameter RELOAD7 = 1'b0, parameter RELOAD8 = 1'b0,
    parameter RELOAD9 = 1'b0, parameter RELOAD10 = 1'b0, parameter RELOAD11 = 1'b0,
    parameter RELOAD12 = 1'b0, parameter RELOAD13 = 1'b0, parameter RELOAD14 = 1'b0,
    parameter RELOAD15 = 1'b0, parameter ONESHOT = 1'b0
) (
    (* clkbuf_sink *) input CLK,
    input rst, input load, input half, input en,
    output tc
);
endmodule

(* blackbox, keep *)
module wp_shift #(
    parameter LEN0 = 1'b0, parameter LEN1 = 1'b0, parameter LEN2 = 1'b0, parameter LEN3 = 1'b0,
    parameter MSB_FIRST = 1'b0
) (
    (* clkbuf_sink *) input CLK,
    input rst, input load, input step, input sin,
    input d0, input d1, input d2, input d3, input d4, input d5, input d6, input d7,
    output sout, output done,
    output q0, output q1, output q2, output q3, output q4, output q5, output q6, output q7
);
endmodule
