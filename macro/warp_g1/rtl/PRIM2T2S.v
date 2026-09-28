module PRIM2T2S
    #(
`ifdef EMULATION
        parameter [639:0] Emulate_Bitstream=640'b0,
`endif
        parameter MaxFramesPerCol=20,
        parameter FrameBitsPerRow=32,
        parameter NoConfigBits=430
    )
    (
 //N
        output  [3:0] N_GBUF_BEG,        //Port(Name=N_GBUF_BEG,IO=OUTPUT,XOffset=0,YOffset=-1,WireCount=4,Side=N)
        output  [7:0] N1BEG,        //Port(Name=N1BEG,IO=OUTPUT,XOffset=0,YOffset=-1,WireCount=8,Side=N)
        output  [7:0] N2BEG,        //Port(Name=N2BEG,IO=OUTPUT,XOffset=0,YOffset=-1,WireCount=8,Side=N)
        output  [7:0] N2BEGb,        //Port(Name=N2BEGb,IO=OUTPUT,XOffset=0,YOffset=-1,WireCount=8,Side=N)
        input  [7:0] S1END,        //Port(Name=S1END,IO=INPUT,XOffset=0,YOffset=1,WireCount=8,Side=N)
        input  [7:0] S2MID,        //Port(Name=S2MID,IO=INPUT,XOffset=0,YOffset=1,WireCount=8,Side=N)
        input  [7:0] S2END,        //Port(Name=S2END,IO=INPUT,XOffset=0,YOffset=1,WireCount=8,Side=N)
        output  [0:0] CO,        //Port(Name=CO,IO=OUTPUT,XOffset=0,YOffset=-1,WireCount=1,Side=N)
 //E
        output  [7:0] E1BEG,        //Port(Name=E1BEG,IO=OUTPUT,XOffset=1,YOffset=0,WireCount=8,Side=E)
        output  [7:0] E2BEG,        //Port(Name=E2BEG,IO=OUTPUT,XOffset=1,YOffset=0,WireCount=8,Side=E)
        output  [7:0] E2BEGb,        //Port(Name=E2BEGb,IO=OUTPUT,XOffset=1,YOffset=0,WireCount=8,Side=E)
        input  [7:0] W1END,        //Port(Name=W1END,IO=INPUT,XOffset=-1,YOffset=0,WireCount=8,Side=E)
        input  [7:0] W2MID,        //Port(Name=W2MID,IO=INPUT,XOffset=-1,YOffset=0,WireCount=8,Side=E)
        input  [7:0] W2END,        //Port(Name=W2END,IO=INPUT,XOffset=-1,YOffset=0,WireCount=8,Side=E)
 //W
        input  [7:0] E1END,        //Port(Name=E1END,IO=INPUT,XOffset=1,YOffset=0,WireCount=8,Side=W)
        input  [7:0] E2MID,        //Port(Name=E2MID,IO=INPUT,XOffset=1,YOffset=0,WireCount=8,Side=W)
        input  [7:0] E2END,        //Port(Name=E2END,IO=INPUT,XOffset=1,YOffset=0,WireCount=8,Side=W)
        output  [7:0] W1BEG,        //Port(Name=W1BEG,IO=OUTPUT,XOffset=-1,YOffset=0,WireCount=8,Side=W)
        output  [7:0] W2BEG,        //Port(Name=W2BEG,IO=OUTPUT,XOffset=-1,YOffset=0,WireCount=8,Side=W)
        output  [7:0] W2BEGb,        //Port(Name=W2BEGb,IO=OUTPUT,XOffset=-1,YOffset=0,WireCount=8,Side=W)
 //S
        input  [3:0] N_GBUF_END,        //Port(Name=N_GBUF_END,IO=INPUT,XOffset=0,YOffset=-1,WireCount=4,Side=S)
        input  [7:0] N1END,        //Port(Name=N1END,IO=INPUT,XOffset=0,YOffset=-1,WireCount=8,Side=S)
        input  [7:0] N2MID,        //Port(Name=N2MID,IO=INPUT,XOffset=0,YOffset=-1,WireCount=8,Side=S)
        input  [7:0] N2END,        //Port(Name=N2END,IO=INPUT,XOffset=0,YOffset=-1,WireCount=8,Side=S)
        output  [7:0] S1BEG,        //Port(Name=S1BEG,IO=OUTPUT,XOffset=0,YOffset=1,WireCount=8,Side=S)
        output  [7:0] S2BEG,        //Port(Name=S2BEG,IO=OUTPUT,XOffset=0,YOffset=1,WireCount=8,Side=S)
        output  [7:0] S2BEGb,        //Port(Name=S2BEGb,IO=OUTPUT,XOffset=0,YOffset=1,WireCount=8,Side=S)
        input  [0:0] CI,        //Port(Name=CI,IO=INPUT,XOffset=0,YOffset=-1,WireCount=1,Side=S)
    //Tile IO ports from BELs
        input  [FrameBitsPerRow-1:0] FrameData, //CONFIG_PORT
        output  [FrameBitsPerRow-1:0] FrameData_O,
        input  [MaxFramesPerCol-1:0] FrameStrobe, //CONFIG_PORT
        output  [MaxFramesPerCol-1:0] FrameStrobe_O
    //global
);
 //signal declarations
 //BEL ports (e.g., slices)
wire TA_CLK;
wire TA_rst;
wire TA_load;
wire TA_half;
wire TA_en;
wire TA_tc;
wire TB_CLK;
wire TB_rst;
wire TB_load;
wire TB_half;
wire TB_en;
wire TB_tc;
wire SA_CLK;
wire SA_rst;
wire SA_load;
wire SA_step;
wire SA_sin;
wire SA_d0;
wire SA_d1;
wire SA_d2;
wire SA_d3;
wire SA_d4;
wire SA_d5;
wire SA_d6;
wire SA_d7;
wire SA_sout;
wire SA_done;
wire SA_q0;
wire SA_q1;
wire SA_q2;
wire SA_q3;
wire SA_q4;
wire SA_q5;
wire SA_q6;
wire SA_q7;
wire SB_CLK;
wire SB_rst;
wire SB_load;
wire SB_step;
wire SB_sin;
wire SB_d0;
wire SB_d1;
wire SB_d2;
wire SB_d3;
wire SB_d4;
wire SB_d5;
wire SB_d6;
wire SB_d7;
wire SB_sout;
wire SB_done;
wire SB_q0;
wire SB_q1;
wire SB_q2;
wire SB_q3;
wire SB_q4;
wire SB_q5;
wire SB_q6;
wire SB_q7;
 //Jump wires
wire[4-1:0] J2MID_ABa_BEG;
wire[4-1:0] J2MID_CDa_BEG;
wire[4-1:0] J2MID_EFa_BEG;
wire[4-1:0] J2MID_GHa_BEG;
wire[4-1:0] J2MID_ABb_BEG;
wire[4-1:0] J2MID_CDb_BEG;
wire[4-1:0] J2MID_EFb_BEG;
wire[4-1:0] J2MID_GHb_BEG;
wire[4-1:0] J2END_AB_BEG;
wire[4-1:0] J2END_CD_BEG;
wire[4-1:0] J2END_EF_BEG;
wire[4-1:0] J2END_GH_BEG;
wire[8-1:0] JN2BEG;
wire[8-1:0] JE2BEG;
wire[8-1:0] JS2BEG;
wire[8-1:0] JW2BEG;
wire[4-1:0] J_l_AB_BEG;
wire[4-1:0] J_l_CD_BEG;
wire[4-1:0] J_l_EF_BEG;
wire[4-1:0] J_l_GH_BEG;
wire[1-1:0] GCLK_BEG;
 //internal configuration data signal to daisy-chain all BELs (if any and in the order they are listed in the fabric.csv)
wire[NoConfigBits-1:0] ConfigBits;
wire[NoConfigBits-1:0] ConfigBits_N;

 //Connection for outgoing wires
wire[FrameBitsPerRow-1:0] FrameData_i;
wire[FrameBitsPerRow-1:0] FrameData_O_i;
wire[MaxFramesPerCol-1:0] FrameStrobe_i;
wire[MaxFramesPerCol-1:0] FrameStrobe_O_i;

assign FrameData_O_i = FrameData_i;

my_buf data_inbuf_0 (
    .A(FrameData[0]),
    .X(FrameData_i[0])
);

my_buf data_inbuf_1 (
    .A(FrameData[1]),
    .X(FrameData_i[1])
);

my_buf data_inbuf_2 (
    .A(FrameData[2]),
    .X(FrameData_i[2])
);

my_buf data_inbuf_3 (
    .A(FrameData[3]),
    .X(FrameData_i[3])
);

my_buf data_inbuf_4 (
    .A(FrameData[4]),
    .X(FrameData_i[4])
);

my_buf data_inbuf_5 (
    .A(FrameData[5]),
    .X(FrameData_i[5])
);

my_buf data_inbuf_6 (
    .A(FrameData[6]),
    .X(FrameData_i[6])
);

my_buf data_inbuf_7 (
    .A(FrameData[7]),
    .X(FrameData_i[7])
);

my_buf data_inbuf_8 (
    .A(FrameData[8]),
    .X(FrameData_i[8])
);

my_buf data_inbuf_9 (
    .A(FrameData[9]),
    .X(FrameData_i[9])
);

my_buf data_inbuf_10 (
    .A(FrameData[10]),
    .X(FrameData_i[10])
);

my_buf data_inbuf_11 (
    .A(FrameData[11]),
    .X(FrameData_i[11])
);

my_buf data_inbuf_12 (
    .A(FrameData[12]),
    .X(FrameData_i[12])
);

my_buf data_inbuf_13 (
    .A(FrameData[13]),
    .X(FrameData_i[13])
);

my_buf data_inbuf_14 (
    .A(FrameData[14]),
    .X(FrameData_i[14])
);

my_buf data_inbuf_15 (
    .A(FrameData[15]),
    .X(FrameData_i[15])
);

my_buf data_inbuf_16 (
    .A(FrameData[16]),
    .X(FrameData_i[16])
);

my_buf data_inbuf_17 (
    .A(FrameData[17]),
    .X(FrameData_i[17])
);

my_buf data_inbuf_18 (
    .A(FrameData[18]),
    .X(FrameData_i[18])
);

my_buf data_inbuf_19 (
    .A(FrameData[19]),
    .X(FrameData_i[19])
);

my_buf data_inbuf_20 (
    .A(FrameData[20]),
    .X(FrameData_i[20])
);

my_buf data_inbuf_21 (
    .A(FrameData[21]),
    .X(FrameData_i[21])
);

my_buf data_inbuf_22 (
    .A(FrameData[22]),
    .X(FrameData_i[22])
);

my_buf data_inbuf_23 (
    .A(FrameData[23]),
    .X(FrameData_i[23])
);

my_buf data_inbuf_24 (
    .A(FrameData[24]),
    .X(FrameData_i[24])
);

my_buf data_inbuf_25 (
    .A(FrameData[25]),
    .X(FrameData_i[25])
);

my_buf data_inbuf_26 (
    .A(FrameData[26]),
    .X(FrameData_i[26])
);

my_buf data_inbuf_27 (
    .A(FrameData[27]),
    .X(FrameData_i[27])
);

my_buf data_inbuf_28 (
    .A(FrameData[28]),
    .X(FrameData_i[28])
);

my_buf data_inbuf_29 (
    .A(FrameData[29]),
    .X(FrameData_i[29])
);

my_buf data_inbuf_30 (
    .A(FrameData[30]),
    .X(FrameData_i[30])
);

my_buf data_inbuf_31 (
    .A(FrameData[31]),
    .X(FrameData_i[31])
);

my_buf data_outbuf_0 (
    .A(FrameData_O_i[0]),
    .X(FrameData_O[0])
);

my_buf data_outbuf_1 (
    .A(FrameData_O_i[1]),
    .X(FrameData_O[1])
);

my_buf data_outbuf_2 (
    .A(FrameData_O_i[2]),
    .X(FrameData_O[2])
);

my_buf data_outbuf_3 (
    .A(FrameData_O_i[3]),
    .X(FrameData_O[3])
);

my_buf data_outbuf_4 (
    .A(FrameData_O_i[4]),
    .X(FrameData_O[4])
);

my_buf data_outbuf_5 (
    .A(FrameData_O_i[5]),
    .X(FrameData_O[5])
);

my_buf data_outbuf_6 (
    .A(FrameData_O_i[6]),
    .X(FrameData_O[6])
);

my_buf data_outbuf_7 (
    .A(FrameData_O_i[7]),
    .X(FrameData_O[7])
);

my_buf data_outbuf_8 (
    .A(FrameData_O_i[8]),
    .X(FrameData_O[8])
);

my_buf data_outbuf_9 (
    .A(FrameData_O_i[9]),
    .X(FrameData_O[9])
);

my_buf data_outbuf_10 (
    .A(FrameData_O_i[10]),
    .X(FrameData_O[10])
);

my_buf data_outbuf_11 (
    .A(FrameData_O_i[11]),
    .X(FrameData_O[11])
);

my_buf data_outbuf_12 (
    .A(FrameData_O_i[12]),
    .X(FrameData_O[12])
);

my_buf data_outbuf_13 (
    .A(FrameData_O_i[13]),
    .X(FrameData_O[13])
);

my_buf data_outbuf_14 (
    .A(FrameData_O_i[14]),
    .X(FrameData_O[14])
);

my_buf data_outbuf_15 (
    .A(FrameData_O_i[15]),
    .X(FrameData_O[15])
);

my_buf data_outbuf_16 (
    .A(FrameData_O_i[16]),
    .X(FrameData_O[16])
);

my_buf data_outbuf_17 (
    .A(FrameData_O_i[17]),
    .X(FrameData_O[17])
);

my_buf data_outbuf_18 (
    .A(FrameData_O_i[18]),
    .X(FrameData_O[18])
);

my_buf data_outbuf_19 (
    .A(FrameData_O_i[19]),
    .X(FrameData_O[19])
);

my_buf data_outbuf_20 (
    .A(FrameData_O_i[20]),
    .X(FrameData_O[20])
);

my_buf data_outbuf_21 (
    .A(FrameData_O_i[21]),
    .X(FrameData_O[21])
);

my_buf data_outbuf_22 (
    .A(FrameData_O_i[22]),
    .X(FrameData_O[22])
);

my_buf data_outbuf_23 (
    .A(FrameData_O_i[23]),
    .X(FrameData_O[23])
);

my_buf data_outbuf_24 (
    .A(FrameData_O_i[24]),
    .X(FrameData_O[24])
);

my_buf data_outbuf_25 (
    .A(FrameData_O_i[25]),
    .X(FrameData_O[25])
);

my_buf data_outbuf_26 (
    .A(FrameData_O_i[26]),
    .X(FrameData_O[26])
);

my_buf data_outbuf_27 (
    .A(FrameData_O_i[27]),
    .X(FrameData_O[27])
);

my_buf data_outbuf_28 (
    .A(FrameData_O_i[28]),
    .X(FrameData_O[28])
);

my_buf data_outbuf_29 (
    .A(FrameData_O_i[29]),
    .X(FrameData_O[29])
);

my_buf data_outbuf_30 (
    .A(FrameData_O_i[30]),
    .X(FrameData_O[30])
);

my_buf data_outbuf_31 (
    .A(FrameData_O_i[31]),
    .X(FrameData_O[31])
);

assign FrameStrobe_O_i = FrameStrobe_i;

my_buf strobe_inbuf_0 (
    .A(FrameStrobe[0]),
    .X(FrameStrobe_i[0])
);

my_buf strobe_inbuf_1 (
    .A(FrameStrobe[1]),
    .X(FrameStrobe_i[1])
);

my_buf strobe_inbuf_2 (
    .A(FrameStrobe[2]),
    .X(FrameStrobe_i[2])
);

my_buf strobe_inbuf_3 (
    .A(FrameStrobe[3]),
    .X(FrameStrobe_i[3])
);

my_buf strobe_inbuf_4 (
    .A(FrameStrobe[4]),
    .X(FrameStrobe_i[4])
);

my_buf strobe_inbuf_5 (
    .A(FrameStrobe[5]),
    .X(FrameStrobe_i[5])
);

my_buf strobe_inbuf_6 (
    .A(FrameStrobe[6]),
    .X(FrameStrobe_i[6])
);

my_buf strobe_inbuf_7 (
    .A(FrameStrobe[7]),
    .X(FrameStrobe_i[7])
);

my_buf strobe_inbuf_8 (
    .A(FrameStrobe[8]),
    .X(FrameStrobe_i[8])
);

my_buf strobe_inbuf_9 (
    .A(FrameStrobe[9]),
    .X(FrameStrobe_i[9])
);

my_buf strobe_inbuf_10 (
    .A(FrameStrobe[10]),
    .X(FrameStrobe_i[10])
);

my_buf strobe_inbuf_11 (
    .A(FrameStrobe[11]),
    .X(FrameStrobe_i[11])
);

my_buf strobe_inbuf_12 (
    .A(FrameStrobe[12]),
    .X(FrameStrobe_i[12])
);

my_buf strobe_inbuf_13 (
    .A(FrameStrobe[13]),
    .X(FrameStrobe_i[13])
);

my_buf strobe_inbuf_14 (
    .A(FrameStrobe[14]),
    .X(FrameStrobe_i[14])
);

my_buf strobe_inbuf_15 (
    .A(FrameStrobe[15]),
    .X(FrameStrobe_i[15])
);

my_buf strobe_inbuf_16 (
    .A(FrameStrobe[16]),
    .X(FrameStrobe_i[16])
);

my_buf strobe_inbuf_17 (
    .A(FrameStrobe[17]),
    .X(FrameStrobe_i[17])
);

my_buf strobe_inbuf_18 (
    .A(FrameStrobe[18]),
    .X(FrameStrobe_i[18])
);

my_buf strobe_inbuf_19 (
    .A(FrameStrobe[19]),
    .X(FrameStrobe_i[19])
);

my_buf strobe_outbuf_0 (
    .A(FrameStrobe_O_i[0]),
    .X(FrameStrobe_O[0])
);

my_buf strobe_outbuf_1 (
    .A(FrameStrobe_O_i[1]),
    .X(FrameStrobe_O[1])
);

my_buf strobe_outbuf_2 (
    .A(FrameStrobe_O_i[2]),
    .X(FrameStrobe_O[2])
);

my_buf strobe_outbuf_3 (
    .A(FrameStrobe_O_i[3]),
    .X(FrameStrobe_O[3])
);

my_buf strobe_outbuf_4 (
    .A(FrameStrobe_O_i[4]),
    .X(FrameStrobe_O[4])
);

my_buf strobe_outbuf_5 (
    .A(FrameStrobe_O_i[5]),
    .X(FrameStrobe_O[5])
);

my_buf strobe_outbuf_6 (
    .A(FrameStrobe_O_i[6]),
    .X(FrameStrobe_O[6])
);

my_buf strobe_outbuf_7 (
    .A(FrameStrobe_O_i[7]),
    .X(FrameStrobe_O[7])
);

my_buf strobe_outbuf_8 (
    .A(FrameStrobe_O_i[8]),
    .X(FrameStrobe_O[8])
);

my_buf strobe_outbuf_9 (
    .A(FrameStrobe_O_i[9]),
    .X(FrameStrobe_O[9])
);

my_buf strobe_outbuf_10 (
    .A(FrameStrobe_O_i[10]),
    .X(FrameStrobe_O[10])
);

my_buf strobe_outbuf_11 (
    .A(FrameStrobe_O_i[11]),
    .X(FrameStrobe_O[11])
);

my_buf strobe_outbuf_12 (
    .A(FrameStrobe_O_i[12]),
    .X(FrameStrobe_O[12])
);

my_buf strobe_outbuf_13 (
    .A(FrameStrobe_O_i[13]),
    .X(FrameStrobe_O[13])
);

my_buf strobe_outbuf_14 (
    .A(FrameStrobe_O_i[14]),
    .X(FrameStrobe_O[14])
);

my_buf strobe_outbuf_15 (
    .A(FrameStrobe_O_i[15]),
    .X(FrameStrobe_O[15])
);

my_buf strobe_outbuf_16 (
    .A(FrameStrobe_O_i[16]),
    .X(FrameStrobe_O[16])
);

my_buf strobe_outbuf_17 (
    .A(FrameStrobe_O_i[17]),
    .X(FrameStrobe_O[17])
);

my_buf strobe_outbuf_18 (
    .A(FrameStrobe_O_i[18]),
    .X(FrameStrobe_O[18])
);

my_buf strobe_outbuf_19 (
    .A(FrameStrobe_O_i[19]),
    .X(FrameStrobe_O[19])
);


 //configuration storage latches
PRIM2T2S_ConfigMem
`ifdef EMULATION
    #(
    .Emulate_Bitstream(Emulate_Bitstream)
    )
`endif
    Inst_PRIM2T2S_ConfigMem
    (
    .FrameData(FrameData),
    .FrameStrobe(FrameStrobe),
    .ConfigBits(ConfigBits),
    .ConfigBits_N(ConfigBits_N)
);


 //BEL component instantiations
wp_timer Inst_TA_wp_timer (
    .CLK(TA_CLK),
    .rst(TA_rst),
    .load(TA_load),
    .half(TA_half),
    .en(TA_en),
    .tc(TA_tc),
    .ConfigBits(ConfigBits[17-1:0])
);

wp_timer Inst_TB_wp_timer (
    .CLK(TB_CLK),
    .rst(TB_rst),
    .load(TB_load),
    .half(TB_half),
    .en(TB_en),
    .tc(TB_tc),
    .ConfigBits(ConfigBits[34-1:17])
);

wp_shift Inst_SA_wp_shift (
    .CLK(SA_CLK),
    .rst(SA_rst),
    .load(SA_load),
    .step(SA_step),
    .sin(SA_sin),
    .d({SA_d7, SA_d6, SA_d5, SA_d4, SA_d3, SA_d2, SA_d1, SA_d0}),
    .sout(SA_sout),
    .done(SA_done),
    .q({SA_q7, SA_q6, SA_q5, SA_q4, SA_q3, SA_q2, SA_q1, SA_q0}),
    .ConfigBits(ConfigBits[39-1:34])
);

wp_shift Inst_SB_wp_shift (
    .CLK(SB_CLK),
    .rst(SB_rst),
    .load(SB_load),
    .step(SB_step),
    .sin(SB_sin),
    .d({SB_d7, SB_d6, SB_d5, SB_d4, SB_d3, SB_d2, SB_d1, SB_d0}),
    .sout(SB_sout),
    .done(SB_done),
    .q({SB_q7, SB_q6, SB_q5, SB_q4, SB_q3, SB_q2, SB_q1, SB_q0}),
    .ConfigBits(ConfigBits[44-1:39])
);

PRIM2T2S_switch_matrix Inst_PRIM2T2S_switch_matrix (
    .N_GBUF_END0(N_GBUF_END[0]),
    .N_GBUF_END1(N_GBUF_END[1]),
    .N_GBUF_END2(N_GBUF_END[2]),
    .N_GBUF_END3(N_GBUF_END[3]),
    .N1END0(N1END[0]),
    .N1END1(N1END[1]),
    .N1END2(N1END[2]),
    .N1END3(N1END[3]),
    .N1END4(N1END[4]),
    .N1END5(N1END[5]),
    .N1END6(N1END[6]),
    .N1END7(N1END[7]),
    .N2MID0(N2MID[0]),
    .N2MID1(N2MID[1]),
    .N2MID2(N2MID[2]),
    .N2MID3(N2MID[3]),
    .N2MID4(N2MID[4]),
    .N2MID5(N2MID[5]),
    .N2MID6(N2MID[6]),
    .N2MID7(N2MID[7]),
    .N2END0(N2END[0]),
    .N2END1(N2END[1]),
    .N2END2(N2END[2]),
    .N2END3(N2END[3]),
    .N2END4(N2END[4]),
    .N2END5(N2END[5]),
    .N2END6(N2END[6]),
    .N2END7(N2END[7]),
    .E1END0(E1END[0]),
    .E1END1(E1END[1]),
    .E1END2(E1END[2]),
    .E1END3(E1END[3]),
    .E1END4(E1END[4]),
    .E1END5(E1END[5]),
    .E1END6(E1END[6]),
    .E1END7(E1END[7]),
    .E2MID0(E2MID[0]),
    .E2MID1(E2MID[1]),
    .E2MID2(E2MID[2]),
    .E2MID3(E2MID[3]),
    .E2MID4(E2MID[4]),
    .E2MID5(E2MID[5]),
    .E2MID6(E2MID[6]),
    .E2MID7(E2MID[7]),
    .E2END0(E2END[0]),
    .E2END1(E2END[1]),
    .E2END2(E2END[2]),
    .E2END3(E2END[3]),
    .E2END4(E2END[4]),
    .E2END5(E2END[5]),
    .E2END6(E2END[6]),
    .E2END7(E2END[7]),
    .S1END0(S1END[0]),
    .S1END1(S1END[1]),
    .S1END2(S1END[2]),
    .S1END3(S1END[3]),
    .S1END4(S1END[4]),
    .S1END5(S1END[5]),
    .S1END6(S1END[6]),
    .S1END7(S1END[7]),
    .S2MID0(S2MID[0]),
    .S2MID1(S2MID[1]),
    .S2MID2(S2MID[2]),
    .S2MID3(S2MID[3]),
    .S2MID4(S2MID[4]),
    .S2MID5(S2MID[5]),
    .S2MID6(S2MID[6]),
    .S2MID7(S2MID[7]),
    .S2END0(S2END[0]),
    .S2END1(S2END[1]),
    .S2END2(S2END[2]),
    .S2END3(S2END[3]),
    .S2END4(S2END[4]),
    .S2END5(S2END[5]),
    .S2END6(S2END[6]),
    .S2END7(S2END[7]),
    .W1END0(W1END[0]),
    .W1END1(W1END[1]),
    .W1END2(W1END[2]),
    .W1END3(W1END[3]),
    .W1END4(W1END[4]),
    .W1END5(W1END[5]),
    .W1END6(W1END[6]),
    .W1END7(W1END[7]),
    .W2MID0(W2MID[0]),
    .W2MID1(W2MID[1]),
    .W2MID2(W2MID[2]),
    .W2MID3(W2MID[3]),
    .W2MID4(W2MID[4]),
    .W2MID5(W2MID[5]),
    .W2MID6(W2MID[6]),
    .W2MID7(W2MID[7]),
    .W2END0(W2END[0]),
    .W2END1(W2END[1]),
    .W2END2(W2END[2]),
    .W2END3(W2END[3]),
    .W2END4(W2END[4]),
    .W2END5(W2END[5]),
    .W2END6(W2END[6]),
    .W2END7(W2END[7]),
    .CI0(CI[0]),
    .TA_tc(TA_tc),
    .TB_tc(TB_tc),
    .SA_sout(SA_sout),
    .SA_done(SA_done),
    .SA_q0(SA_q0),
    .SA_q1(SA_q1),
    .SA_q2(SA_q2),
    .SA_q3(SA_q3),
    .SA_q4(SA_q4),
    .SA_q5(SA_q5),
    .SA_q6(SA_q6),
    .SA_q7(SA_q7),
    .SB_sout(SB_sout),
    .SB_done(SB_done),
    .SB_q0(SB_q0),
    .SB_q1(SB_q1),
    .SB_q2(SB_q2),
    .SB_q3(SB_q3),
    .SB_q4(SB_q4),
    .SB_q5(SB_q5),
    .SB_q6(SB_q6),
    .SB_q7(SB_q7),
    .J2MID_ABa_END0(J2MID_ABa_BEG[0]),
    .J2MID_ABa_END1(J2MID_ABa_BEG[1]),
    .J2MID_ABa_END2(J2MID_ABa_BEG[2]),
    .J2MID_ABa_END3(J2MID_ABa_BEG[3]),
    .J2MID_CDa_END0(J2MID_CDa_BEG[0]),
    .J2MID_CDa_END1(J2MID_CDa_BEG[1]),
    .J2MID_CDa_END2(J2MID_CDa_BEG[2]),
    .J2MID_CDa_END3(J2MID_CDa_BEG[3]),
    .J2MID_EFa_END0(J2MID_EFa_BEG[0]),
    .J2MID_EFa_END1(J2MID_EFa_BEG[1]),
    .J2MID_EFa_END2(J2MID_EFa_BEG[2]),
    .J2MID_EFa_END3(J2MID_EFa_BEG[3]),
    .J2MID_GHa_END0(J2MID_GHa_BEG[0]),
    .J2MID_GHa_END1(J2MID_GHa_BEG[1]),
    .J2MID_GHa_END2(J2MID_GHa_BEG[2]),
    .J2MID_GHa_END3(J2MID_GHa_BEG[3]),
    .J2MID_ABb_END0(J2MID_ABb_BEG[0]),
    .J2MID_ABb_END1(J2MID_ABb_BEG[1]),
    .J2MID_ABb_END2(J2MID_ABb_BEG[2]),
    .J2MID_ABb_END3(J2MID_ABb_BEG[3]),
    .J2MID_CDb_END0(J2MID_CDb_BEG[0]),
    .J2MID_CDb_END1(J2MID_CDb_BEG[1]),
    .J2MID_CDb_END2(J2MID_CDb_BEG[2]),
    .J2MID_CDb_END3(J2MID_CDb_BEG[3]),
    .J2MID_EFb_END0(J2MID_EFb_BEG[0]),
    .J2MID_EFb_END1(J2MID_EFb_BEG[1]),
    .J2MID_EFb_END2(J2MID_EFb_BEG[2]),
    .J2MID_EFb_END3(J2MID_EFb_BEG[3]),
    .J2MID_GHb_END0(J2MID_GHb_BEG[0]),
    .J2MID_GHb_END1(J2MID_GHb_BEG[1]),
    .J2MID_GHb_END2(J2MID_GHb_BEG[2]),
    .J2MID_GHb_END3(J2MID_GHb_BEG[3]),
    .J2END_AB_END0(J2END_AB_BEG[0]),
    .J2END_AB_END1(J2END_AB_BEG[1]),
    .J2END_AB_END2(J2END_AB_BEG[2]),
    .J2END_AB_END3(J2END_AB_BEG[3]),
    .J2END_CD_END0(J2END_CD_BEG[0]),
    .J2END_CD_END1(J2END_CD_BEG[1]),
    .J2END_CD_END2(J2END_CD_BEG[2]),
    .J2END_CD_END3(J2END_CD_BEG[3]),
    .J2END_EF_END0(J2END_EF_BEG[0]),
    .J2END_EF_END1(J2END_EF_BEG[1]),
    .J2END_EF_END2(J2END_EF_BEG[2]),
    .J2END_EF_END3(J2END_EF_BEG[3]),
    .J2END_GH_END0(J2END_GH_BEG[0]),
    .J2END_GH_END1(J2END_GH_BEG[1]),
    .J2END_GH_END2(J2END_GH_BEG[2]),
    .J2END_GH_END3(J2END_GH_BEG[3]),
    .JN2END0(JN2BEG[0]),
    .JN2END1(JN2BEG[1]),
    .JN2END2(JN2BEG[2]),
    .JN2END3(JN2BEG[3]),
    .JN2END4(JN2BEG[4]),
    .JN2END5(JN2BEG[5]),
    .JN2END6(JN2BEG[6]),
    .JN2END7(JN2BEG[7]),
    .JE2END0(JE2BEG[0]),
    .JE2END1(JE2BEG[1]),
    .JE2END2(JE2BEG[2]),
    .JE2END3(JE2BEG[3]),
    .JE2END4(JE2BEG[4]),
    .JE2END5(JE2BEG[5]),
    .JE2END6(JE2BEG[6]),
    .JE2END7(JE2BEG[7]),
    .JS2END0(JS2BEG[0]),
    .JS2END1(JS2BEG[1]),
    .JS2END2(JS2BEG[2]),
    .JS2END3(JS2BEG[3]),
    .JS2END4(JS2BEG[4]),
    .JS2END5(JS2BEG[5]),
    .JS2END6(JS2BEG[6]),
    .JS2END7(JS2BEG[7]),
    .JW2END0(JW2BEG[0]),
    .JW2END1(JW2BEG[1]),
    .JW2END2(JW2BEG[2]),
    .JW2END3(JW2BEG[3]),
    .JW2END4(JW2BEG[4]),
    .JW2END5(JW2BEG[5]),
    .JW2END6(JW2BEG[6]),
    .JW2END7(JW2BEG[7]),
    .J_l_AB_END0(J_l_AB_BEG[0]),
    .J_l_AB_END1(J_l_AB_BEG[1]),
    .J_l_AB_END2(J_l_AB_BEG[2]),
    .J_l_AB_END3(J_l_AB_BEG[3]),
    .J_l_CD_END0(J_l_CD_BEG[0]),
    .J_l_CD_END1(J_l_CD_BEG[1]),
    .J_l_CD_END2(J_l_CD_BEG[2]),
    .J_l_CD_END3(J_l_CD_BEG[3]),
    .J_l_EF_END0(J_l_EF_BEG[0]),
    .J_l_EF_END1(J_l_EF_BEG[1]),
    .J_l_EF_END2(J_l_EF_BEG[2]),
    .J_l_EF_END3(J_l_EF_BEG[3]),
    .J_l_GH_END0(J_l_GH_BEG[0]),
    .J_l_GH_END1(J_l_GH_BEG[1]),
    .J_l_GH_END2(J_l_GH_BEG[2]),
    .J_l_GH_END3(J_l_GH_BEG[3]),
    .GCLK_END0(GCLK_BEG[0]),
    .N_GBUF_BEG0(N_GBUF_BEG[0]),
    .N_GBUF_BEG1(N_GBUF_BEG[1]),
    .N_GBUF_BEG2(N_GBUF_BEG[2]),
    .N_GBUF_BEG3(N_GBUF_BEG[3]),
    .N1BEG0(N1BEG[0]),
    .N1BEG1(N1BEG[1]),
    .N1BEG2(N1BEG[2]),
    .N1BEG3(N1BEG[3]),
    .N1BEG4(N1BEG[4]),
    .N1BEG5(N1BEG[5]),
    .N1BEG6(N1BEG[6]),
    .N1BEG7(N1BEG[7]),
    .N2BEG0(N2BEG[0]),
    .N2BEG1(N2BEG[1]),
    .N2BEG2(N2BEG[2]),
    .N2BEG3(N2BEG[3]),
    .N2BEG4(N2BEG[4]),
    .N2BEG5(N2BEG[5]),
    .N2BEG6(N2BEG[6]),
    .N2BEG7(N2BEG[7]),
    .N2BEGb0(N2BEGb[0]),
    .N2BEGb1(N2BEGb[1]),
    .N2BEGb2(N2BEGb[2]),
    .N2BEGb3(N2BEGb[3]),
    .N2BEGb4(N2BEGb[4]),
    .N2BEGb5(N2BEGb[5]),
    .N2BEGb6(N2BEGb[6]),
    .N2BEGb7(N2BEGb[7]),
    .E1BEG0(E1BEG[0]),
    .E1BEG1(E1BEG[1]),
    .E1BEG2(E1BEG[2]),
    .E1BEG3(E1BEG[3]),
    .E1BEG4(E1BEG[4]),
    .E1BEG5(E1BEG[5]),
    .E1BEG6(E1BEG[6]),
    .E1BEG7(E1BEG[7]),
    .E2BEG0(E2BEG[0]),
    .E2BEG1(E2BEG[1]),
    .E2BEG2(E2BEG[2]),
    .E2BEG3(E2BEG[3]),
    .E2BEG4(E2BEG[4]),
    .E2BEG5(E2BEG[5]),
    .E2BEG6(E2BEG[6]),
    .E2BEG7(E2BEG[7]),
    .E2BEGb0(E2BEGb[0]),
    .E2BEGb1(E2BEGb[1]),
    .E2BEGb2(E2BEGb[2]),
    .E2BEGb3(E2BEGb[3]),
    .E2BEGb4(E2BEGb[4]),
    .E2BEGb5(E2BEGb[5]),
    .E2BEGb6(E2BEGb[6]),
    .E2BEGb7(E2BEGb[7]),
    .S1BEG0(S1BEG[0]),
    .S1BEG1(S1BEG[1]),
    .S1BEG2(S1BEG[2]),
    .S1BEG3(S1BEG[3]),
    .S1BEG4(S1BEG[4]),
    .S1BEG5(S1BEG[5]),
    .S1BEG6(S1BEG[6]),
    .S1BEG7(S1BEG[7]),
    .S2BEG0(S2BEG[0]),
    .S2BEG1(S2BEG[1]),
    .S2BEG2(S2BEG[2]),
    .S2BEG3(S2BEG[3]),
    .S2BEG4(S2BEG[4]),
    .S2BEG5(S2BEG[5]),
    .S2BEG6(S2BEG[6]),
    .S2BEG7(S2BEG[7]),
    .S2BEGb0(S2BEGb[0]),
    .S2BEGb1(S2BEGb[1]),
    .S2BEGb2(S2BEGb[2]),
    .S2BEGb3(S2BEGb[3]),
    .S2BEGb4(S2BEGb[4]),
    .S2BEGb5(S2BEGb[5]),
    .S2BEGb6(S2BEGb[6]),
    .S2BEGb7(S2BEGb[7]),
    .W1BEG0(W1BEG[0]),
    .W1BEG1(W1BEG[1]),
    .W1BEG2(W1BEG[2]),
    .W1BEG3(W1BEG[3]),
    .W1BEG4(W1BEG[4]),
    .W1BEG5(W1BEG[5]),
    .W1BEG6(W1BEG[6]),
    .W1BEG7(W1BEG[7]),
    .W2BEG0(W2BEG[0]),
    .W2BEG1(W2BEG[1]),
    .W2BEG2(W2BEG[2]),
    .W2BEG3(W2BEG[3]),
    .W2BEG4(W2BEG[4]),
    .W2BEG5(W2BEG[5]),
    .W2BEG6(W2BEG[6]),
    .W2BEG7(W2BEG[7]),
    .W2BEGb0(W2BEGb[0]),
    .W2BEGb1(W2BEGb[1]),
    .W2BEGb2(W2BEGb[2]),
    .W2BEGb3(W2BEGb[3]),
    .W2BEGb4(W2BEGb[4]),
    .W2BEGb5(W2BEGb[5]),
    .W2BEGb6(W2BEGb[6]),
    .W2BEGb7(W2BEGb[7]),
    .CO0(CO[0]),
    .TA_CLK(TA_CLK),
    .TA_rst(TA_rst),
    .TA_load(TA_load),
    .TA_half(TA_half),
    .TA_en(TA_en),
    .TB_CLK(TB_CLK),
    .TB_rst(TB_rst),
    .TB_load(TB_load),
    .TB_half(TB_half),
    .TB_en(TB_en),
    .SA_CLK(SA_CLK),
    .SA_rst(SA_rst),
    .SA_load(SA_load),
    .SA_step(SA_step),
    .SA_sin(SA_sin),
    .SA_d0(SA_d0),
    .SA_d1(SA_d1),
    .SA_d2(SA_d2),
    .SA_d3(SA_d3),
    .SA_d4(SA_d4),
    .SA_d5(SA_d5),
    .SA_d6(SA_d6),
    .SA_d7(SA_d7),
    .SB_CLK(SB_CLK),
    .SB_rst(SB_rst),
    .SB_load(SB_load),
    .SB_step(SB_step),
    .SB_sin(SB_sin),
    .SB_d0(SB_d0),
    .SB_d1(SB_d1),
    .SB_d2(SB_d2),
    .SB_d3(SB_d3),
    .SB_d4(SB_d4),
    .SB_d5(SB_d5),
    .SB_d6(SB_d6),
    .SB_d7(SB_d7),
    .J2MID_ABa_BEG0(J2MID_ABa_BEG[0]),
    .J2MID_ABa_BEG1(J2MID_ABa_BEG[1]),
    .J2MID_ABa_BEG2(J2MID_ABa_BEG[2]),
    .J2MID_ABa_BEG3(J2MID_ABa_BEG[3]),
    .J2MID_CDa_BEG0(J2MID_CDa_BEG[0]),
    .J2MID_CDa_BEG1(J2MID_CDa_BEG[1]),
    .J2MID_CDa_BEG2(J2MID_CDa_BEG[2]),
    .J2MID_CDa_BEG3(J2MID_CDa_BEG[3]),
    .J2MID_EFa_BEG0(J2MID_EFa_BEG[0]),
    .J2MID_EFa_BEG1(J2MID_EFa_BEG[1]),
    .J2MID_EFa_BEG2(J2MID_EFa_BEG[2]),
    .J2MID_EFa_BEG3(J2MID_EFa_BEG[3]),
    .J2MID_GHa_BEG0(J2MID_GHa_BEG[0]),
    .J2MID_GHa_BEG1(J2MID_GHa_BEG[1]),
    .J2MID_GHa_BEG2(J2MID_GHa_BEG[2]),
    .J2MID_GHa_BEG3(J2MID_GHa_BEG[3]),
    .J2MID_ABb_BEG0(J2MID_ABb_BEG[0]),
    .J2MID_ABb_BEG1(J2MID_ABb_BEG[1]),
    .J2MID_ABb_BEG2(J2MID_ABb_BEG[2]),
    .J2MID_ABb_BEG3(J2MID_ABb_BEG[3]),
    .J2MID_CDb_BEG0(J2MID_CDb_BEG[0]),
    .J2MID_CDb_BEG1(J2MID_CDb_BEG[1]),
    .J2MID_CDb_BEG2(J2MID_CDb_BEG[2]),
    .J2MID_CDb_BEG3(J2MID_CDb_BEG[3]),
    .J2MID_EFb_BEG0(J2MID_EFb_BEG[0]),
    .J2MID_EFb_BEG1(J2MID_EFb_BEG[1]),
    .J2MID_EFb_BEG2(J2MID_EFb_BEG[2]),
    .J2MID_EFb_BEG3(J2MID_EFb_BEG[3]),
    .J2MID_GHb_BEG0(J2MID_GHb_BEG[0]),
    .J2MID_GHb_BEG1(J2MID_GHb_BEG[1]),
    .J2MID_GHb_BEG2(J2MID_GHb_BEG[2]),
    .J2MID_GHb_BEG3(J2MID_GHb_BEG[3]),
    .J2END_AB_BEG0(J2END_AB_BEG[0]),
    .J2END_AB_BEG1(J2END_AB_BEG[1]),
    .J2END_AB_BEG2(J2END_AB_BEG[2]),
    .J2END_AB_BEG3(J2END_AB_BEG[3]),
    .J2END_CD_BEG0(J2END_CD_BEG[0]),
    .J2END_CD_BEG1(J2END_CD_BEG[1]),
    .J2END_CD_BEG2(J2END_CD_BEG[2]),
    .J2END_CD_BEG3(J2END_CD_BEG[3]),
    .J2END_EF_BEG0(J2END_EF_BEG[0]),
    .J2END_EF_BEG1(J2END_EF_BEG[1]),
    .J2END_EF_BEG2(J2END_EF_BEG[2]),
    .J2END_EF_BEG3(J2END_EF_BEG[3]),
    .J2END_GH_BEG0(J2END_GH_BEG[0]),
    .J2END_GH_BEG1(J2END_GH_BEG[1]),
    .J2END_GH_BEG2(J2END_GH_BEG[2]),
    .J2END_GH_BEG3(J2END_GH_BEG[3]),
    .JN2BEG0(JN2BEG[0]),
    .JN2BEG1(JN2BEG[1]),
    .JN2BEG2(JN2BEG[2]),
    .JN2BEG3(JN2BEG[3]),
    .JN2BEG4(JN2BEG[4]),
    .JN2BEG5(JN2BEG[5]),
    .JN2BEG6(JN2BEG[6]),
    .JN2BEG7(JN2BEG[7]),
    .JE2BEG0(JE2BEG[0]),
    .JE2BEG1(JE2BEG[1]),
    .JE2BEG2(JE2BEG[2]),
    .JE2BEG3(JE2BEG[3]),
    .JE2BEG4(JE2BEG[4]),
    .JE2BEG5(JE2BEG[5]),
    .JE2BEG6(JE2BEG[6]),
    .JE2BEG7(JE2BEG[7]),
    .JS2BEG0(JS2BEG[0]),
    .JS2BEG1(JS2BEG[1]),
    .JS2BEG2(JS2BEG[2]),
    .JS2BEG3(JS2BEG[3]),
    .JS2BEG4(JS2BEG[4]),
    .JS2BEG5(JS2BEG[5]),
    .JS2BEG6(JS2BEG[6]),
    .JS2BEG7(JS2BEG[7]),
    .JW2BEG0(JW2BEG[0]),
    .JW2BEG1(JW2BEG[1]),
    .JW2BEG2(JW2BEG[2]),
    .JW2BEG3(JW2BEG[3]),
    .JW2BEG4(JW2BEG[4]),
    .JW2BEG5(JW2BEG[5]),
    .JW2BEG6(JW2BEG[6]),
    .JW2BEG7(JW2BEG[7]),
    .J_l_AB_BEG0(J_l_AB_BEG[0]),
    .J_l_AB_BEG1(J_l_AB_BEG[1]),
    .J_l_AB_BEG2(J_l_AB_BEG[2]),
    .J_l_AB_BEG3(J_l_AB_BEG[3]),
    .J_l_CD_BEG0(J_l_CD_BEG[0]),
    .J_l_CD_BEG1(J_l_CD_BEG[1]),
    .J_l_CD_BEG2(J_l_CD_BEG[2]),
    .J_l_CD_BEG3(J_l_CD_BEG[3]),
    .J_l_EF_BEG0(J_l_EF_BEG[0]),
    .J_l_EF_BEG1(J_l_EF_BEG[1]),
    .J_l_EF_BEG2(J_l_EF_BEG[2]),
    .J_l_EF_BEG3(J_l_EF_BEG[3]),
    .J_l_GH_BEG0(J_l_GH_BEG[0]),
    .J_l_GH_BEG1(J_l_GH_BEG[1]),
    .J_l_GH_BEG2(J_l_GH_BEG[2]),
    .J_l_GH_BEG3(J_l_GH_BEG[3]),
    .GCLK_BEG0(GCLK_BEG[0]),
    .ConfigBits(ConfigBits[430-1:44]),
    .ConfigBits_N(ConfigBits_N[430-1:44])
);

endmodule