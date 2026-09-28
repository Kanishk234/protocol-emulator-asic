 // NumberOfConfigBits: 57
module N_IO_switch_matrix
    #(
        parameter NoConfigBits=57
    )
    (
        input  N_GBUF_END0,
        input  N_GBUF_END1,
        input  N_GBUF_END2,
        input  N_GBUF_END3,
        input  N1END0,
        input  N1END1,
        input  N1END2,
        input  N1END3,
        input  N1END4,
        input  N1END5,
        input  N1END6,
        input  N1END7,
        input  N2MID0,
        input  N2MID1,
        input  N2MID2,
        input  N2MID3,
        input  N2MID4,
        input  N2MID5,
        input  N2MID6,
        input  N2MID7,
        input  N2END0,
        input  N2END1,
        input  N2END2,
        input  N2END3,
        input  N2END4,
        input  N2END5,
        input  N2END6,
        input  N2END7,
        input  Ci0,
        input  A_OUT,
        output  S1BEG0,
        output  S1BEG1,
        output  S1BEG2,
        output  S1BEG3,
        output  S1BEG4,
        output  S1BEG5,
        output  S1BEG6,
        output  S1BEG7,
        output  S2BEG0,
        output  S2BEG1,
        output  S2BEG2,
        output  S2BEG3,
        output  S2BEG4,
        output  S2BEG5,
        output  S2BEG6,
        output  S2BEG7,
        output  S2BEGb0,
        output  S2BEGb1,
        output  S2BEGb2,
        output  S2BEGb3,
        output  S2BEGb4,
        output  S2BEGb5,
        output  S2BEGb6,
        output  S2BEGb7,
        output  A_CLK,
        output  A_IN,
        output  A_EN,
 //global
        input  [NoConfigBits-1:0] ConfigBits,
        input  [NoConfigBits-1:0] ConfigBits_N
);
parameter GND0 = 1'b0;
parameter GND = 1'b0;
parameter VCC0 = 1'b1;
parameter VCC = 1'b1;
parameter VDD0 = 1'b1;
parameter VDD = 1'b1;

wire[4-1:0] S1BEG0_input;
wire[4-1:0] S1BEG1_input;
wire[4-1:0] S1BEG2_input;
wire[4-1:0] S1BEG3_input;
wire[4-1:0] S1BEG4_input;
wire[4-1:0] S1BEG5_input;
wire[4-1:0] S1BEG6_input;
wire[4-1:0] S1BEG7_input;
wire[4-1:0] S2BEG0_input;
wire[4-1:0] S2BEG1_input;
wire[4-1:0] S2BEG2_input;
wire[4-1:0] S2BEG3_input;
wire[4-1:0] S2BEG4_input;
wire[4-1:0] S2BEG5_input;
wire[4-1:0] S2BEG6_input;
wire[4-1:0] S2BEG7_input;
wire[4-1:0] S2BEGb0_input;
wire[4-1:0] S2BEGb1_input;
wire[4-1:0] S2BEGb2_input;
wire[4-1:0] S2BEGb3_input;
wire[4-1:0] S2BEGb4_input;
wire[4-1:0] S2BEGb5_input;
wire[4-1:0] S2BEGb6_input;
wire[4-1:0] S2BEGb7_input;
wire[4-1:0] A_CLK_input;
wire[16-1:0] A_IN_input;
wire[8-1:0] A_EN_input;
 //The configuration bits (if any) are just a long shift register
 //This shift register is padded to an even number of flops/latches
 //switch matrix multiplexer S1BEG0 MUX-4
assign S1BEG0_input = {A_OUT,N2END7,N2MID7,N1END7};
cus_mux41 inst_cus_mux41_S1BEG0 (
    .A0(S1BEG0_input[0]),
    .A1(S1BEG0_input[1]),
    .A2(S1BEG0_input[2]),
    .A3(S1BEG0_input[3]),
    .S0(ConfigBits[0+0]),
    .S0N(ConfigBits_N[0+0]),
    .S1(ConfigBits[0+1]),
    .S1N(ConfigBits_N[0+1]),
    .X(S1BEG0)
);

 //switch matrix multiplexer S1BEG1 MUX-4
assign S1BEG1_input = {A_OUT,N2END6,N2MID6,N1END6};
cus_mux41 inst_cus_mux41_S1BEG1 (
    .A0(S1BEG1_input[0]),
    .A1(S1BEG1_input[1]),
    .A2(S1BEG1_input[2]),
    .A3(S1BEG1_input[3]),
    .S0(ConfigBits[2+0]),
    .S0N(ConfigBits_N[2+0]),
    .S1(ConfigBits[2+1]),
    .S1N(ConfigBits_N[2+1]),
    .X(S1BEG1)
);

 //switch matrix multiplexer S1BEG2 MUX-4
assign S1BEG2_input = {A_OUT,N2END5,N2MID5,N1END5};
cus_mux41 inst_cus_mux41_S1BEG2 (
    .A0(S1BEG2_input[0]),
    .A1(S1BEG2_input[1]),
    .A2(S1BEG2_input[2]),
    .A3(S1BEG2_input[3]),
    .S0(ConfigBits[4+0]),
    .S0N(ConfigBits_N[4+0]),
    .S1(ConfigBits[4+1]),
    .S1N(ConfigBits_N[4+1]),
    .X(S1BEG2)
);

 //switch matrix multiplexer S1BEG3 MUX-4
assign S1BEG3_input = {A_OUT,N2END4,N2MID4,N1END4};
cus_mux41 inst_cus_mux41_S1BEG3 (
    .A0(S1BEG3_input[0]),
    .A1(S1BEG3_input[1]),
    .A2(S1BEG3_input[2]),
    .A3(S1BEG3_input[3]),
    .S0(ConfigBits[6+0]),
    .S0N(ConfigBits_N[6+0]),
    .S1(ConfigBits[6+1]),
    .S1N(ConfigBits_N[6+1]),
    .X(S1BEG3)
);

 //switch matrix multiplexer S1BEG4 MUX-4
assign S1BEG4_input = {A_OUT,N2END3,N2MID3,N1END3};
cus_mux41 inst_cus_mux41_S1BEG4 (
    .A0(S1BEG4_input[0]),
    .A1(S1BEG4_input[1]),
    .A2(S1BEG4_input[2]),
    .A3(S1BEG4_input[3]),
    .S0(ConfigBits[8+0]),
    .S0N(ConfigBits_N[8+0]),
    .S1(ConfigBits[8+1]),
    .S1N(ConfigBits_N[8+1]),
    .X(S1BEG4)
);

 //switch matrix multiplexer S1BEG5 MUX-4
assign S1BEG5_input = {A_OUT,N2END2,N2MID2,N1END2};
cus_mux41 inst_cus_mux41_S1BEG5 (
    .A0(S1BEG5_input[0]),
    .A1(S1BEG5_input[1]),
    .A2(S1BEG5_input[2]),
    .A3(S1BEG5_input[3]),
    .S0(ConfigBits[10+0]),
    .S0N(ConfigBits_N[10+0]),
    .S1(ConfigBits[10+1]),
    .S1N(ConfigBits_N[10+1]),
    .X(S1BEG5)
);

 //switch matrix multiplexer S1BEG6 MUX-4
assign S1BEG6_input = {A_OUT,N2END1,N2MID1,N1END1};
cus_mux41 inst_cus_mux41_S1BEG6 (
    .A0(S1BEG6_input[0]),
    .A1(S1BEG6_input[1]),
    .A2(S1BEG6_input[2]),
    .A3(S1BEG6_input[3]),
    .S0(ConfigBits[12+0]),
    .S0N(ConfigBits_N[12+0]),
    .S1(ConfigBits[12+1]),
    .S1N(ConfigBits_N[12+1]),
    .X(S1BEG6)
);

 //switch matrix multiplexer S1BEG7 MUX-4
assign S1BEG7_input = {A_OUT,N2END0,N2MID0,N1END0};
cus_mux41 inst_cus_mux41_S1BEG7 (
    .A0(S1BEG7_input[0]),
    .A1(S1BEG7_input[1]),
    .A2(S1BEG7_input[2]),
    .A3(S1BEG7_input[3]),
    .S0(ConfigBits[14+0]),
    .S0N(ConfigBits_N[14+0]),
    .S1(ConfigBits[14+1]),
    .S1N(ConfigBits_N[14+1]),
    .X(S1BEG7)
);

 //switch matrix multiplexer S2BEG0 MUX-4
assign S2BEG0_input = {A_OUT,N2END7,N2MID7,N1END7};
cus_mux41 inst_cus_mux41_S2BEG0 (
    .A0(S2BEG0_input[0]),
    .A1(S2BEG0_input[1]),
    .A2(S2BEG0_input[2]),
    .A3(S2BEG0_input[3]),
    .S0(ConfigBits[16+0]),
    .S0N(ConfigBits_N[16+0]),
    .S1(ConfigBits[16+1]),
    .S1N(ConfigBits_N[16+1]),
    .X(S2BEG0)
);

 //switch matrix multiplexer S2BEG1 MUX-4
assign S2BEG1_input = {A_OUT,N2END6,N2MID6,N1END6};
cus_mux41 inst_cus_mux41_S2BEG1 (
    .A0(S2BEG1_input[0]),
    .A1(S2BEG1_input[1]),
    .A2(S2BEG1_input[2]),
    .A3(S2BEG1_input[3]),
    .S0(ConfigBits[18+0]),
    .S0N(ConfigBits_N[18+0]),
    .S1(ConfigBits[18+1]),
    .S1N(ConfigBits_N[18+1]),
    .X(S2BEG1)
);

 //switch matrix multiplexer S2BEG2 MUX-4
assign S2BEG2_input = {A_OUT,N2END5,N2MID5,N1END5};
cus_mux41 inst_cus_mux41_S2BEG2 (
    .A0(S2BEG2_input[0]),
    .A1(S2BEG2_input[1]),
    .A2(S2BEG2_input[2]),
    .A3(S2BEG2_input[3]),
    .S0(ConfigBits[20+0]),
    .S0N(ConfigBits_N[20+0]),
    .S1(ConfigBits[20+1]),
    .S1N(ConfigBits_N[20+1]),
    .X(S2BEG2)
);

 //switch matrix multiplexer S2BEG3 MUX-4
assign S2BEG3_input = {A_OUT,N2END4,N2MID4,N1END4};
cus_mux41 inst_cus_mux41_S2BEG3 (
    .A0(S2BEG3_input[0]),
    .A1(S2BEG3_input[1]),
    .A2(S2BEG3_input[2]),
    .A3(S2BEG3_input[3]),
    .S0(ConfigBits[22+0]),
    .S0N(ConfigBits_N[22+0]),
    .S1(ConfigBits[22+1]),
    .S1N(ConfigBits_N[22+1]),
    .X(S2BEG3)
);

 //switch matrix multiplexer S2BEG4 MUX-4
assign S2BEG4_input = {A_OUT,N2END3,N2MID3,N1END3};
cus_mux41 inst_cus_mux41_S2BEG4 (
    .A0(S2BEG4_input[0]),
    .A1(S2BEG4_input[1]),
    .A2(S2BEG4_input[2]),
    .A3(S2BEG4_input[3]),
    .S0(ConfigBits[24+0]),
    .S0N(ConfigBits_N[24+0]),
    .S1(ConfigBits[24+1]),
    .S1N(ConfigBits_N[24+1]),
    .X(S2BEG4)
);

 //switch matrix multiplexer S2BEG5 MUX-4
assign S2BEG5_input = {A_OUT,N2END2,N2MID2,N1END2};
cus_mux41 inst_cus_mux41_S2BEG5 (
    .A0(S2BEG5_input[0]),
    .A1(S2BEG5_input[1]),
    .A2(S2BEG5_input[2]),
    .A3(S2BEG5_input[3]),
    .S0(ConfigBits[26+0]),
    .S0N(ConfigBits_N[26+0]),
    .S1(ConfigBits[26+1]),
    .S1N(ConfigBits_N[26+1]),
    .X(S2BEG5)
);

 //switch matrix multiplexer S2BEG6 MUX-4
assign S2BEG6_input = {A_OUT,N2END1,N2MID1,N1END1};
cus_mux41 inst_cus_mux41_S2BEG6 (
    .A0(S2BEG6_input[0]),
    .A1(S2BEG6_input[1]),
    .A2(S2BEG6_input[2]),
    .A3(S2BEG6_input[3]),
    .S0(ConfigBits[28+0]),
    .S0N(ConfigBits_N[28+0]),
    .S1(ConfigBits[28+1]),
    .S1N(ConfigBits_N[28+1]),
    .X(S2BEG6)
);

 //switch matrix multiplexer S2BEG7 MUX-4
assign S2BEG7_input = {A_OUT,N2END0,N2MID0,N1END0};
cus_mux41 inst_cus_mux41_S2BEG7 (
    .A0(S2BEG7_input[0]),
    .A1(S2BEG7_input[1]),
    .A2(S2BEG7_input[2]),
    .A3(S2BEG7_input[3]),
    .S0(ConfigBits[30+0]),
    .S0N(ConfigBits_N[30+0]),
    .S1(ConfigBits[30+1]),
    .S1N(ConfigBits_N[30+1]),
    .X(S2BEG7)
);

 //switch matrix multiplexer S2BEGb0 MUX-4
assign S2BEGb0_input = {A_OUT,N2END7,N2MID7,N1END7};
cus_mux41 inst_cus_mux41_S2BEGb0 (
    .A0(S2BEGb0_input[0]),
    .A1(S2BEGb0_input[1]),
    .A2(S2BEGb0_input[2]),
    .A3(S2BEGb0_input[3]),
    .S0(ConfigBits[32+0]),
    .S0N(ConfigBits_N[32+0]),
    .S1(ConfigBits[32+1]),
    .S1N(ConfigBits_N[32+1]),
    .X(S2BEGb0)
);

 //switch matrix multiplexer S2BEGb1 MUX-4
assign S2BEGb1_input = {A_OUT,N2END6,N2MID6,N1END6};
cus_mux41 inst_cus_mux41_S2BEGb1 (
    .A0(S2BEGb1_input[0]),
    .A1(S2BEGb1_input[1]),
    .A2(S2BEGb1_input[2]),
    .A3(S2BEGb1_input[3]),
    .S0(ConfigBits[34+0]),
    .S0N(ConfigBits_N[34+0]),
    .S1(ConfigBits[34+1]),
    .S1N(ConfigBits_N[34+1]),
    .X(S2BEGb1)
);

 //switch matrix multiplexer S2BEGb2 MUX-4
assign S2BEGb2_input = {A_OUT,N2END5,N2MID5,N1END5};
cus_mux41 inst_cus_mux41_S2BEGb2 (
    .A0(S2BEGb2_input[0]),
    .A1(S2BEGb2_input[1]),
    .A2(S2BEGb2_input[2]),
    .A3(S2BEGb2_input[3]),
    .S0(ConfigBits[36+0]),
    .S0N(ConfigBits_N[36+0]),
    .S1(ConfigBits[36+1]),
    .S1N(ConfigBits_N[36+1]),
    .X(S2BEGb2)
);

 //switch matrix multiplexer S2BEGb3 MUX-4
assign S2BEGb3_input = {A_OUT,N2END4,N2MID4,N1END4};
cus_mux41 inst_cus_mux41_S2BEGb3 (
    .A0(S2BEGb3_input[0]),
    .A1(S2BEGb3_input[1]),
    .A2(S2BEGb3_input[2]),
    .A3(S2BEGb3_input[3]),
    .S0(ConfigBits[38+0]),
    .S0N(ConfigBits_N[38+0]),
    .S1(ConfigBits[38+1]),
    .S1N(ConfigBits_N[38+1]),
    .X(S2BEGb3)
);

 //switch matrix multiplexer S2BEGb4 MUX-4
assign S2BEGb4_input = {A_OUT,N2END3,N2MID3,N1END3};
cus_mux41 inst_cus_mux41_S2BEGb4 (
    .A0(S2BEGb4_input[0]),
    .A1(S2BEGb4_input[1]),
    .A2(S2BEGb4_input[2]),
    .A3(S2BEGb4_input[3]),
    .S0(ConfigBits[40+0]),
    .S0N(ConfigBits_N[40+0]),
    .S1(ConfigBits[40+1]),
    .S1N(ConfigBits_N[40+1]),
    .X(S2BEGb4)
);

 //switch matrix multiplexer S2BEGb5 MUX-4
assign S2BEGb5_input = {A_OUT,N2END2,N2MID2,N1END2};
cus_mux41 inst_cus_mux41_S2BEGb5 (
    .A0(S2BEGb5_input[0]),
    .A1(S2BEGb5_input[1]),
    .A2(S2BEGb5_input[2]),
    .A3(S2BEGb5_input[3]),
    .S0(ConfigBits[42+0]),
    .S0N(ConfigBits_N[42+0]),
    .S1(ConfigBits[42+1]),
    .S1N(ConfigBits_N[42+1]),
    .X(S2BEGb5)
);

 //switch matrix multiplexer S2BEGb6 MUX-4
assign S2BEGb6_input = {A_OUT,N2END1,N2MID1,N1END1};
cus_mux41 inst_cus_mux41_S2BEGb6 (
    .A0(S2BEGb6_input[0]),
    .A1(S2BEGb6_input[1]),
    .A2(S2BEGb6_input[2]),
    .A3(S2BEGb6_input[3]),
    .S0(ConfigBits[44+0]),
    .S0N(ConfigBits_N[44+0]),
    .S1(ConfigBits[44+1]),
    .S1N(ConfigBits_N[44+1]),
    .X(S2BEGb6)
);

 //switch matrix multiplexer S2BEGb7 MUX-4
assign S2BEGb7_input = {A_OUT,N2END0,N2MID0,N1END0};
cus_mux41 inst_cus_mux41_S2BEGb7 (
    .A0(S2BEGb7_input[0]),
    .A1(S2BEGb7_input[1]),
    .A2(S2BEGb7_input[2]),
    .A3(S2BEGb7_input[3]),
    .S0(ConfigBits[46+0]),
    .S0N(ConfigBits_N[46+0]),
    .S1(ConfigBits[46+1]),
    .S1N(ConfigBits_N[46+1]),
    .X(S2BEGb7)
);

 //switch matrix multiplexer A_CLK MUX-4
assign A_CLK_input = {N_GBUF_END3,N_GBUF_END2,N_GBUF_END1,N_GBUF_END0};
cus_mux41 inst_cus_mux41_A_CLK (
    .A0(A_CLK_input[0]),
    .A1(A_CLK_input[1]),
    .A2(A_CLK_input[2]),
    .A3(A_CLK_input[3]),
    .S0(ConfigBits[48+0]),
    .S0N(ConfigBits_N[48+0]),
    .S1(ConfigBits[48+1]),
    .S1N(ConfigBits_N[48+1]),
    .X(A_CLK)
);

 //switch matrix multiplexer A_IN MUX-16
assign A_IN_input = {N2END7,N2END6,N2END5,N2END4,N2END3,N2END2,N2END1,N2END0,N1END7,N1END6,N1END5,N1END4,N1END3,N1END2,N1END1,N1END0};
cus_mux161 inst_cus_mux161_A_IN (
    .A0(A_IN_input[0]),
    .A1(A_IN_input[1]),
    .A2(A_IN_input[2]),
    .A3(A_IN_input[3]),
    .A4(A_IN_input[4]),
    .A5(A_IN_input[5]),
    .A6(A_IN_input[6]),
    .A7(A_IN_input[7]),
    .A8(A_IN_input[8]),
    .A9(A_IN_input[9]),
    .A10(A_IN_input[10]),
    .A11(A_IN_input[11]),
    .A12(A_IN_input[12]),
    .A13(A_IN_input[13]),
    .A14(A_IN_input[14]),
    .A15(A_IN_input[15]),
    .S0(ConfigBits[50+0]),
    .S0N(ConfigBits_N[50+0]),
    .S1(ConfigBits[50+1]),
    .S1N(ConfigBits_N[50+1]),
    .S2(ConfigBits[50+2]),
    .S2N(ConfigBits_N[50+2]),
    .S3(ConfigBits[50+3]),
    .S3N(ConfigBits_N[50+3]),
    .X(A_IN)
);

 //switch matrix multiplexer A_EN MUX-8
assign A_EN_input = {VCC0,GND0,N2END2,N2END0,N2MID7,N2MID4,N1END7,N1END3};
cus_mux81 inst_cus_mux81_A_EN (
    .A0(A_EN_input[0]),
    .A1(A_EN_input[1]),
    .A2(A_EN_input[2]),
    .A3(A_EN_input[3]),
    .A4(A_EN_input[4]),
    .A5(A_EN_input[5]),
    .A6(A_EN_input[6]),
    .A7(A_EN_input[7]),
    .S0(ConfigBits[54+0]),
    .S0N(ConfigBits_N[54+0]),
    .S1(ConfigBits[54+1]),
    .S1N(ConfigBits_N[54+1]),
    .S2(ConfigBits[54+2]),
    .S2N(ConfigBits_N[54+2]),
    .X(A_EN)
);

endmodule