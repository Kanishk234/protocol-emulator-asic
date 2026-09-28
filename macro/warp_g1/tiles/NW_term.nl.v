module NW_term (FrameData,
    FrameData_O,
    FrameStrobe,
    FrameStrobe_O,
    N_GBUF_END,
    S_GBUF_FEED_BEG);
 input [31:0] FrameData;
 output [31:0] FrameData_O;
 input [19:0] FrameStrobe;
 output [19:0] FrameStrobe_O;
 input [3:0] N_GBUF_END;
 output [3:0] S_GBUF_FEED_BEG;

 wire net1;
 wire net2;
 wire net3;
 wire net4;
 wire net5;
 wire net6;
 wire net7;
 wire net8;
 wire net9;
 wire net10;
 wire net11;
 wire net12;
 wire net13;
 wire net14;
 wire net15;
 wire net16;
 wire net17;
 wire net18;
 wire net19;
 wire net20;
 wire net21;
 wire net22;
 wire net23;
 wire net24;
 wire net25;
 wire net26;
 wire net27;
 wire net28;
 wire net29;
 wire net30;
 wire net31;
 wire net32;
 wire net33;
 wire net34;
 wire net35;
 wire net36;
 wire net37;
 wire net38;
 wire net39;
 wire net40;
 wire net41;
 wire net42;
 wire net43;
 wire net44;
 wire net45;
 wire net46;
 wire net47;
 wire net48;
 wire net49;
 wire net50;
 wire net51;
 wire net52;
 wire \Inst_NW_term_ConfigMem.Inst_frame0_bit28.Q ;
 wire \Inst_NW_term_ConfigMem.Inst_frame0_bit29.Q ;
 wire \Inst_NW_term_ConfigMem.Inst_frame0_bit30.Q ;
 wire \Inst_NW_term_ConfigMem.Inst_frame0_bit31.Q ;
 wire net53;
 wire net54;
 wire net55;
 wire net56;

 sg13cmos5l_decap_8 FILLER_0_0 ();
 sg13cmos5l_decap_8 FILLER_0_106 ();
 sg13cmos5l_fill_2 FILLER_0_113 ();
 sg13cmos5l_fill_1 FILLER_0_115 ();
 sg13cmos5l_decap_8 FILLER_0_120 ();
 sg13cmos5l_decap_4 FILLER_0_127 ();
 sg13cmos5l_decap_8 FILLER_0_14 ();
 sg13cmos5l_decap_8 FILLER_0_21 ();
 sg13cmos5l_decap_8 FILLER_0_28 ();
 sg13cmos5l_decap_8 FILLER_0_35 ();
 sg13cmos5l_decap_8 FILLER_0_42 ();
 sg13cmos5l_decap_8 FILLER_0_49 ();
 sg13cmos5l_decap_8 FILLER_0_56 ();
 sg13cmos5l_decap_8 FILLER_0_63 ();
 sg13cmos5l_decap_8 FILLER_0_7 ();
 sg13cmos5l_decap_8 FILLER_0_70 ();
 sg13cmos5l_decap_8 FILLER_0_77 ();
 sg13cmos5l_decap_8 FILLER_0_84 ();
 sg13cmos5l_decap_4 FILLER_0_91 ();
 sg13cmos5l_decap_8 FILLER_0_99 ();
 sg13cmos5l_decap_8 FILLER_10_0 ();
 sg13cmos5l_fill_1 FILLER_10_102 ();
 sg13cmos5l_fill_2 FILLER_10_107 ();
 sg13cmos5l_decap_8 FILLER_10_121 ();
 sg13cmos5l_fill_2 FILLER_10_128 ();
 sg13cmos5l_fill_1 FILLER_10_130 ();
 sg13cmos5l_fill_1 FILLER_10_18 ();
 sg13cmos5l_decap_8 FILLER_10_27 ();
 sg13cmos5l_decap_4 FILLER_10_34 ();
 sg13cmos5l_fill_1 FILLER_10_38 ();
 sg13cmos5l_fill_1 FILLER_10_43 ();
 sg13cmos5l_fill_1 FILLER_10_48 ();
 sg13cmos5l_decap_8 FILLER_10_61 ();
 sg13cmos5l_decap_8 FILLER_10_68 ();
 sg13cmos5l_fill_2 FILLER_10_7 ();
 sg13cmos5l_decap_8 FILLER_10_75 ();
 sg13cmos5l_fill_1 FILLER_10_82 ();
 sg13cmos5l_fill_1 FILLER_10_87 ();
 sg13cmos5l_fill_1 FILLER_10_9 ();
 sg13cmos5l_fill_2 FILLER_10_96 ();
 sg13cmos5l_fill_2 FILLER_11_0 ();
 sg13cmos5l_fill_2 FILLER_11_100 ();
 sg13cmos5l_fill_2 FILLER_11_106 ();
 sg13cmos5l_fill_1 FILLER_11_112 ();
 sg13cmos5l_fill_2 FILLER_11_129 ();
 sg13cmos5l_fill_1 FILLER_11_2 ();
 sg13cmos5l_fill_2 FILLER_11_23 ();
 sg13cmos5l_fill_2 FILLER_11_33 ();
 sg13cmos5l_fill_1 FILLER_11_39 ();
 sg13cmos5l_fill_1 FILLER_11_44 ();
 sg13cmos5l_fill_1 FILLER_11_49 ();
 sg13cmos5l_decap_4 FILLER_11_70 ();
 sg13cmos5l_fill_1 FILLER_11_74 ();
 sg13cmos5l_fill_1 FILLER_11_95 ();
 sg13cmos5l_decap_8 FILLER_12_0 ();
 sg13cmos5l_decap_8 FILLER_12_105 ();
 sg13cmos5l_decap_4 FILLER_12_112 ();
 sg13cmos5l_fill_1 FILLER_12_116 ();
 sg13cmos5l_decap_8 FILLER_12_121 ();
 sg13cmos5l_fill_2 FILLER_12_128 ();
 sg13cmos5l_fill_1 FILLER_12_130 ();
 sg13cmos5l_decap_8 FILLER_12_14 ();
 sg13cmos5l_decap_8 FILLER_12_21 ();
 sg13cmos5l_decap_8 FILLER_12_28 ();
 sg13cmos5l_decap_8 FILLER_12_35 ();
 sg13cmos5l_decap_8 FILLER_12_42 ();
 sg13cmos5l_decap_8 FILLER_12_49 ();
 sg13cmos5l_decap_8 FILLER_12_56 ();
 sg13cmos5l_decap_8 FILLER_12_63 ();
 sg13cmos5l_fill_2 FILLER_12_7 ();
 sg13cmos5l_decap_8 FILLER_12_70 ();
 sg13cmos5l_decap_8 FILLER_12_77 ();
 sg13cmos5l_decap_8 FILLER_12_84 ();
 sg13cmos5l_fill_1 FILLER_12_9 ();
 sg13cmos5l_decap_8 FILLER_12_91 ();
 sg13cmos5l_decap_8 FILLER_12_98 ();
 sg13cmos5l_decap_8 FILLER_1_0 ();
 sg13cmos5l_decap_8 FILLER_1_124 ();
 sg13cmos5l_decap_8 FILLER_1_14 ();
 sg13cmos5l_fill_1 FILLER_1_21 ();
 sg13cmos5l_fill_2 FILLER_1_34 ();
 sg13cmos5l_decap_8 FILLER_1_40 ();
 sg13cmos5l_decap_8 FILLER_1_47 ();
 sg13cmos5l_decap_8 FILLER_1_54 ();
 sg13cmos5l_decap_8 FILLER_1_61 ();
 sg13cmos5l_decap_8 FILLER_1_68 ();
 sg13cmos5l_decap_8 FILLER_1_7 ();
 sg13cmos5l_decap_8 FILLER_1_75 ();
 sg13cmos5l_decap_4 FILLER_1_82 ();
 sg13cmos5l_fill_2 FILLER_1_90 ();
 sg13cmos5l_decap_8 FILLER_2_0 ();
 sg13cmos5l_fill_2 FILLER_2_101 ();
 sg13cmos5l_decap_4 FILLER_2_107 ();
 sg13cmos5l_fill_1 FILLER_2_115 ();
 sg13cmos5l_decap_8 FILLER_2_120 ();
 sg13cmos5l_decap_4 FILLER_2_127 ();
 sg13cmos5l_decap_8 FILLER_2_14 ();
 sg13cmos5l_decap_4 FILLER_2_21 ();
 sg13cmos5l_fill_1 FILLER_2_29 ();
 sg13cmos5l_decap_4 FILLER_2_34 ();
 sg13cmos5l_fill_2 FILLER_2_38 ();
 sg13cmos5l_decap_8 FILLER_2_44 ();
 sg13cmos5l_decap_8 FILLER_2_51 ();
 sg13cmos5l_decap_8 FILLER_2_58 ();
 sg13cmos5l_decap_8 FILLER_2_65 ();
 sg13cmos5l_decap_8 FILLER_2_7 ();
 sg13cmos5l_decap_8 FILLER_2_72 ();
 sg13cmos5l_decap_4 FILLER_2_79 ();
 sg13cmos5l_fill_2 FILLER_2_83 ();
 sg13cmos5l_fill_1 FILLER_2_89 ();
 sg13cmos5l_fill_2 FILLER_2_94 ();
 sg13cmos5l_fill_1 FILLER_2_96 ();
 sg13cmos5l_decap_8 FILLER_3_0 ();
 sg13cmos5l_fill_2 FILLER_3_104 ();
 sg13cmos5l_fill_1 FILLER_3_106 ();
 sg13cmos5l_fill_1 FILLER_3_11 ();
 sg13cmos5l_fill_2 FILLER_3_111 ();
 sg13cmos5l_decap_8 FILLER_3_121 ();
 sg13cmos5l_fill_2 FILLER_3_128 ();
 sg13cmos5l_fill_1 FILLER_3_130 ();
 sg13cmos5l_decap_8 FILLER_3_29 ();
 sg13cmos5l_decap_8 FILLER_3_36 ();
 sg13cmos5l_decap_8 FILLER_3_43 ();
 sg13cmos5l_decap_8 FILLER_3_50 ();
 sg13cmos5l_decap_8 FILLER_3_57 ();
 sg13cmos5l_decap_8 FILLER_3_64 ();
 sg13cmos5l_decap_4 FILLER_3_7 ();
 sg13cmos5l_decap_8 FILLER_3_71 ();
 sg13cmos5l_decap_8 FILLER_3_78 ();
 sg13cmos5l_decap_8 FILLER_3_85 ();
 sg13cmos5l_decap_4 FILLER_3_92 ();
 sg13cmos5l_decap_8 FILLER_4_0 ();
 sg13cmos5l_decap_4 FILLER_4_109 ();
 sg13cmos5l_decap_8 FILLER_4_121 ();
 sg13cmos5l_fill_2 FILLER_4_128 ();
 sg13cmos5l_fill_1 FILLER_4_130 ();
 sg13cmos5l_decap_8 FILLER_4_41 ();
 sg13cmos5l_decap_8 FILLER_4_48 ();
 sg13cmos5l_decap_8 FILLER_4_55 ();
 sg13cmos5l_decap_8 FILLER_4_62 ();
 sg13cmos5l_decap_8 FILLER_4_69 ();
 sg13cmos5l_decap_8 FILLER_4_76 ();
 sg13cmos5l_decap_8 FILLER_4_83 ();
 sg13cmos5l_decap_8 FILLER_4_90 ();
 sg13cmos5l_decap_4 FILLER_4_97 ();
 sg13cmos5l_decap_8 FILLER_5_0 ();
 sg13cmos5l_fill_1 FILLER_5_100 ();
 sg13cmos5l_decap_4 FILLER_5_109 ();
 sg13cmos5l_decap_4 FILLER_5_125 ();
 sg13cmos5l_fill_2 FILLER_5_129 ();
 sg13cmos5l_decap_8 FILLER_5_14 ();
 sg13cmos5l_decap_8 FILLER_5_21 ();
 sg13cmos5l_decap_8 FILLER_5_28 ();
 sg13cmos5l_decap_8 FILLER_5_35 ();
 sg13cmos5l_decap_8 FILLER_5_42 ();
 sg13cmos5l_decap_8 FILLER_5_49 ();
 sg13cmos5l_decap_8 FILLER_5_56 ();
 sg13cmos5l_decap_8 FILLER_5_63 ();
 sg13cmos5l_decap_8 FILLER_5_7 ();
 sg13cmos5l_decap_8 FILLER_5_70 ();
 sg13cmos5l_decap_8 FILLER_5_77 ();
 sg13cmos5l_decap_8 FILLER_5_84 ();
 sg13cmos5l_decap_8 FILLER_5_91 ();
 sg13cmos5l_fill_2 FILLER_5_98 ();
 sg13cmos5l_decap_8 FILLER_6_0 ();
 sg13cmos5l_fill_2 FILLER_6_110 ();
 sg13cmos5l_fill_1 FILLER_6_112 ();
 sg13cmos5l_decap_4 FILLER_6_125 ();
 sg13cmos5l_fill_2 FILLER_6_129 ();
 sg13cmos5l_decap_4 FILLER_6_14 ();
 sg13cmos5l_fill_2 FILLER_6_18 ();
 sg13cmos5l_decap_8 FILLER_6_24 ();
 sg13cmos5l_decap_8 FILLER_6_31 ();
 sg13cmos5l_decap_8 FILLER_6_38 ();
 sg13cmos5l_decap_8 FILLER_6_45 ();
 sg13cmos5l_decap_8 FILLER_6_52 ();
 sg13cmos5l_decap_8 FILLER_6_59 ();
 sg13cmos5l_decap_8 FILLER_6_66 ();
 sg13cmos5l_decap_8 FILLER_6_7 ();
 sg13cmos5l_decap_8 FILLER_6_73 ();
 sg13cmos5l_decap_8 FILLER_6_80 ();
 sg13cmos5l_decap_8 FILLER_6_91 ();
 sg13cmos5l_decap_4 FILLER_6_98 ();
 sg13cmos5l_decap_8 FILLER_7_0 ();
 sg13cmos5l_decap_8 FILLER_7_100 ();
 sg13cmos5l_decap_8 FILLER_7_107 ();
 sg13cmos5l_decap_8 FILLER_7_114 ();
 sg13cmos5l_decap_8 FILLER_7_121 ();
 sg13cmos5l_fill_2 FILLER_7_128 ();
 sg13cmos5l_fill_1 FILLER_7_130 ();
 sg13cmos5l_decap_8 FILLER_7_28 ();
 sg13cmos5l_decap_8 FILLER_7_35 ();
 sg13cmos5l_decap_4 FILLER_7_42 ();
 sg13cmos5l_fill_2 FILLER_7_46 ();
 sg13cmos5l_decap_4 FILLER_7_52 ();
 sg13cmos5l_fill_1 FILLER_7_56 ();
 sg13cmos5l_decap_8 FILLER_7_61 ();
 sg13cmos5l_fill_2 FILLER_7_68 ();
 sg13cmos5l_fill_1 FILLER_7_70 ();
 sg13cmos5l_fill_1 FILLER_7_75 ();
 sg13cmos5l_decap_8 FILLER_7_80 ();
 sg13cmos5l_decap_8 FILLER_7_87 ();
 sg13cmos5l_fill_2 FILLER_7_94 ();
 sg13cmos5l_decap_4 FILLER_8_0 ();
 sg13cmos5l_decap_8 FILLER_8_102 ();
 sg13cmos5l_decap_8 FILLER_8_109 ();
 sg13cmos5l_fill_1 FILLER_8_116 ();
 sg13cmos5l_decap_8 FILLER_8_121 ();
 sg13cmos5l_fill_2 FILLER_8_128 ();
 sg13cmos5l_fill_1 FILLER_8_130 ();
 sg13cmos5l_decap_8 FILLER_8_18 ();
 sg13cmos5l_decap_8 FILLER_8_25 ();
 sg13cmos5l_decap_8 FILLER_8_32 ();
 sg13cmos5l_decap_4 FILLER_8_39 ();
 sg13cmos5l_fill_2 FILLER_8_4 ();
 sg13cmos5l_fill_1 FILLER_8_43 ();
 sg13cmos5l_decap_4 FILLER_8_48 ();
 sg13cmos5l_fill_1 FILLER_8_52 ();
 sg13cmos5l_decap_8 FILLER_8_57 ();
 sg13cmos5l_fill_2 FILLER_8_64 ();
 sg13cmos5l_fill_1 FILLER_8_70 ();
 sg13cmos5l_decap_8 FILLER_8_75 ();
 sg13cmos5l_decap_4 FILLER_8_82 ();
 sg13cmos5l_fill_1 FILLER_8_86 ();
 sg13cmos5l_decap_8 FILLER_8_91 ();
 sg13cmos5l_decap_8 FILLER_9_0 ();
 sg13cmos5l_decap_4 FILLER_9_102 ();
 sg13cmos5l_fill_2 FILLER_9_106 ();
 sg13cmos5l_fill_1 FILLER_9_116 ();
 sg13cmos5l_decap_4 FILLER_9_125 ();
 sg13cmos5l_fill_2 FILLER_9_129 ();
 sg13cmos5l_decap_8 FILLER_9_14 ();
 sg13cmos5l_decap_8 FILLER_9_21 ();
 sg13cmos5l_decap_8 FILLER_9_28 ();
 sg13cmos5l_decap_8 FILLER_9_39 ();
 sg13cmos5l_decap_8 FILLER_9_46 ();
 sg13cmos5l_decap_8 FILLER_9_53 ();
 sg13cmos5l_decap_8 FILLER_9_60 ();
 sg13cmos5l_decap_8 FILLER_9_67 ();
 sg13cmos5l_decap_8 FILLER_9_7 ();
 sg13cmos5l_decap_8 FILLER_9_74 ();
 sg13cmos5l_decap_8 FILLER_9_81 ();
 sg13cmos5l_decap_8 FILLER_9_88 ();
 sg13cmos5l_decap_8 FILLER_9_95 ();
 sg13cmos5l_dlhq_1 _00_ (.D(FrameData[28]),
    .GATE(FrameStrobe[0]),
    .Q(\Inst_NW_term_ConfigMem.Inst_frame0_bit28.Q ));
 sg13cmos5l_dlhq_1 _01_ (.D(FrameData[29]),
    .GATE(FrameStrobe[0]),
    .Q(\Inst_NW_term_ConfigMem.Inst_frame0_bit29.Q ));
 sg13cmos5l_dlhq_1 _02_ (.D(FrameData[30]),
    .GATE(FrameStrobe[0]),
    .Q(\Inst_NW_term_ConfigMem.Inst_frame0_bit30.Q ));
 sg13cmos5l_dlhq_1 _03_ (.D(FrameData[31]),
    .GATE(FrameStrobe[0]),
    .Q(\Inst_NW_term_ConfigMem.Inst_frame0_bit31.Q ));
 sg13cmos5l_buf_1 _04_ (.A(FrameData[0]),
    .X(net1));
 sg13cmos5l_buf_1 _05_ (.A(FrameData[1]),
    .X(net12));
 sg13cmos5l_buf_1 _06_ (.A(FrameData[2]),
    .X(net23));
 sg13cmos5l_buf_1 _07_ (.A(FrameData[3]),
    .X(net26));
 sg13cmos5l_buf_1 _08_ (.A(FrameData[4]),
    .X(net27));
 sg13cmos5l_buf_1 _09_ (.A(FrameData[5]),
    .X(net28));
 sg13cmos5l_buf_1 _10_ (.A(FrameData[6]),
    .X(net29));
 sg13cmos5l_buf_1 _11_ (.A(FrameData[7]),
    .X(net30));
 sg13cmos5l_buf_1 _12_ (.A(FrameData[8]),
    .X(net31));
 sg13cmos5l_buf_1 _13_ (.A(FrameData[9]),
    .X(net32));
 sg13cmos5l_buf_1 _14_ (.A(FrameData[10]),
    .X(net2));
 sg13cmos5l_buf_1 _15_ (.A(FrameData[11]),
    .X(net3));
 sg13cmos5l_buf_1 _16_ (.A(FrameData[12]),
    .X(net4));
 sg13cmos5l_buf_1 _17_ (.A(FrameData[13]),
    .X(net5));
 sg13cmos5l_buf_1 _18_ (.A(FrameData[14]),
    .X(net6));
 sg13cmos5l_buf_1 _19_ (.A(FrameData[15]),
    .X(net7));
 sg13cmos5l_buf_1 _20_ (.A(FrameData[16]),
    .X(net8));
 sg13cmos5l_buf_1 _21_ (.A(FrameData[17]),
    .X(net9));
 sg13cmos5l_buf_1 _22_ (.A(FrameData[18]),
    .X(net10));
 sg13cmos5l_buf_1 _23_ (.A(FrameData[19]),
    .X(net11));
 sg13cmos5l_buf_1 _24_ (.A(FrameData[20]),
    .X(net13));
 sg13cmos5l_buf_1 _25_ (.A(FrameData[21]),
    .X(net14));
 sg13cmos5l_buf_1 _26_ (.A(FrameData[22]),
    .X(net15));
 sg13cmos5l_buf_1 _27_ (.A(FrameData[23]),
    .X(net16));
 sg13cmos5l_buf_1 _28_ (.A(FrameData[24]),
    .X(net17));
 sg13cmos5l_buf_1 _29_ (.A(FrameData[25]),
    .X(net18));
 sg13cmos5l_buf_1 _30_ (.A(FrameData[26]),
    .X(net19));
 sg13cmos5l_buf_1 _31_ (.A(FrameData[27]),
    .X(net20));
 sg13cmos5l_buf_1 _32_ (.A(FrameData[28]),
    .X(net21));
 sg13cmos5l_buf_1 _33_ (.A(FrameData[29]),
    .X(net22));
 sg13cmos5l_buf_1 _34_ (.A(FrameData[30]),
    .X(net24));
 sg13cmos5l_buf_1 _35_ (.A(FrameData[31]),
    .X(net25));
 sg13cmos5l_buf_1 _36_ (.A(FrameStrobe[0]),
    .X(net33));
 sg13cmos5l_buf_1 _37_ (.A(FrameStrobe[1]),
    .X(net44));
 sg13cmos5l_buf_1 _38_ (.A(FrameStrobe[2]),
    .X(net45));
 sg13cmos5l_buf_1 _39_ (.A(FrameStrobe[3]),
    .X(net46));
 sg13cmos5l_buf_1 _40_ (.A(FrameStrobe[4]),
    .X(net47));
 sg13cmos5l_buf_1 _41_ (.A(FrameStrobe[5]),
    .X(net48));
 sg13cmos5l_buf_1 _42_ (.A(FrameStrobe[6]),
    .X(net49));
 sg13cmos5l_buf_1 _43_ (.A(FrameStrobe[7]),
    .X(net50));
 sg13cmos5l_buf_1 _44_ (.A(FrameStrobe[8]),
    .X(net51));
 sg13cmos5l_buf_1 _45_ (.A(FrameStrobe[9]),
    .X(net52));
 sg13cmos5l_buf_1 _46_ (.A(FrameStrobe[10]),
    .X(net34));
 sg13cmos5l_buf_1 _47_ (.A(FrameStrobe[11]),
    .X(net35));
 sg13cmos5l_buf_1 _48_ (.A(FrameStrobe[12]),
    .X(net36));
 sg13cmos5l_buf_1 _49_ (.A(FrameStrobe[13]),
    .X(net37));
 sg13cmos5l_buf_1 _50_ (.A(FrameStrobe[14]),
    .X(net38));
 sg13cmos5l_buf_1 _51_ (.A(FrameStrobe[15]),
    .X(net39));
 sg13cmos5l_buf_1 _52_ (.A(FrameStrobe[16]),
    .X(net40));
 sg13cmos5l_buf_1 _53_ (.A(FrameStrobe[17]),
    .X(net41));
 sg13cmos5l_buf_1 _54_ (.A(FrameStrobe[18]),
    .X(net42));
 sg13cmos5l_buf_1 _55_ (.A(FrameStrobe[19]),
    .X(net43));
 sg13cmos5l_buf_1 _56_ (.A(\Inst_NW_term_ConfigMem.Inst_frame0_bit28.Q ),
    .X(net53));
 sg13cmos5l_buf_1 _57_ (.A(\Inst_NW_term_ConfigMem.Inst_frame0_bit29.Q ),
    .X(net54));
 sg13cmos5l_buf_1 _58_ (.A(\Inst_NW_term_ConfigMem.Inst_frame0_bit30.Q ),
    .X(net55));
 sg13cmos5l_buf_1 _59_ (.A(\Inst_NW_term_ConfigMem.Inst_frame0_bit31.Q ),
    .X(net56));
 sg13cmos5l_buf_1 output1 (.A(net1),
    .X(FrameData_O[0]));
 sg13cmos5l_buf_1 output10 (.A(net10),
    .X(FrameData_O[18]));
 sg13cmos5l_buf_1 output11 (.A(net11),
    .X(FrameData_O[19]));
 sg13cmos5l_buf_1 output12 (.A(net12),
    .X(FrameData_O[1]));
 sg13cmos5l_buf_1 output13 (.A(net13),
    .X(FrameData_O[20]));
 sg13cmos5l_buf_1 output14 (.A(net14),
    .X(FrameData_O[21]));
 sg13cmos5l_buf_1 output15 (.A(net15),
    .X(FrameData_O[22]));
 sg13cmos5l_buf_1 output16 (.A(net16),
    .X(FrameData_O[23]));
 sg13cmos5l_buf_1 output17 (.A(net17),
    .X(FrameData_O[24]));
 sg13cmos5l_buf_1 output18 (.A(net18),
    .X(FrameData_O[25]));
 sg13cmos5l_buf_1 output19 (.A(net19),
    .X(FrameData_O[26]));
 sg13cmos5l_buf_1 output2 (.A(net2),
    .X(FrameData_O[10]));
 sg13cmos5l_buf_1 output20 (.A(net20),
    .X(FrameData_O[27]));
 sg13cmos5l_buf_1 output21 (.A(net21),
    .X(FrameData_O[28]));
 sg13cmos5l_buf_1 output22 (.A(net22),
    .X(FrameData_O[29]));
 sg13cmos5l_buf_1 output23 (.A(net23),
    .X(FrameData_O[2]));
 sg13cmos5l_buf_1 output24 (.A(net24),
    .X(FrameData_O[30]));
 sg13cmos5l_buf_1 output25 (.A(net25),
    .X(FrameData_O[31]));
 sg13cmos5l_buf_1 output26 (.A(net26),
    .X(FrameData_O[3]));
 sg13cmos5l_buf_1 output27 (.A(net27),
    .X(FrameData_O[4]));
 sg13cmos5l_buf_1 output28 (.A(net28),
    .X(FrameData_O[5]));
 sg13cmos5l_buf_1 output29 (.A(net29),
    .X(FrameData_O[6]));
 sg13cmos5l_buf_1 output3 (.A(net3),
    .X(FrameData_O[11]));
 sg13cmos5l_buf_1 output30 (.A(net30),
    .X(FrameData_O[7]));
 sg13cmos5l_buf_1 output31 (.A(net31),
    .X(FrameData_O[8]));
 sg13cmos5l_buf_1 output32 (.A(net32),
    .X(FrameData_O[9]));
 sg13cmos5l_buf_1 output33 (.A(net33),
    .X(FrameStrobe_O[0]));
 sg13cmos5l_buf_1 output34 (.A(net34),
    .X(FrameStrobe_O[10]));
 sg13cmos5l_buf_1 output35 (.A(net35),
    .X(FrameStrobe_O[11]));
 sg13cmos5l_buf_1 output36 (.A(net36),
    .X(FrameStrobe_O[12]));
 sg13cmos5l_buf_1 output37 (.A(net37),
    .X(FrameStrobe_O[13]));
 sg13cmos5l_buf_1 output38 (.A(net38),
    .X(FrameStrobe_O[14]));
 sg13cmos5l_buf_1 output39 (.A(net39),
    .X(FrameStrobe_O[15]));
 sg13cmos5l_buf_1 output4 (.A(net4),
    .X(FrameData_O[12]));
 sg13cmos5l_buf_1 output40 (.A(net40),
    .X(FrameStrobe_O[16]));
 sg13cmos5l_buf_1 output41 (.A(net41),
    .X(FrameStrobe_O[17]));
 sg13cmos5l_buf_1 output42 (.A(net42),
    .X(FrameStrobe_O[18]));
 sg13cmos5l_buf_1 output43 (.A(net43),
    .X(FrameStrobe_O[19]));
 sg13cmos5l_buf_1 output44 (.A(net44),
    .X(FrameStrobe_O[1]));
 sg13cmos5l_buf_1 output45 (.A(net45),
    .X(FrameStrobe_O[2]));
 sg13cmos5l_buf_1 output46 (.A(net46),
    .X(FrameStrobe_O[3]));
 sg13cmos5l_buf_1 output47 (.A(net47),
    .X(FrameStrobe_O[4]));
 sg13cmos5l_buf_1 output48 (.A(net48),
    .X(FrameStrobe_O[5]));
 sg13cmos5l_buf_1 output49 (.A(net49),
    .X(FrameStrobe_O[6]));
 sg13cmos5l_buf_1 output5 (.A(net5),
    .X(FrameData_O[13]));
 sg13cmos5l_buf_1 output50 (.A(net50),
    .X(FrameStrobe_O[7]));
 sg13cmos5l_buf_1 output51 (.A(net51),
    .X(FrameStrobe_O[8]));
 sg13cmos5l_buf_1 output52 (.A(net52),
    .X(FrameStrobe_O[9]));
 sg13cmos5l_buf_1 output53 (.A(net53),
    .X(S_GBUF_FEED_BEG[0]));
 sg13cmos5l_buf_1 output54 (.A(net54),
    .X(S_GBUF_FEED_BEG[1]));
 sg13cmos5l_buf_1 output55 (.A(net55),
    .X(S_GBUF_FEED_BEG[2]));
 sg13cmos5l_buf_1 output56 (.A(net56),
    .X(S_GBUF_FEED_BEG[3]));
 sg13cmos5l_buf_1 output6 (.A(net6),
    .X(FrameData_O[14]));
 sg13cmos5l_buf_1 output7 (.A(net7),
    .X(FrameData_O[15]));
 sg13cmos5l_buf_1 output8 (.A(net8),
    .X(FrameData_O[16]));
 sg13cmos5l_buf_1 output9 (.A(net9),
    .X(FrameData_O[17]));
endmodule
