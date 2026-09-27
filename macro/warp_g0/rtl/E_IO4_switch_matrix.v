 // NumberOfConfigBits: 84
module E_IO4_switch_matrix
    #(
        parameter NoConfigBits=84
    )
    (
        input  N_GBUF_END0,
        input  N_GBUF_END1,
        input  N_GBUF_END2,
        input  N_GBUF_END3,
        input  E1END0,
        input  E1END1,
        input  E1END2,
        input  E1END3,
        input  E1END4,
        input  E1END5,
        input  E1END6,
        input  E1END7,
        input  E2MID0,
        input  E2MID1,
        input  E2MID2,
        input  E2MID3,
        input  E2MID4,
        input  E2MID5,
        input  E2MID6,
        input  E2MID7,
        input  E2END0,
        input  E2END1,
        input  E2END2,
        input  E2END3,
        input  E2END4,
        input  E2END5,
        input  E2END6,
        input  E2END7,
        input  A_OUT,
        input  B_OUT,
        input  C_OUT,
        input  D_OUT,
        output  N_GBUF_BEG0,
        output  N_GBUF_BEG1,
        output  N_GBUF_BEG2,
        output  N_GBUF_BEG3,
        output  W1BEG0,
        output  W1BEG1,
        output  W1BEG2,
        output  W1BEG3,
        output  W1BEG4,
        output  W1BEG5,
        output  W1BEG6,
        output  W1BEG7,
        output  W2BEG0,
        output  W2BEG1,
        output  W2BEG2,
        output  W2BEG3,
        output  W2BEG4,
        output  W2BEG5,
        output  W2BEG6,
        output  W2BEG7,
        output  W2BEGb0,
        output  W2BEGb1,
        output  W2BEGb2,
        output  W2BEGb3,
        output  W2BEGb4,
        output  W2BEGb5,
        output  W2BEGb6,
        output  W2BEGb7,
        output  A_CLK,
        output  A_IN,
        output  A_EN,
        output  B_CLK,
        output  B_IN,
        output  B_EN,
        output  C_CLK,
        output  C_IN,
        output  C_EN,
        output  D_CLK,
        output  D_IN,
        output  D_EN,
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

wire[4-1:0] W1BEG0_input;
wire[4-1:0] W1BEG1_input;
wire[4-1:0] W1BEG2_input;
wire[4-1:0] W1BEG3_input;
wire[4-1:0] W1BEG4_input;
wire[4-1:0] W1BEG5_input;
wire[4-1:0] W1BEG6_input;
wire[4-1:0] W1BEG7_input;
wire[4-1:0] W2BEG0_input;
wire[4-1:0] W2BEG1_input;
wire[4-1:0] W2BEG2_input;
wire[4-1:0] W2BEG3_input;
wire[4-1:0] W2BEG4_input;
wire[4-1:0] W2BEG5_input;
wire[4-1:0] W2BEG6_input;
wire[4-1:0] W2BEG7_input;
wire[4-1:0] W2BEGb0_input;
wire[4-1:0] W2BEGb1_input;
wire[4-1:0] W2BEGb2_input;
wire[4-1:0] W2BEGb3_input;
wire[4-1:0] W2BEGb4_input;
wire[4-1:0] W2BEGb5_input;
wire[4-1:0] W2BEGb6_input;
wire[4-1:0] W2BEGb7_input;
wire[4-1:0] A_CLK_input;
wire[16-1:0] A_IN_input;
wire[8-1:0] A_EN_input;
wire[4-1:0] B_CLK_input;
wire[16-1:0] B_IN_input;
wire[8-1:0] B_EN_input;
wire[4-1:0] C_CLK_input;
wire[16-1:0] C_IN_input;
wire[8-1:0] C_EN_input;
wire[4-1:0] D_CLK_input;
wire[16-1:0] D_IN_input;
wire[8-1:0] D_EN_input;
 //The configuration bits (if any) are just a long shift register
 //This shift register is padded to an even number of flops/latches
 //switch matrix multiplexer N_GBUF_BEG0 MUX-1
assign N_GBUF_BEG0 = N_GBUF_END0;

 //switch matrix multiplexer N_GBUF_BEG1 MUX-1
assign N_GBUF_BEG1 = N_GBUF_END1;

 //switch matrix multiplexer N_GBUF_BEG2 MUX-1
assign N_GBUF_BEG2 = N_GBUF_END2;

 //switch matrix multiplexer N_GBUF_BEG3 MUX-1
assign N_GBUF_BEG3 = N_GBUF_END3;

 //switch matrix multiplexer W1BEG0 MUX-4
assign W1BEG0_input = {A_OUT,E2END7,E2MID7,E1END7};
cus_mux41 inst_cus_mux41_W1BEG0 (
    .A0(W1BEG0_input[0]),
    .A1(W1BEG0_input[1]),
    .A2(W1BEG0_input[2]),
    .A3(W1BEG0_input[3]),
    .S0(ConfigBits[0+0]),
    .S0N(ConfigBits_N[0+0]),
    .S1(ConfigBits[0+1]),
    .S1N(ConfigBits_N[0+1]),
    .X(W1BEG0)
);

 //switch matrix multiplexer W1BEG1 MUX-4
assign W1BEG1_input = {B_OUT,E2END6,E2MID6,E1END6};
cus_mux41 inst_cus_mux41_W1BEG1 (
    .A0(W1BEG1_input[0]),
    .A1(W1BEG1_input[1]),
    .A2(W1BEG1_input[2]),
    .A3(W1BEG1_input[3]),
    .S0(ConfigBits[2+0]),
    .S0N(ConfigBits_N[2+0]),
    .S1(ConfigBits[2+1]),
    .S1N(ConfigBits_N[2+1]),
    .X(W1BEG1)
);

 //switch matrix multiplexer W1BEG2 MUX-4
assign W1BEG2_input = {C_OUT,E2END5,E2MID5,E1END5};
cus_mux41 inst_cus_mux41_W1BEG2 (
    .A0(W1BEG2_input[0]),
    .A1(W1BEG2_input[1]),
    .A2(W1BEG2_input[2]),
    .A3(W1BEG2_input[3]),
    .S0(ConfigBits[4+0]),
    .S0N(ConfigBits_N[4+0]),
    .S1(ConfigBits[4+1]),
    .S1N(ConfigBits_N[4+1]),
    .X(W1BEG2)
);

 //switch matrix multiplexer W1BEG3 MUX-4
assign W1BEG3_input = {D_OUT,E2END4,E2MID4,E1END4};
cus_mux41 inst_cus_mux41_W1BEG3 (
    .A0(W1BEG3_input[0]),
    .A1(W1BEG3_input[1]),
    .A2(W1BEG3_input[2]),
    .A3(W1BEG3_input[3]),
    .S0(ConfigBits[6+0]),
    .S0N(ConfigBits_N[6+0]),
    .S1(ConfigBits[6+1]),
    .S1N(ConfigBits_N[6+1]),
    .X(W1BEG3)
);

 //switch matrix multiplexer W1BEG4 MUX-4
assign W1BEG4_input = {A_OUT,E2END3,E2MID3,E1END3};
cus_mux41 inst_cus_mux41_W1BEG4 (
    .A0(W1BEG4_input[0]),
    .A1(W1BEG4_input[1]),
    .A2(W1BEG4_input[2]),
    .A3(W1BEG4_input[3]),
    .S0(ConfigBits[8+0]),
    .S0N(ConfigBits_N[8+0]),
    .S1(ConfigBits[8+1]),
    .S1N(ConfigBits_N[8+1]),
    .X(W1BEG4)
);

 //switch matrix multiplexer W1BEG5 MUX-4
assign W1BEG5_input = {B_OUT,E2END2,E2MID2,E1END2};
cus_mux41 inst_cus_mux41_W1BEG5 (
    .A0(W1BEG5_input[0]),
    .A1(W1BEG5_input[1]),
    .A2(W1BEG5_input[2]),
    .A3(W1BEG5_input[3]),
    .S0(ConfigBits[10+0]),
    .S0N(ConfigBits_N[10+0]),
    .S1(ConfigBits[10+1]),
    .S1N(ConfigBits_N[10+1]),
    .X(W1BEG5)
);

 //switch matrix multiplexer W1BEG6 MUX-4
assign W1BEG6_input = {C_OUT,E2END1,E2MID1,E1END1};
cus_mux41 inst_cus_mux41_W1BEG6 (
    .A0(W1BEG6_input[0]),
    .A1(W1BEG6_input[1]),
    .A2(W1BEG6_input[2]),
    .A3(W1BEG6_input[3]),
    .S0(ConfigBits[12+0]),
    .S0N(ConfigBits_N[12+0]),
    .S1(ConfigBits[12+1]),
    .S1N(ConfigBits_N[12+1]),
    .X(W1BEG6)
);

 //switch matrix multiplexer W1BEG7 MUX-4
assign W1BEG7_input = {D_OUT,E2END0,E2MID0,E1END0};
cus_mux41 inst_cus_mux41_W1BEG7 (
    .A0(W1BEG7_input[0]),
    .A1(W1BEG7_input[1]),
    .A2(W1BEG7_input[2]),
    .A3(W1BEG7_input[3]),
    .S0(ConfigBits[14+0]),
    .S0N(ConfigBits_N[14+0]),
    .S1(ConfigBits[14+1]),
    .S1N(ConfigBits_N[14+1]),
    .X(W1BEG7)
);

 //switch matrix multiplexer W2BEG0 MUX-4
assign W2BEG0_input = {A_OUT,E2END7,E2MID7,E1END7};
cus_mux41 inst_cus_mux41_W2BEG0 (
    .A0(W2BEG0_input[0]),
    .A1(W2BEG0_input[1]),
    .A2(W2BEG0_input[2]),
    .A3(W2BEG0_input[3]),
    .S0(ConfigBits[16+0]),
    .S0N(ConfigBits_N[16+0]),
    .S1(ConfigBits[16+1]),
    .S1N(ConfigBits_N[16+1]),
    .X(W2BEG0)
);

 //switch matrix multiplexer W2BEG1 MUX-4
assign W2BEG1_input = {B_OUT,E2END6,E2MID6,E1END6};
cus_mux41 inst_cus_mux41_W2BEG1 (
    .A0(W2BEG1_input[0]),
    .A1(W2BEG1_input[1]),
    .A2(W2BEG1_input[2]),
    .A3(W2BEG1_input[3]),
    .S0(ConfigBits[18+0]),
    .S0N(ConfigBits_N[18+0]),
    .S1(ConfigBits[18+1]),
    .S1N(ConfigBits_N[18+1]),
    .X(W2BEG1)
);

 //switch matrix multiplexer W2BEG2 MUX-4
assign W2BEG2_input = {C_OUT,E2END5,E2MID5,E1END5};
cus_mux41 inst_cus_mux41_W2BEG2 (
    .A0(W2BEG2_input[0]),
    .A1(W2BEG2_input[1]),
    .A2(W2BEG2_input[2]),
    .A3(W2BEG2_input[3]),
    .S0(ConfigBits[20+0]),
    .S0N(ConfigBits_N[20+0]),
    .S1(ConfigBits[20+1]),
    .S1N(ConfigBits_N[20+1]),
    .X(W2BEG2)
);

 //switch matrix multiplexer W2BEG3 MUX-4
assign W2BEG3_input = {D_OUT,E2END4,E2MID4,E1END4};
cus_mux41 inst_cus_mux41_W2BEG3 (
    .A0(W2BEG3_input[0]),
    .A1(W2BEG3_input[1]),
    .A2(W2BEG3_input[2]),
    .A3(W2BEG3_input[3]),
    .S0(ConfigBits[22+0]),
    .S0N(ConfigBits_N[22+0]),
    .S1(ConfigBits[22+1]),
    .S1N(ConfigBits_N[22+1]),
    .X(W2BEG3)
);

 //switch matrix multiplexer W2BEG4 MUX-4
assign W2BEG4_input = {A_OUT,E2END3,E2MID3,E1END3};
cus_mux41 inst_cus_mux41_W2BEG4 (
    .A0(W2BEG4_input[0]),
    .A1(W2BEG4_input[1]),
    .A2(W2BEG4_input[2]),
    .A3(W2BEG4_input[3]),
    .S0(ConfigBits[24+0]),
    .S0N(ConfigBits_N[24+0]),
    .S1(ConfigBits[24+1]),
    .S1N(ConfigBits_N[24+1]),
    .X(W2BEG4)
);

 //switch matrix multiplexer W2BEG5 MUX-4
assign W2BEG5_input = {B_OUT,E2END2,E2MID2,E1END2};
cus_mux41 inst_cus_mux41_W2BEG5 (
    .A0(W2BEG5_input[0]),
    .A1(W2BEG5_input[1]),
    .A2(W2BEG5_input[2]),
    .A3(W2BEG5_input[3]),
    .S0(ConfigBits[26+0]),
    .S0N(ConfigBits_N[26+0]),
    .S1(ConfigBits[26+1]),
    .S1N(ConfigBits_N[26+1]),
    .X(W2BEG5)
);

 //switch matrix multiplexer W2BEG6 MUX-4
assign W2BEG6_input = {C_OUT,E2END1,E2MID1,E1END1};
cus_mux41 inst_cus_mux41_W2BEG6 (
    .A0(W2BEG6_input[0]),
    .A1(W2BEG6_input[1]),
    .A2(W2BEG6_input[2]),
    .A3(W2BEG6_input[3]),
    .S0(ConfigBits[28+0]),
    .S0N(ConfigBits_N[28+0]),
    .S1(ConfigBits[28+1]),
    .S1N(ConfigBits_N[28+1]),
    .X(W2BEG6)
);

 //switch matrix multiplexer W2BEG7 MUX-4
assign W2BEG7_input = {D_OUT,E2END0,E2MID0,E1END0};
cus_mux41 inst_cus_mux41_W2BEG7 (
    .A0(W2BEG7_input[0]),
    .A1(W2BEG7_input[1]),
    .A2(W2BEG7_input[2]),
    .A3(W2BEG7_input[3]),
    .S0(ConfigBits[30+0]),
    .S0N(ConfigBits_N[30+0]),
    .S1(ConfigBits[30+1]),
    .S1N(ConfigBits_N[30+1]),
    .X(W2BEG7)
);

 //switch matrix multiplexer W2BEGb0 MUX-4
assign W2BEGb0_input = {D_OUT,E2END7,E2MID7,E1END7};
cus_mux41 inst_cus_mux41_W2BEGb0 (
    .A0(W2BEGb0_input[0]),
    .A1(W2BEGb0_input[1]),
    .A2(W2BEGb0_input[2]),
    .A3(W2BEGb0_input[3]),
    .S0(ConfigBits[32+0]),
    .S0N(ConfigBits_N[32+0]),
    .S1(ConfigBits[32+1]),
    .S1N(ConfigBits_N[32+1]),
    .X(W2BEGb0)
);

 //switch matrix multiplexer W2BEGb1 MUX-4
assign W2BEGb1_input = {C_OUT,E2END6,E2MID6,E1END6};
cus_mux41 inst_cus_mux41_W2BEGb1 (
    .A0(W2BEGb1_input[0]),
    .A1(W2BEGb1_input[1]),
    .A2(W2BEGb1_input[2]),
    .A3(W2BEGb1_input[3]),
    .S0(ConfigBits[34+0]),
    .S0N(ConfigBits_N[34+0]),
    .S1(ConfigBits[34+1]),
    .S1N(ConfigBits_N[34+1]),
    .X(W2BEGb1)
);

 //switch matrix multiplexer W2BEGb2 MUX-4
assign W2BEGb2_input = {C_OUT,E2END5,E2MID5,E1END5};
cus_mux41 inst_cus_mux41_W2BEGb2 (
    .A0(W2BEGb2_input[0]),
    .A1(W2BEGb2_input[1]),
    .A2(W2BEGb2_input[2]),
    .A3(W2BEGb2_input[3]),
    .S0(ConfigBits[36+0]),
    .S0N(ConfigBits_N[36+0]),
    .S1(ConfigBits[36+1]),
    .S1N(ConfigBits_N[36+1]),
    .X(W2BEGb2)
);

 //switch matrix multiplexer W2BEGb3 MUX-4
assign W2BEGb3_input = {A_OUT,E2END4,E2MID4,E1END4};
cus_mux41 inst_cus_mux41_W2BEGb3 (
    .A0(W2BEGb3_input[0]),
    .A1(W2BEGb3_input[1]),
    .A2(W2BEGb3_input[2]),
    .A3(W2BEGb3_input[3]),
    .S0(ConfigBits[38+0]),
    .S0N(ConfigBits_N[38+0]),
    .S1(ConfigBits[38+1]),
    .S1N(ConfigBits_N[38+1]),
    .X(W2BEGb3)
);

 //switch matrix multiplexer W2BEGb4 MUX-4
assign W2BEGb4_input = {D_OUT,E2END3,E2MID3,E1END3};
cus_mux41 inst_cus_mux41_W2BEGb4 (
    .A0(W2BEGb4_input[0]),
    .A1(W2BEGb4_input[1]),
    .A2(W2BEGb4_input[2]),
    .A3(W2BEGb4_input[3]),
    .S0(ConfigBits[40+0]),
    .S0N(ConfigBits_N[40+0]),
    .S1(ConfigBits[40+1]),
    .S1N(ConfigBits_N[40+1]),
    .X(W2BEGb4)
);

 //switch matrix multiplexer W2BEGb5 MUX-4
assign W2BEGb5_input = {C_OUT,E2END2,E2MID2,E1END2};
cus_mux41 inst_cus_mux41_W2BEGb5 (
    .A0(W2BEGb5_input[0]),
    .A1(W2BEGb5_input[1]),
    .A2(W2BEGb5_input[2]),
    .A3(W2BEGb5_input[3]),
    .S0(ConfigBits[42+0]),
    .S0N(ConfigBits_N[42+0]),
    .S1(ConfigBits[42+1]),
    .S1N(ConfigBits_N[42+1]),
    .X(W2BEGb5)
);

 //switch matrix multiplexer W2BEGb6 MUX-4
assign W2BEGb6_input = {B_OUT,E2END1,E2MID1,E1END1};
cus_mux41 inst_cus_mux41_W2BEGb6 (
    .A0(W2BEGb6_input[0]),
    .A1(W2BEGb6_input[1]),
    .A2(W2BEGb6_input[2]),
    .A3(W2BEGb6_input[3]),
    .S0(ConfigBits[44+0]),
    .S0N(ConfigBits_N[44+0]),
    .S1(ConfigBits[44+1]),
    .S1N(ConfigBits_N[44+1]),
    .X(W2BEGb6)
);

 //switch matrix multiplexer W2BEGb7 MUX-4
assign W2BEGb7_input = {A_OUT,E2END0,E2MID0,E1END0};
cus_mux41 inst_cus_mux41_W2BEGb7 (
    .A0(W2BEGb7_input[0]),
    .A1(W2BEGb7_input[1]),
    .A2(W2BEGb7_input[2]),
    .A3(W2BEGb7_input[3]),
    .S0(ConfigBits[46+0]),
    .S0N(ConfigBits_N[46+0]),
    .S1(ConfigBits[46+1]),
    .S1N(ConfigBits_N[46+1]),
    .X(W2BEGb7)
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
assign A_IN_input = {VCC0,GND0,E2END7,E2END6,E2END5,E2MID2,E2MID1,E2MID0,E1END7,E1END6,E1END5,E1END4,E1END3,E1END2,E1END1,E1END0};
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
assign A_EN_input = {VCC0,GND0,E2END2,E2END0,E2MID7,E2MID4,E1END7,E1END3};
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

 //switch matrix multiplexer B_CLK MUX-4
assign B_CLK_input = {N_GBUF_END3,N_GBUF_END2,N_GBUF_END1,N_GBUF_END0};
cus_mux41 inst_cus_mux41_B_CLK (
    .A0(B_CLK_input[0]),
    .A1(B_CLK_input[1]),
    .A2(B_CLK_input[2]),
    .A3(B_CLK_input[3]),
    .S0(ConfigBits[57+0]),
    .S0N(ConfigBits_N[57+0]),
    .S1(ConfigBits[57+1]),
    .S1N(ConfigBits_N[57+1]),
    .X(B_CLK)
);

 //switch matrix multiplexer B_IN MUX-16
assign B_IN_input = {VCC0,GND0,E2END7,E2END6,E2END5,E2MID2,E2MID1,E2MID0,E1END7,E1END6,E1END5,E1END4,E1END3,E1END2,E1END1,E1END0};
cus_mux161 inst_cus_mux161_B_IN (
    .A0(B_IN_input[0]),
    .A1(B_IN_input[1]),
    .A2(B_IN_input[2]),
    .A3(B_IN_input[3]),
    .A4(B_IN_input[4]),
    .A5(B_IN_input[5]),
    .A6(B_IN_input[6]),
    .A7(B_IN_input[7]),
    .A8(B_IN_input[8]),
    .A9(B_IN_input[9]),
    .A10(B_IN_input[10]),
    .A11(B_IN_input[11]),
    .A12(B_IN_input[12]),
    .A13(B_IN_input[13]),
    .A14(B_IN_input[14]),
    .A15(B_IN_input[15]),
    .S0(ConfigBits[59+0]),
    .S0N(ConfigBits_N[59+0]),
    .S1(ConfigBits[59+1]),
    .S1N(ConfigBits_N[59+1]),
    .S2(ConfigBits[59+2]),
    .S2N(ConfigBits_N[59+2]),
    .S3(ConfigBits[59+3]),
    .S3N(ConfigBits_N[59+3]),
    .X(B_IN)
);

 //switch matrix multiplexer B_EN MUX-8
assign B_EN_input = {VCC0,GND0,E2END2,E2END0,E2MID7,E2MID4,E1END7,E1END3};
cus_mux81 inst_cus_mux81_B_EN (
    .A0(B_EN_input[0]),
    .A1(B_EN_input[1]),
    .A2(B_EN_input[2]),
    .A3(B_EN_input[3]),
    .A4(B_EN_input[4]),
    .A5(B_EN_input[5]),
    .A6(B_EN_input[6]),
    .A7(B_EN_input[7]),
    .S0(ConfigBits[63+0]),
    .S0N(ConfigBits_N[63+0]),
    .S1(ConfigBits[63+1]),
    .S1N(ConfigBits_N[63+1]),
    .S2(ConfigBits[63+2]),
    .S2N(ConfigBits_N[63+2]),
    .X(B_EN)
);

 //switch matrix multiplexer C_CLK MUX-4
assign C_CLK_input = {N_GBUF_END3,N_GBUF_END2,N_GBUF_END1,N_GBUF_END0};
cus_mux41 inst_cus_mux41_C_CLK (
    .A0(C_CLK_input[0]),
    .A1(C_CLK_input[1]),
    .A2(C_CLK_input[2]),
    .A3(C_CLK_input[3]),
    .S0(ConfigBits[66+0]),
    .S0N(ConfigBits_N[66+0]),
    .S1(ConfigBits[66+1]),
    .S1N(ConfigBits_N[66+1]),
    .X(C_CLK)
);

 //switch matrix multiplexer C_IN MUX-16
assign C_IN_input = {VCC0,GND0,E2END7,E2END6,E2END5,E2MID2,E2MID1,E2MID0,E1END7,E1END6,E1END5,E1END4,E1END3,E1END2,E1END1,E1END0};
cus_mux161 inst_cus_mux161_C_IN (
    .A0(C_IN_input[0]),
    .A1(C_IN_input[1]),
    .A2(C_IN_input[2]),
    .A3(C_IN_input[3]),
    .A4(C_IN_input[4]),
    .A5(C_IN_input[5]),
    .A6(C_IN_input[6]),
    .A7(C_IN_input[7]),
    .A8(C_IN_input[8]),
    .A9(C_IN_input[9]),
    .A10(C_IN_input[10]),
    .A11(C_IN_input[11]),
    .A12(C_IN_input[12]),
    .A13(C_IN_input[13]),
    .A14(C_IN_input[14]),
    .A15(C_IN_input[15]),
    .S0(ConfigBits[68+0]),
    .S0N(ConfigBits_N[68+0]),
    .S1(ConfigBits[68+1]),
    .S1N(ConfigBits_N[68+1]),
    .S2(ConfigBits[68+2]),
    .S2N(ConfigBits_N[68+2]),
    .S3(ConfigBits[68+3]),
    .S3N(ConfigBits_N[68+3]),
    .X(C_IN)
);

 //switch matrix multiplexer C_EN MUX-8
assign C_EN_input = {VCC0,GND0,E2END2,E2END0,E2MID7,E2MID4,E1END7,E1END3};
cus_mux81 inst_cus_mux81_C_EN (
    .A0(C_EN_input[0]),
    .A1(C_EN_input[1]),
    .A2(C_EN_input[2]),
    .A3(C_EN_input[3]),
    .A4(C_EN_input[4]),
    .A5(C_EN_input[5]),
    .A6(C_EN_input[6]),
    .A7(C_EN_input[7]),
    .S0(ConfigBits[72+0]),
    .S0N(ConfigBits_N[72+0]),
    .S1(ConfigBits[72+1]),
    .S1N(ConfigBits_N[72+1]),
    .S2(ConfigBits[72+2]),
    .S2N(ConfigBits_N[72+2]),
    .X(C_EN)
);

 //switch matrix multiplexer D_CLK MUX-4
assign D_CLK_input = {N_GBUF_END3,N_GBUF_END2,N_GBUF_END1,N_GBUF_END0};
cus_mux41 inst_cus_mux41_D_CLK (
    .A0(D_CLK_input[0]),
    .A1(D_CLK_input[1]),
    .A2(D_CLK_input[2]),
    .A3(D_CLK_input[3]),
    .S0(ConfigBits[75+0]),
    .S0N(ConfigBits_N[75+0]),
    .S1(ConfigBits[75+1]),
    .S1N(ConfigBits_N[75+1]),
    .X(D_CLK)
);

 //switch matrix multiplexer D_IN MUX-16
assign D_IN_input = {VCC0,GND0,E2END7,E2END6,E2END5,E2MID2,E2MID1,E2MID0,E1END7,E1END6,E1END5,E1END4,E1END3,E1END2,E1END1,E1END0};
cus_mux161 inst_cus_mux161_D_IN (
    .A0(D_IN_input[0]),
    .A1(D_IN_input[1]),
    .A2(D_IN_input[2]),
    .A3(D_IN_input[3]),
    .A4(D_IN_input[4]),
    .A5(D_IN_input[5]),
    .A6(D_IN_input[6]),
    .A7(D_IN_input[7]),
    .A8(D_IN_input[8]),
    .A9(D_IN_input[9]),
    .A10(D_IN_input[10]),
    .A11(D_IN_input[11]),
    .A12(D_IN_input[12]),
    .A13(D_IN_input[13]),
    .A14(D_IN_input[14]),
    .A15(D_IN_input[15]),
    .S0(ConfigBits[77+0]),
    .S0N(ConfigBits_N[77+0]),
    .S1(ConfigBits[77+1]),
    .S1N(ConfigBits_N[77+1]),
    .S2(ConfigBits[77+2]),
    .S2N(ConfigBits_N[77+2]),
    .S3(ConfigBits[77+3]),
    .S3N(ConfigBits_N[77+3]),
    .X(D_IN)
);

 //switch matrix multiplexer D_EN MUX-8
assign D_EN_input = {VCC0,GND0,E2END2,E2END0,E2MID7,E2MID4,E1END7,E1END3};
cus_mux81 inst_cus_mux81_D_EN (
    .A0(D_EN_input[0]),
    .A1(D_EN_input[1]),
    .A2(D_EN_input[2]),
    .A3(D_EN_input[3]),
    .A4(D_EN_input[4]),
    .A5(D_EN_input[5]),
    .A6(D_EN_input[6]),
    .A7(D_EN_input[7]),
    .S0(ConfigBits[81+0]),
    .S0N(ConfigBits_N[81+0]),
    .S1(ConfigBits[81+1]),
    .S1N(ConfigBits_N[81+1]),
    .S2(ConfigBits[81+2]),
    .S2N(ConfigBits_N[81+2]),
    .X(D_EN)
);

endmodule