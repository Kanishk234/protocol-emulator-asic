 // NumberOfConfigBits: 78
module S_IO2_switch_matrix
    #(
        parameter NoConfigBits=78
    )
    (
        input  W_GBUF_FEED_END0,
        input  W_GBUF_FEED_END1,
        input  W_GBUF_FEED_END2,
        input  W_GBUF_FEED_END3,
        input  E_GBUF_END0,
        input  E_GBUF_END1,
        input  E_GBUF_END2,
        input  E_GBUF_END3,
        input  S1END0,
        input  S1END1,
        input  S1END2,
        input  S1END3,
        input  S1END4,
        input  S1END5,
        input  S1END6,
        input  S1END7,
        input  S2MID0,
        input  S2MID1,
        input  S2MID2,
        input  S2MID3,
        input  S2MID4,
        input  S2MID5,
        input  S2MID6,
        input  S2MID7,
        input  S2END0,
        input  S2END1,
        input  S2END2,
        input  S2END3,
        input  S2END4,
        input  S2END5,
        input  S2END6,
        input  S2END7,
        input  A_OUT,
        input  B_OUT,
        output  W_GBUF_FEED_BEG0,
        output  W_GBUF_FEED_BEG1,
        output  W_GBUF_FEED_BEG2,
        output  W_GBUF_FEED_BEG3,
        output  N_GBUF_BEG0,
        output  N_GBUF_BEG1,
        output  N_GBUF_BEG2,
        output  N_GBUF_BEG3,
        output  E_GBUF_BEG0,
        output  E_GBUF_BEG1,
        output  E_GBUF_BEG2,
        output  E_GBUF_BEG3,
        output  N1BEG0,
        output  N1BEG1,
        output  N1BEG2,
        output  N1BEG3,
        output  N1BEG4,
        output  N1BEG5,
        output  N1BEG6,
        output  N1BEG7,
        output  N2BEG0,
        output  N2BEG1,
        output  N2BEG2,
        output  N2BEG3,
        output  N2BEG4,
        output  N2BEG5,
        output  N2BEG6,
        output  N2BEG7,
        output  N2BEGb0,
        output  N2BEGb1,
        output  N2BEGb2,
        output  N2BEGb3,
        output  N2BEGb4,
        output  N2BEGb5,
        output  N2BEGb6,
        output  N2BEGb7,
        output  Co0,
        output  A_CLK,
        output  A_IN,
        output  A_EN,
        output  B_CLK,
        output  B_IN,
        output  B_EN,
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

wire[5-1:0] W_GBUF_FEED_BEG0_input;
wire[5-1:0] W_GBUF_FEED_BEG1_input;
wire[5-1:0] W_GBUF_FEED_BEG2_input;
wire[5-1:0] W_GBUF_FEED_BEG3_input;
wire[4-1:0] N1BEG0_input;
wire[4-1:0] N1BEG1_input;
wire[4-1:0] N1BEG2_input;
wire[4-1:0] N1BEG3_input;
wire[4-1:0] N1BEG4_input;
wire[4-1:0] N1BEG5_input;
wire[4-1:0] N1BEG6_input;
wire[4-1:0] N1BEG7_input;
wire[4-1:0] N2BEG0_input;
wire[4-1:0] N2BEG1_input;
wire[4-1:0] N2BEG2_input;
wire[4-1:0] N2BEG3_input;
wire[4-1:0] N2BEG4_input;
wire[4-1:0] N2BEG5_input;
wire[4-1:0] N2BEG6_input;
wire[4-1:0] N2BEG7_input;
wire[4-1:0] N2BEGb0_input;
wire[4-1:0] N2BEGb1_input;
wire[4-1:0] N2BEGb2_input;
wire[4-1:0] N2BEGb3_input;
wire[4-1:0] N2BEGb4_input;
wire[4-1:0] N2BEGb5_input;
wire[4-1:0] N2BEGb6_input;
wire[4-1:0] N2BEGb7_input;
wire[4-1:0] A_CLK_input;
wire[16-1:0] A_IN_input;
wire[8-1:0] A_EN_input;
wire[4-1:0] B_CLK_input;
wire[16-1:0] B_IN_input;
wire[8-1:0] B_EN_input;
 //The configuration bits (if any) are just a long shift register
 //This shift register is padded to an even number of flops/latches
 //switch matrix multiplexer W_GBUF_FEED_BEG0 MUX-5
assign W_GBUF_FEED_BEG0_input = {B_OUT,A_OUT,S2END7,S1END1,W_GBUF_FEED_END0};
cus_mux81 inst_cus_mux81_W_GBUF_FEED_BEG0 (
    .A0(W_GBUF_FEED_BEG0_input[0]),
    .A1(W_GBUF_FEED_BEG0_input[1]),
    .A2(W_GBUF_FEED_BEG0_input[2]),
    .A3(W_GBUF_FEED_BEG0_input[3]),
    .A4(W_GBUF_FEED_BEG0_input[4]),
    .A5(GND0),
    .A6(GND0),
    .A7(GND0),
    .S0(ConfigBits[0+0]),
    .S0N(ConfigBits_N[0+0]),
    .S1(ConfigBits[0+1]),
    .S1N(ConfigBits_N[0+1]),
    .S2(ConfigBits[0+2]),
    .S2N(ConfigBits_N[0+2]),
    .X(W_GBUF_FEED_BEG0)
);

 //switch matrix multiplexer W_GBUF_FEED_BEG1 MUX-5
assign W_GBUF_FEED_BEG1_input = {B_OUT,A_OUT,S2END6,S1END2,W_GBUF_FEED_END1};
cus_mux81 inst_cus_mux81_W_GBUF_FEED_BEG1 (
    .A0(W_GBUF_FEED_BEG1_input[0]),
    .A1(W_GBUF_FEED_BEG1_input[1]),
    .A2(W_GBUF_FEED_BEG1_input[2]),
    .A3(W_GBUF_FEED_BEG1_input[3]),
    .A4(W_GBUF_FEED_BEG1_input[4]),
    .A5(GND0),
    .A6(GND0),
    .A7(GND0),
    .S0(ConfigBits[3+0]),
    .S0N(ConfigBits_N[3+0]),
    .S1(ConfigBits[3+1]),
    .S1N(ConfigBits_N[3+1]),
    .S2(ConfigBits[3+2]),
    .S2N(ConfigBits_N[3+2]),
    .X(W_GBUF_FEED_BEG1)
);

 //switch matrix multiplexer W_GBUF_FEED_BEG2 MUX-5
assign W_GBUF_FEED_BEG2_input = {B_OUT,A_OUT,S2END5,S1END3,W_GBUF_FEED_END2};
cus_mux81 inst_cus_mux81_W_GBUF_FEED_BEG2 (
    .A0(W_GBUF_FEED_BEG2_input[0]),
    .A1(W_GBUF_FEED_BEG2_input[1]),
    .A2(W_GBUF_FEED_BEG2_input[2]),
    .A3(W_GBUF_FEED_BEG2_input[3]),
    .A4(W_GBUF_FEED_BEG2_input[4]),
    .A5(GND0),
    .A6(GND0),
    .A7(GND0),
    .S0(ConfigBits[6+0]),
    .S0N(ConfigBits_N[6+0]),
    .S1(ConfigBits[6+1]),
    .S1N(ConfigBits_N[6+1]),
    .S2(ConfigBits[6+2]),
    .S2N(ConfigBits_N[6+2]),
    .X(W_GBUF_FEED_BEG2)
);

 //switch matrix multiplexer W_GBUF_FEED_BEG3 MUX-5
assign W_GBUF_FEED_BEG3_input = {B_OUT,A_OUT,S2END4,S1END0,W_GBUF_FEED_END3};
cus_mux81 inst_cus_mux81_W_GBUF_FEED_BEG3 (
    .A0(W_GBUF_FEED_BEG3_input[0]),
    .A1(W_GBUF_FEED_BEG3_input[1]),
    .A2(W_GBUF_FEED_BEG3_input[2]),
    .A3(W_GBUF_FEED_BEG3_input[3]),
    .A4(W_GBUF_FEED_BEG3_input[4]),
    .A5(GND0),
    .A6(GND0),
    .A7(GND0),
    .S0(ConfigBits[9+0]),
    .S0N(ConfigBits_N[9+0]),
    .S1(ConfigBits[9+1]),
    .S1N(ConfigBits_N[9+1]),
    .S2(ConfigBits[9+2]),
    .S2N(ConfigBits_N[9+2]),
    .X(W_GBUF_FEED_BEG3)
);

 //switch matrix multiplexer N_GBUF_BEG0 MUX-1
assign N_GBUF_BEG0 = E_GBUF_END0;

 //switch matrix multiplexer N_GBUF_BEG1 MUX-1
assign N_GBUF_BEG1 = E_GBUF_END1;

 //switch matrix multiplexer N_GBUF_BEG2 MUX-1
assign N_GBUF_BEG2 = E_GBUF_END2;

 //switch matrix multiplexer N_GBUF_BEG3 MUX-1
assign N_GBUF_BEG3 = E_GBUF_END3;

 //switch matrix multiplexer E_GBUF_BEG0 MUX-1
assign E_GBUF_BEG0 = E_GBUF_END0;

 //switch matrix multiplexer E_GBUF_BEG1 MUX-1
assign E_GBUF_BEG1 = E_GBUF_END1;

 //switch matrix multiplexer E_GBUF_BEG2 MUX-1
assign E_GBUF_BEG2 = E_GBUF_END2;

 //switch matrix multiplexer E_GBUF_BEG3 MUX-1
assign E_GBUF_BEG3 = E_GBUF_END3;

 //switch matrix multiplexer N1BEG0 MUX-4
assign N1BEG0_input = {A_OUT,S2END7,S2MID7,S1END7};
cus_mux41 inst_cus_mux41_N1BEG0 (
    .A0(N1BEG0_input[0]),
    .A1(N1BEG0_input[1]),
    .A2(N1BEG0_input[2]),
    .A3(N1BEG0_input[3]),
    .S0(ConfigBits[12+0]),
    .S0N(ConfigBits_N[12+0]),
    .S1(ConfigBits[12+1]),
    .S1N(ConfigBits_N[12+1]),
    .X(N1BEG0)
);

 //switch matrix multiplexer N1BEG1 MUX-4
assign N1BEG1_input = {B_OUT,S2END6,S2MID6,S1END6};
cus_mux41 inst_cus_mux41_N1BEG1 (
    .A0(N1BEG1_input[0]),
    .A1(N1BEG1_input[1]),
    .A2(N1BEG1_input[2]),
    .A3(N1BEG1_input[3]),
    .S0(ConfigBits[14+0]),
    .S0N(ConfigBits_N[14+0]),
    .S1(ConfigBits[14+1]),
    .S1N(ConfigBits_N[14+1]),
    .X(N1BEG1)
);

 //switch matrix multiplexer N1BEG2 MUX-4
assign N1BEG2_input = {A_OUT,S2END5,S2MID5,S1END5};
cus_mux41 inst_cus_mux41_N1BEG2 (
    .A0(N1BEG2_input[0]),
    .A1(N1BEG2_input[1]),
    .A2(N1BEG2_input[2]),
    .A3(N1BEG2_input[3]),
    .S0(ConfigBits[16+0]),
    .S0N(ConfigBits_N[16+0]),
    .S1(ConfigBits[16+1]),
    .S1N(ConfigBits_N[16+1]),
    .X(N1BEG2)
);

 //switch matrix multiplexer N1BEG3 MUX-4
assign N1BEG3_input = {B_OUT,S2END4,S2MID4,S1END4};
cus_mux41 inst_cus_mux41_N1BEG3 (
    .A0(N1BEG3_input[0]),
    .A1(N1BEG3_input[1]),
    .A2(N1BEG3_input[2]),
    .A3(N1BEG3_input[3]),
    .S0(ConfigBits[18+0]),
    .S0N(ConfigBits_N[18+0]),
    .S1(ConfigBits[18+1]),
    .S1N(ConfigBits_N[18+1]),
    .X(N1BEG3)
);

 //switch matrix multiplexer N1BEG4 MUX-4
assign N1BEG4_input = {A_OUT,S2END3,S2MID3,S1END3};
cus_mux41 inst_cus_mux41_N1BEG4 (
    .A0(N1BEG4_input[0]),
    .A1(N1BEG4_input[1]),
    .A2(N1BEG4_input[2]),
    .A3(N1BEG4_input[3]),
    .S0(ConfigBits[20+0]),
    .S0N(ConfigBits_N[20+0]),
    .S1(ConfigBits[20+1]),
    .S1N(ConfigBits_N[20+1]),
    .X(N1BEG4)
);

 //switch matrix multiplexer N1BEG5 MUX-4
assign N1BEG5_input = {B_OUT,S2END2,S2MID2,S1END2};
cus_mux41 inst_cus_mux41_N1BEG5 (
    .A0(N1BEG5_input[0]),
    .A1(N1BEG5_input[1]),
    .A2(N1BEG5_input[2]),
    .A3(N1BEG5_input[3]),
    .S0(ConfigBits[22+0]),
    .S0N(ConfigBits_N[22+0]),
    .S1(ConfigBits[22+1]),
    .S1N(ConfigBits_N[22+1]),
    .X(N1BEG5)
);

 //switch matrix multiplexer N1BEG6 MUX-4
assign N1BEG6_input = {A_OUT,S2END1,S2MID1,S1END1};
cus_mux41 inst_cus_mux41_N1BEG6 (
    .A0(N1BEG6_input[0]),
    .A1(N1BEG6_input[1]),
    .A2(N1BEG6_input[2]),
    .A3(N1BEG6_input[3]),
    .S0(ConfigBits[24+0]),
    .S0N(ConfigBits_N[24+0]),
    .S1(ConfigBits[24+1]),
    .S1N(ConfigBits_N[24+1]),
    .X(N1BEG6)
);

 //switch matrix multiplexer N1BEG7 MUX-4
assign N1BEG7_input = {B_OUT,S2END0,S2MID0,S1END0};
cus_mux41 inst_cus_mux41_N1BEG7 (
    .A0(N1BEG7_input[0]),
    .A1(N1BEG7_input[1]),
    .A2(N1BEG7_input[2]),
    .A3(N1BEG7_input[3]),
    .S0(ConfigBits[26+0]),
    .S0N(ConfigBits_N[26+0]),
    .S1(ConfigBits[26+1]),
    .S1N(ConfigBits_N[26+1]),
    .X(N1BEG7)
);

 //switch matrix multiplexer N2BEG0 MUX-4
assign N2BEG0_input = {A_OUT,S2END7,S2MID7,S1END7};
cus_mux41 inst_cus_mux41_N2BEG0 (
    .A0(N2BEG0_input[0]),
    .A1(N2BEG0_input[1]),
    .A2(N2BEG0_input[2]),
    .A3(N2BEG0_input[3]),
    .S0(ConfigBits[28+0]),
    .S0N(ConfigBits_N[28+0]),
    .S1(ConfigBits[28+1]),
    .S1N(ConfigBits_N[28+1]),
    .X(N2BEG0)
);

 //switch matrix multiplexer N2BEG1 MUX-4
assign N2BEG1_input = {B_OUT,S2END6,S2MID6,S1END6};
cus_mux41 inst_cus_mux41_N2BEG1 (
    .A0(N2BEG1_input[0]),
    .A1(N2BEG1_input[1]),
    .A2(N2BEG1_input[2]),
    .A3(N2BEG1_input[3]),
    .S0(ConfigBits[30+0]),
    .S0N(ConfigBits_N[30+0]),
    .S1(ConfigBits[30+1]),
    .S1N(ConfigBits_N[30+1]),
    .X(N2BEG1)
);

 //switch matrix multiplexer N2BEG2 MUX-4
assign N2BEG2_input = {A_OUT,S2END5,S2MID5,S1END5};
cus_mux41 inst_cus_mux41_N2BEG2 (
    .A0(N2BEG2_input[0]),
    .A1(N2BEG2_input[1]),
    .A2(N2BEG2_input[2]),
    .A3(N2BEG2_input[3]),
    .S0(ConfigBits[32+0]),
    .S0N(ConfigBits_N[32+0]),
    .S1(ConfigBits[32+1]),
    .S1N(ConfigBits_N[32+1]),
    .X(N2BEG2)
);

 //switch matrix multiplexer N2BEG3 MUX-4
assign N2BEG3_input = {B_OUT,S2END4,S2MID4,S1END4};
cus_mux41 inst_cus_mux41_N2BEG3 (
    .A0(N2BEG3_input[0]),
    .A1(N2BEG3_input[1]),
    .A2(N2BEG3_input[2]),
    .A3(N2BEG3_input[3]),
    .S0(ConfigBits[34+0]),
    .S0N(ConfigBits_N[34+0]),
    .S1(ConfigBits[34+1]),
    .S1N(ConfigBits_N[34+1]),
    .X(N2BEG3)
);

 //switch matrix multiplexer N2BEG4 MUX-4
assign N2BEG4_input = {A_OUT,S2END3,S2MID3,S1END3};
cus_mux41 inst_cus_mux41_N2BEG4 (
    .A0(N2BEG4_input[0]),
    .A1(N2BEG4_input[1]),
    .A2(N2BEG4_input[2]),
    .A3(N2BEG4_input[3]),
    .S0(ConfigBits[36+0]),
    .S0N(ConfigBits_N[36+0]),
    .S1(ConfigBits[36+1]),
    .S1N(ConfigBits_N[36+1]),
    .X(N2BEG4)
);

 //switch matrix multiplexer N2BEG5 MUX-4
assign N2BEG5_input = {B_OUT,S2END2,S2MID2,S1END2};
cus_mux41 inst_cus_mux41_N2BEG5 (
    .A0(N2BEG5_input[0]),
    .A1(N2BEG5_input[1]),
    .A2(N2BEG5_input[2]),
    .A3(N2BEG5_input[3]),
    .S0(ConfigBits[38+0]),
    .S0N(ConfigBits_N[38+0]),
    .S1(ConfigBits[38+1]),
    .S1N(ConfigBits_N[38+1]),
    .X(N2BEG5)
);

 //switch matrix multiplexer N2BEG6 MUX-4
assign N2BEG6_input = {A_OUT,S2END1,S2MID1,S1END1};
cus_mux41 inst_cus_mux41_N2BEG6 (
    .A0(N2BEG6_input[0]),
    .A1(N2BEG6_input[1]),
    .A2(N2BEG6_input[2]),
    .A3(N2BEG6_input[3]),
    .S0(ConfigBits[40+0]),
    .S0N(ConfigBits_N[40+0]),
    .S1(ConfigBits[40+1]),
    .S1N(ConfigBits_N[40+1]),
    .X(N2BEG6)
);

 //switch matrix multiplexer N2BEG7 MUX-4
assign N2BEG7_input = {B_OUT,S2END0,S2MID0,S1END0};
cus_mux41 inst_cus_mux41_N2BEG7 (
    .A0(N2BEG7_input[0]),
    .A1(N2BEG7_input[1]),
    .A2(N2BEG7_input[2]),
    .A3(N2BEG7_input[3]),
    .S0(ConfigBits[42+0]),
    .S0N(ConfigBits_N[42+0]),
    .S1(ConfigBits[42+1]),
    .S1N(ConfigBits_N[42+1]),
    .X(N2BEG7)
);

 //switch matrix multiplexer N2BEGb0 MUX-4
assign N2BEGb0_input = {B_OUT,S2END7,S2MID7,S1END7};
cus_mux41 inst_cus_mux41_N2BEGb0 (
    .A0(N2BEGb0_input[0]),
    .A1(N2BEGb0_input[1]),
    .A2(N2BEGb0_input[2]),
    .A3(N2BEGb0_input[3]),
    .S0(ConfigBits[44+0]),
    .S0N(ConfigBits_N[44+0]),
    .S1(ConfigBits[44+1]),
    .S1N(ConfigBits_N[44+1]),
    .X(N2BEGb0)
);

 //switch matrix multiplexer N2BEGb1 MUX-4
assign N2BEGb1_input = {A_OUT,S2END6,S2MID6,S1END6};
cus_mux41 inst_cus_mux41_N2BEGb1 (
    .A0(N2BEGb1_input[0]),
    .A1(N2BEGb1_input[1]),
    .A2(N2BEGb1_input[2]),
    .A3(N2BEGb1_input[3]),
    .S0(ConfigBits[46+0]),
    .S0N(ConfigBits_N[46+0]),
    .S1(ConfigBits[46+1]),
    .S1N(ConfigBits_N[46+1]),
    .X(N2BEGb1)
);

 //switch matrix multiplexer N2BEGb2 MUX-4
assign N2BEGb2_input = {B_OUT,S2END5,S2MID5,S1END5};
cus_mux41 inst_cus_mux41_N2BEGb2 (
    .A0(N2BEGb2_input[0]),
    .A1(N2BEGb2_input[1]),
    .A2(N2BEGb2_input[2]),
    .A3(N2BEGb2_input[3]),
    .S0(ConfigBits[48+0]),
    .S0N(ConfigBits_N[48+0]),
    .S1(ConfigBits[48+1]),
    .S1N(ConfigBits_N[48+1]),
    .X(N2BEGb2)
);

 //switch matrix multiplexer N2BEGb3 MUX-4
assign N2BEGb3_input = {A_OUT,S2END4,S2MID4,S1END4};
cus_mux41 inst_cus_mux41_N2BEGb3 (
    .A0(N2BEGb3_input[0]),
    .A1(N2BEGb3_input[1]),
    .A2(N2BEGb3_input[2]),
    .A3(N2BEGb3_input[3]),
    .S0(ConfigBits[50+0]),
    .S0N(ConfigBits_N[50+0]),
    .S1(ConfigBits[50+1]),
    .S1N(ConfigBits_N[50+1]),
    .X(N2BEGb3)
);

 //switch matrix multiplexer N2BEGb4 MUX-4
assign N2BEGb4_input = {B_OUT,S2END3,S2MID3,S1END3};
cus_mux41 inst_cus_mux41_N2BEGb4 (
    .A0(N2BEGb4_input[0]),
    .A1(N2BEGb4_input[1]),
    .A2(N2BEGb4_input[2]),
    .A3(N2BEGb4_input[3]),
    .S0(ConfigBits[52+0]),
    .S0N(ConfigBits_N[52+0]),
    .S1(ConfigBits[52+1]),
    .S1N(ConfigBits_N[52+1]),
    .X(N2BEGb4)
);

 //switch matrix multiplexer N2BEGb5 MUX-4
assign N2BEGb5_input = {A_OUT,S2END2,S2MID2,S1END2};
cus_mux41 inst_cus_mux41_N2BEGb5 (
    .A0(N2BEGb5_input[0]),
    .A1(N2BEGb5_input[1]),
    .A2(N2BEGb5_input[2]),
    .A3(N2BEGb5_input[3]),
    .S0(ConfigBits[54+0]),
    .S0N(ConfigBits_N[54+0]),
    .S1(ConfigBits[54+1]),
    .S1N(ConfigBits_N[54+1]),
    .X(N2BEGb5)
);

 //switch matrix multiplexer N2BEGb6 MUX-4
assign N2BEGb6_input = {B_OUT,S2END1,S2MID1,S1END1};
cus_mux41 inst_cus_mux41_N2BEGb6 (
    .A0(N2BEGb6_input[0]),
    .A1(N2BEGb6_input[1]),
    .A2(N2BEGb6_input[2]),
    .A3(N2BEGb6_input[3]),
    .S0(ConfigBits[56+0]),
    .S0N(ConfigBits_N[56+0]),
    .S1(ConfigBits[56+1]),
    .S1N(ConfigBits_N[56+1]),
    .X(N2BEGb6)
);

 //switch matrix multiplexer N2BEGb7 MUX-4
assign N2BEGb7_input = {A_OUT,S2END0,S2MID0,S1END0};
cus_mux41 inst_cus_mux41_N2BEGb7 (
    .A0(N2BEGb7_input[0]),
    .A1(N2BEGb7_input[1]),
    .A2(N2BEGb7_input[2]),
    .A3(N2BEGb7_input[3]),
    .S0(ConfigBits[58+0]),
    .S0N(ConfigBits_N[58+0]),
    .S1(ConfigBits[58+1]),
    .S1N(ConfigBits_N[58+1]),
    .X(N2BEGb7)
);

 //switch matrix multiplexer Co0 MUX-1
assign Co0 = GND0;

 //switch matrix multiplexer A_CLK MUX-4
assign A_CLK_input = {E_GBUF_END3,E_GBUF_END2,E_GBUF_END1,E_GBUF_END0};
cus_mux41 inst_cus_mux41_A_CLK (
    .A0(A_CLK_input[0]),
    .A1(A_CLK_input[1]),
    .A2(A_CLK_input[2]),
    .A3(A_CLK_input[3]),
    .S0(ConfigBits[60+0]),
    .S0N(ConfigBits_N[60+0]),
    .S1(ConfigBits[60+1]),
    .S1N(ConfigBits_N[60+1]),
    .X(A_CLK)
);

 //switch matrix multiplexer A_IN MUX-16
assign A_IN_input = {VCC0,GND0,S2END7,S2END6,S2END5,S2MID2,S2MID1,S2MID0,S1END7,S1END6,S1END5,S1END4,S1END3,S1END2,S1END1,S1END0};
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
    .S0(ConfigBits[62+0]),
    .S0N(ConfigBits_N[62+0]),
    .S1(ConfigBits[62+1]),
    .S1N(ConfigBits_N[62+1]),
    .S2(ConfigBits[62+2]),
    .S2N(ConfigBits_N[62+2]),
    .S3(ConfigBits[62+3]),
    .S3N(ConfigBits_N[62+3]),
    .X(A_IN)
);

 //switch matrix multiplexer A_EN MUX-8
assign A_EN_input = {VCC0,GND0,S2END2,S2END0,S2MID7,S2MID4,S1END7,S1END3};
cus_mux81 inst_cus_mux81_A_EN (
    .A0(A_EN_input[0]),
    .A1(A_EN_input[1]),
    .A2(A_EN_input[2]),
    .A3(A_EN_input[3]),
    .A4(A_EN_input[4]),
    .A5(A_EN_input[5]),
    .A6(A_EN_input[6]),
    .A7(A_EN_input[7]),
    .S0(ConfigBits[66+0]),
    .S0N(ConfigBits_N[66+0]),
    .S1(ConfigBits[66+1]),
    .S1N(ConfigBits_N[66+1]),
    .S2(ConfigBits[66+2]),
    .S2N(ConfigBits_N[66+2]),
    .X(A_EN)
);

 //switch matrix multiplexer B_CLK MUX-4
assign B_CLK_input = {E_GBUF_END3,E_GBUF_END2,E_GBUF_END1,E_GBUF_END0};
cus_mux41 inst_cus_mux41_B_CLK (
    .A0(B_CLK_input[0]),
    .A1(B_CLK_input[1]),
    .A2(B_CLK_input[2]),
    .A3(B_CLK_input[3]),
    .S0(ConfigBits[69+0]),
    .S0N(ConfigBits_N[69+0]),
    .S1(ConfigBits[69+1]),
    .S1N(ConfigBits_N[69+1]),
    .X(B_CLK)
);

 //switch matrix multiplexer B_IN MUX-16
assign B_IN_input = {VCC0,GND0,S2END7,S2END6,S2END5,S2MID2,S2MID1,S2MID0,S1END7,S1END6,S1END5,S1END4,S1END3,S1END2,S1END1,S1END0};
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
    .S0(ConfigBits[71+0]),
    .S0N(ConfigBits_N[71+0]),
    .S1(ConfigBits[71+1]),
    .S1N(ConfigBits_N[71+1]),
    .S2(ConfigBits[71+2]),
    .S2N(ConfigBits_N[71+2]),
    .S3(ConfigBits[71+3]),
    .S3N(ConfigBits_N[71+3]),
    .X(B_IN)
);

 //switch matrix multiplexer B_EN MUX-8
assign B_EN_input = {VCC0,GND0,S2END2,S2END0,S2MID7,S2MID4,S1END7,S1END3};
cus_mux81 inst_cus_mux81_B_EN (
    .A0(B_EN_input[0]),
    .A1(B_EN_input[1]),
    .A2(B_EN_input[2]),
    .A3(B_EN_input[3]),
    .A4(B_EN_input[4]),
    .A5(B_EN_input[5]),
    .A6(B_EN_input[6]),
    .A7(B_EN_input[7]),
    .S0(ConfigBits[75+0]),
    .S0N(ConfigBits_N[75+0]),
    .S1(ConfigBits[75+1]),
    .S1N(ConfigBits_N[75+1]),
    .S2(ConfigBits[75+2]),
    .S2N(ConfigBits_N[75+2]),
    .X(B_EN)
);

endmodule