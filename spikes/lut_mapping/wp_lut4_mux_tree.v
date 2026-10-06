// D-047 isolated CMOS5L LUT implementation experiment, not chip RTL.
`default_nettype none
module wp_lut4_mux_tree (
    input wire [3:0] I,
    input wire [15:0] INIT,
    output wire O
);
    wire [3:0] lower;
    sg13cmos5l_mux4_1 m0 (.A0(INIT[0]), .A1(INIT[1]), .A2(INIT[2]), .A3(INIT[3]),
                            .S0(I[0]), .S1(I[1]), .X(lower[0]));
    sg13cmos5l_mux4_1 m1 (.A0(INIT[4]), .A1(INIT[5]), .A2(INIT[6]), .A3(INIT[7]),
                            .S0(I[0]), .S1(I[1]), .X(lower[1]));
    sg13cmos5l_mux4_1 m2 (.A0(INIT[8]), .A1(INIT[9]), .A2(INIT[10]), .A3(INIT[11]),
                            .S0(I[0]), .S1(I[1]), .X(lower[2]));
    sg13cmos5l_mux4_1 m3 (.A0(INIT[12]), .A1(INIT[13]), .A2(INIT[14]), .A3(INIT[15]),
                            .S0(I[0]), .S1(I[1]), .X(lower[3]));
    sg13cmos5l_mux4_1 upper (.A0(lower[0]), .A1(lower[1]), .A2(lower[2]), .A3(lower[3]),
                               .S0(I[2]), .S1(I[3]), .X(O));
endmodule
