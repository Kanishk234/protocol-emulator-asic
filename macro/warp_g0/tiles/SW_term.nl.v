module SW_term (SYS_RESET_RESET_top,
    E_GBUF_BEG,
    FrameData,
    FrameData_O,
    FrameStrobe,
    FrameStrobe_O,
    N_GBUF_BEG,
    S_GBUF_FEED_END,
    W_GBUF_FEED_END);
 input SYS_RESET_RESET_top;
 output [3:0] E_GBUF_BEG;
 input [31:0] FrameData;
 output [31:0] FrameData_O;
 input [19:0] FrameStrobe;
 output [19:0] FrameStrobe_O;
 output [3:0] N_GBUF_BEG;
 input [3:0] S_GBUF_FEED_END;
 input [3:0] W_GBUF_FEED_END;

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
 wire net53;
 wire net54;
 wire net55;
 wire net56;
 wire GBUF_A_OUT;
 wire GBUF_B_OUT;
 wire GBUF_C_OUT;
 wire GBUF_D_OUT;
 wire \Inst_GBUF_A_GBUF.ConfigBits[0] ;
 wire \Inst_GBUF_B_GBUF.ConfigBits[0] ;
 wire \Inst_GBUF_C_GBUF.ConfigBits[0] ;
 wire \Inst_GBUF_D_GBUF.ConfigBits[0] ;
 wire \Inst_SW_term_ConfigMem.Inst_frame0_bit16.Q ;
 wire \Inst_SW_term_ConfigMem.Inst_frame0_bit17.Q ;
 wire \Inst_SW_term_ConfigMem.Inst_frame0_bit18.Q ;
 wire \Inst_SW_term_ConfigMem.Inst_frame0_bit19.Q ;
 wire \Inst_SW_term_ConfigMem.Inst_frame0_bit20.Q ;
 wire \Inst_SW_term_ConfigMem.Inst_frame0_bit21.Q ;
 wire \Inst_SW_term_ConfigMem.Inst_frame0_bit22.Q ;
 wire \Inst_SW_term_ConfigMem.Inst_frame0_bit23.Q ;
 wire \Inst_SW_term_ConfigMem.Inst_frame0_bit24.Q ;
 wire \Inst_SW_term_ConfigMem.Inst_frame0_bit25.Q ;
 wire \Inst_SW_term_ConfigMem.Inst_frame0_bit26.Q ;
 wire \Inst_SW_term_ConfigMem.Inst_frame0_bit27.Q ;
 wire \Inst_SW_term_ConfigMem.Inst_frame0_bit28.Q ;
 wire \Inst_SW_term_ConfigMem.Inst_frame0_bit29.Q ;
 wire \Inst_SW_term_ConfigMem.Inst_frame0_bit30.Q ;
 wire \Inst_SW_term_ConfigMem.Inst_frame0_bit31.Q ;
 wire net57;
 wire net58;
 wire net59;
 wire net60;
 wire _000_;
 wire _001_;
 wire _002_;
 wire _003_;
 wire _004_;
 wire _005_;
 wire _006_;
 wire _007_;
 wire _008_;
 wire _009_;
 wire _010_;
 wire _011_;
 wire _012_;
 wire _013_;
 wire _014_;
 wire _015_;
 wire _016_;
 wire _017_;
 wire _018_;
 wire _019_;
 wire _020_;
 wire _021_;
 wire _022_;
 wire _023_;
 wire _024_;
 wire _025_;
 wire _026_;
 wire _027_;
 wire _028_;
 wire _029_;
 wire _030_;
 wire _031_;
 wire _032_;
 wire _033_;
 wire _034_;
 wire _035_;
 wire _036_;
 wire _037_;
 wire _038_;
 wire _039_;
 wire _040_;
 wire _041_;
 wire _042_;
 wire _043_;
 wire _044_;
 wire _045_;
 wire _046_;
 wire _047_;
 wire _048_;
 wire _049_;
 wire _050_;

 sg13cmos5l_decap_8 FILLER_0_0 ();
 sg13cmos5l_fill_1 FILLER_0_104 ();
 sg13cmos5l_fill_2 FILLER_0_109 ();
 sg13cmos5l_decap_8 FILLER_0_14 ();
 sg13cmos5l_decap_8 FILLER_0_21 ();
 sg13cmos5l_decap_8 FILLER_0_28 ();
 sg13cmos5l_decap_8 FILLER_0_35 ();
 sg13cmos5l_decap_8 FILLER_0_42 ();
 sg13cmos5l_fill_2 FILLER_0_49 ();
 sg13cmos5l_fill_1 FILLER_0_51 ();
 sg13cmos5l_decap_8 FILLER_0_56 ();
 sg13cmos5l_decap_8 FILLER_0_63 ();
 sg13cmos5l_fill_2 FILLER_0_7 ();
 sg13cmos5l_fill_2 FILLER_0_70 ();
 sg13cmos5l_decap_8 FILLER_0_76 ();
 sg13cmos5l_decap_8 FILLER_0_83 ();
 sg13cmos5l_fill_1 FILLER_0_9 ();
 sg13cmos5l_decap_8 FILLER_0_90 ();
 sg13cmos5l_decap_8 FILLER_0_97 ();
 sg13cmos5l_decap_4 FILLER_10_0 ();
 sg13cmos5l_decap_4 FILLER_10_100 ();
 sg13cmos5l_fill_1 FILLER_10_104 ();
 sg13cmos5l_decap_4 FILLER_10_125 ();
 sg13cmos5l_fill_2 FILLER_10_129 ();
 sg13cmos5l_fill_2 FILLER_10_21 ();
 sg13cmos5l_fill_1 FILLER_10_44 ();
 sg13cmos5l_fill_2 FILLER_10_49 ();
 sg13cmos5l_fill_1 FILLER_10_72 ();
 sg13cmos5l_fill_1 FILLER_10_95 ();
 sg13cmos5l_decap_8 FILLER_11_0 ();
 sg13cmos5l_fill_1 FILLER_11_104 ();
 sg13cmos5l_decap_4 FILLER_11_125 ();
 sg13cmos5l_fill_2 FILLER_11_129 ();
 sg13cmos5l_fill_2 FILLER_11_25 ();
 sg13cmos5l_fill_1 FILLER_11_27 ();
 sg13cmos5l_fill_2 FILLER_11_7 ();
 sg13cmos5l_fill_1 FILLER_11_91 ();
 sg13cmos5l_decap_8 FILLER_12_0 ();
 sg13cmos5l_fill_2 FILLER_12_106 ();
 sg13cmos5l_fill_1 FILLER_12_108 ();
 sg13cmos5l_decap_4 FILLER_12_113 ();
 sg13cmos5l_decap_8 FILLER_12_121 ();
 sg13cmos5l_fill_2 FILLER_12_128 ();
 sg13cmos5l_fill_1 FILLER_12_130 ();
 sg13cmos5l_decap_8 FILLER_12_14 ();
 sg13cmos5l_decap_8 FILLER_12_21 ();
 sg13cmos5l_decap_8 FILLER_12_28 ();
 sg13cmos5l_fill_2 FILLER_12_35 ();
 sg13cmos5l_decap_8 FILLER_12_41 ();
 sg13cmos5l_fill_1 FILLER_12_48 ();
 sg13cmos5l_fill_1 FILLER_12_53 ();
 sg13cmos5l_fill_1 FILLER_12_58 ();
 sg13cmos5l_decap_8 FILLER_12_63 ();
 sg13cmos5l_decap_8 FILLER_12_7 ();
 sg13cmos5l_decap_8 FILLER_12_70 ();
 sg13cmos5l_decap_4 FILLER_12_77 ();
 sg13cmos5l_fill_1 FILLER_12_81 ();
 sg13cmos5l_decap_8 FILLER_12_85 ();
 sg13cmos5l_decap_8 FILLER_12_92 ();
 sg13cmos5l_decap_8 FILLER_12_99 ();
 sg13cmos5l_fill_2 FILLER_1_0 ();
 sg13cmos5l_fill_2 FILLER_1_114 ();
 sg13cmos5l_fill_1 FILLER_1_116 ();
 sg13cmos5l_fill_2 FILLER_1_129 ();
 sg13cmos5l_decap_8 FILLER_1_18 ();
 sg13cmos5l_fill_2 FILLER_1_49 ();
 sg13cmos5l_fill_1 FILLER_1_51 ();
 sg13cmos5l_fill_1 FILLER_1_72 ();
 sg13cmos5l_fill_1 FILLER_1_85 ();
 sg13cmos5l_decap_4 FILLER_2_0 ();
 sg13cmos5l_fill_2 FILLER_2_129 ();
 sg13cmos5l_decap_8 FILLER_2_18 ();
 sg13cmos5l_decap_4 FILLER_2_25 ();
 sg13cmos5l_fill_2 FILLER_2_29 ();
 sg13cmos5l_fill_2 FILLER_2_4 ();
 sg13cmos5l_decap_8 FILLER_2_54 ();
 sg13cmos5l_decap_8 FILLER_2_61 ();
 sg13cmos5l_decap_4 FILLER_2_68 ();
 sg13cmos5l_fill_1 FILLER_2_72 ();
 sg13cmos5l_decap_8 FILLER_2_77 ();
 sg13cmos5l_decap_8 FILLER_2_84 ();
 sg13cmos5l_decap_8 FILLER_2_91 ();
 sg13cmos5l_decap_8 FILLER_2_98 ();
 sg13cmos5l_fill_2 FILLER_3_114 ();
 sg13cmos5l_fill_1 FILLER_3_116 ();
 sg13cmos5l_fill_2 FILLER_3_129 ();
 sg13cmos5l_decap_8 FILLER_3_57 ();
 sg13cmos5l_decap_4 FILLER_3_64 ();
 sg13cmos5l_fill_1 FILLER_3_68 ();
 sg13cmos5l_decap_4 FILLER_3_89 ();
 sg13cmos5l_fill_1 FILLER_3_93 ();
 sg13cmos5l_decap_4 FILLER_3_98 ();
 sg13cmos5l_fill_2 FILLER_4_115 ();
 sg13cmos5l_fill_2 FILLER_4_129 ();
 sg13cmos5l_fill_1 FILLER_4_37 ();
 sg13cmos5l_decap_8 FILLER_4_53 ();
 sg13cmos5l_fill_1 FILLER_4_60 ();
 sg13cmos5l_fill_2 FILLER_4_76 ();
 sg13cmos5l_decap_4 FILLER_5_0 ();
 sg13cmos5l_fill_1 FILLER_5_103 ();
 sg13cmos5l_fill_1 FILLER_5_116 ();
 sg13cmos5l_fill_2 FILLER_5_129 ();
 sg13cmos5l_fill_2 FILLER_5_38 ();
 sg13cmos5l_fill_2 FILLER_5_57 ();
 sg13cmos5l_fill_1 FILLER_5_59 ();
 sg13cmos5l_decap_8 FILLER_5_92 ();
 sg13cmos5l_decap_4 FILLER_5_99 ();
 sg13cmos5l_decap_8 FILLER_6_0 ();
 sg13cmos5l_fill_1 FILLER_6_116 ();
 sg13cmos5l_fill_2 FILLER_6_129 ();
 sg13cmos5l_fill_2 FILLER_6_25 ();
 sg13cmos5l_fill_1 FILLER_6_27 ();
 sg13cmos5l_fill_1 FILLER_6_49 ();
 sg13cmos5l_fill_1 FILLER_6_7 ();
 sg13cmos5l_fill_2 FILLER_6_71 ();
 sg13cmos5l_decap_8 FILLER_6_90 ();
 sg13cmos5l_decap_8 FILLER_6_97 ();
 sg13cmos5l_decap_8 FILLER_7_0 ();
 sg13cmos5l_fill_2 FILLER_7_101 ();
 sg13cmos5l_fill_1 FILLER_7_103 ();
 sg13cmos5l_fill_1 FILLER_7_116 ();
 sg13cmos5l_decap_4 FILLER_7_125 ();
 sg13cmos5l_fill_2 FILLER_7_129 ();
 sg13cmos5l_fill_1 FILLER_7_14 ();
 sg13cmos5l_decap_4 FILLER_7_32 ();
 sg13cmos5l_fill_1 FILLER_7_36 ();
 sg13cmos5l_decap_8 FILLER_7_51 ();
 sg13cmos5l_decap_8 FILLER_7_7 ();
 sg13cmos5l_fill_2 FILLER_7_75 ();
 sg13cmos5l_decap_8 FILLER_7_94 ();
 sg13cmos5l_decap_4 FILLER_8_0 ();
 sg13cmos5l_fill_1 FILLER_8_103 ();
 sg13cmos5l_fill_1 FILLER_8_116 ();
 sg13cmos5l_fill_2 FILLER_8_129 ();
 sg13cmos5l_fill_2 FILLER_8_23 ();
 sg13cmos5l_fill_1 FILLER_8_25 ();
 sg13cmos5l_fill_2 FILLER_8_4 ();
 sg13cmos5l_decap_8 FILLER_8_57 ();
 sg13cmos5l_decap_4 FILLER_8_64 ();
 sg13cmos5l_fill_2 FILLER_8_68 ();
 sg13cmos5l_decap_8 FILLER_8_84 ();
 sg13cmos5l_decap_4 FILLER_8_99 ();
 sg13cmos5l_decap_4 FILLER_9_0 ();
 sg13cmos5l_fill_1 FILLER_9_104 ();
 sg13cmos5l_decap_4 FILLER_9_125 ();
 sg13cmos5l_fill_2 FILLER_9_129 ();
 sg13cmos5l_fill_1 FILLER_9_21 ();
 sg13cmos5l_decap_4 FILLER_9_28 ();
 sg13cmos5l_fill_1 FILLER_9_32 ();
 sg13cmos5l_decap_8 FILLER_9_51 ();
 sg13cmos5l_fill_2 FILLER_9_58 ();
 sg13cmos5l_fill_1 FILLER_9_60 ();
 sg13cmos5l_fill_1 FILLER_9_80 ();
 sg13cmos5l_decap_8 FILLER_9_97 ();
 sg13cmos5l_inv_1 _051_ (.Y(_000_),
    .A(\Inst_SW_term_ConfigMem.Inst_frame0_bit22.Q ));
 sg13cmos5l_inv_1 _052_ (.Y(_001_),
    .A(\Inst_SW_term_ConfigMem.Inst_frame0_bit26.Q ));
 sg13cmos5l_inv_1 _053_ (.Y(_002_),
    .A(\Inst_SW_term_ConfigMem.Inst_frame0_bit30.Q ));
 sg13cmos5l_nor2b_1 _054_ (.A(W_GBUF_FEED_END[1]),
    .B_N(\Inst_SW_term_ConfigMem.Inst_frame0_bit16.Q ),
    .Y(_003_));
 sg13cmos5l_nor2_1 _055_ (.A(\Inst_SW_term_ConfigMem.Inst_frame0_bit16.Q ),
    .B(W_GBUF_FEED_END[0]),
    .Y(_004_));
 sg13cmos5l_nor2b_1 _056_ (.A(W_GBUF_FEED_END[3]),
    .B_N(\Inst_SW_term_ConfigMem.Inst_frame0_bit16.Q ),
    .Y(_005_));
 sg13cmos5l_mux4_1 _057_ (.S0(\Inst_SW_term_ConfigMem.Inst_frame0_bit16.Q ),
    .A0(S_GBUF_FEED_END[0]),
    .A1(S_GBUF_FEED_END[1]),
    .A2(S_GBUF_FEED_END[2]),
    .A3(S_GBUF_FEED_END[3]),
    .S1(\Inst_SW_term_ConfigMem.Inst_frame0_bit17.Q ),
    .X(_006_));
 sg13cmos5l_or2_1 _058_ (.X(_007_),
    .B(_006_),
    .A(\Inst_SW_term_ConfigMem.Inst_frame0_bit18.Q ));
 sg13cmos5l_nor3_1 _059_ (.A(\Inst_SW_term_ConfigMem.Inst_frame0_bit17.Q ),
    .B(_003_),
    .C(_004_),
    .Y(_008_));
 sg13cmos5l_o21ai_1 _060_ (.B1(\Inst_SW_term_ConfigMem.Inst_frame0_bit17.Q ),
    .Y(_009_),
    .A1(\Inst_SW_term_ConfigMem.Inst_frame0_bit16.Q ),
    .A2(W_GBUF_FEED_END[2]));
 sg13cmos5l_o21ai_1 _061_ (.B1(\Inst_SW_term_ConfigMem.Inst_frame0_bit18.Q ),
    .Y(_010_),
    .A1(_005_),
    .A2(_009_));
 sg13cmos5l_o21ai_1 _062_ (.B1(_007_),
    .Y(_011_),
    .A1(_008_),
    .A2(_010_));
 sg13cmos5l_nor3_1 _063_ (.A(\Inst_SW_term_ConfigMem.Inst_frame0_bit18.Q ),
    .B(\Inst_SW_term_ConfigMem.Inst_frame0_bit16.Q ),
    .C(\Inst_SW_term_ConfigMem.Inst_frame0_bit17.Q ),
    .Y(_012_));
 sg13cmos5l_nand3_1 _064_ (.B(\Inst_SW_term_ConfigMem.Inst_frame0_bit19.Q ),
    .C(_012_),
    .A(SYS_RESET_RESET_top),
    .Y(_013_));
 sg13cmos5l_o21ai_1 _065_ (.B1(_013_),
    .Y(_014_),
    .A1(\Inst_SW_term_ConfigMem.Inst_frame0_bit19.Q ),
    .A2(_011_));
 sg13cmos5l_xor2_1 _066_ (.B(_014_),
    .A(\Inst_GBUF_A_GBUF.ConfigBits[0] ),
    .X(GBUF_A_OUT));
 sg13cmos5l_nor2b_1 _067_ (.A(W_GBUF_FEED_END[1]),
    .B_N(\Inst_SW_term_ConfigMem.Inst_frame0_bit20.Q ),
    .Y(_015_));
 sg13cmos5l_nor2_1 _068_ (.A(W_GBUF_FEED_END[0]),
    .B(\Inst_SW_term_ConfigMem.Inst_frame0_bit20.Q ),
    .Y(_016_));
 sg13cmos5l_nor2b_1 _069_ (.A(W_GBUF_FEED_END[3]),
    .B_N(\Inst_SW_term_ConfigMem.Inst_frame0_bit20.Q ),
    .Y(_017_));
 sg13cmos5l_mux4_1 _070_ (.S0(\Inst_SW_term_ConfigMem.Inst_frame0_bit20.Q ),
    .A0(S_GBUF_FEED_END[0]),
    .A1(S_GBUF_FEED_END[1]),
    .A2(S_GBUF_FEED_END[2]),
    .A3(S_GBUF_FEED_END[3]),
    .S1(\Inst_SW_term_ConfigMem.Inst_frame0_bit21.Q ),
    .X(_018_));
 sg13cmos5l_nand2b_1 _071_ (.Y(_019_),
    .B(_000_),
    .A_N(_018_));
 sg13cmos5l_nor3_1 _072_ (.A(\Inst_SW_term_ConfigMem.Inst_frame0_bit21.Q ),
    .B(_015_),
    .C(_016_),
    .Y(_020_));
 sg13cmos5l_o21ai_1 _073_ (.B1(\Inst_SW_term_ConfigMem.Inst_frame0_bit21.Q ),
    .Y(_021_),
    .A1(W_GBUF_FEED_END[2]),
    .A2(\Inst_SW_term_ConfigMem.Inst_frame0_bit20.Q ));
 sg13cmos5l_o21ai_1 _074_ (.B1(\Inst_SW_term_ConfigMem.Inst_frame0_bit22.Q ),
    .Y(_022_),
    .A1(_017_),
    .A2(_021_));
 sg13cmos5l_o21ai_1 _075_ (.B1(_019_),
    .Y(_023_),
    .A1(_020_),
    .A2(_022_));
 sg13cmos5l_nor2_1 _076_ (.A(\Inst_SW_term_ConfigMem.Inst_frame0_bit20.Q ),
    .B(\Inst_SW_term_ConfigMem.Inst_frame0_bit21.Q ),
    .Y(_024_));
 sg13cmos5l_nand4_1 _077_ (.B(_000_),
    .C(\Inst_SW_term_ConfigMem.Inst_frame0_bit23.Q ),
    .A(SYS_RESET_RESET_top),
    .Y(_025_),
    .D(_024_));
 sg13cmos5l_o21ai_1 _078_ (.B1(_025_),
    .Y(_026_),
    .A1(\Inst_SW_term_ConfigMem.Inst_frame0_bit23.Q ),
    .A2(_023_));
 sg13cmos5l_xor2_1 _079_ (.B(_026_),
    .A(\Inst_GBUF_B_GBUF.ConfigBits[0] ),
    .X(GBUF_B_OUT));
 sg13cmos5l_nor2b_1 _080_ (.A(W_GBUF_FEED_END[1]),
    .B_N(\Inst_SW_term_ConfigMem.Inst_frame0_bit24.Q ),
    .Y(_027_));
 sg13cmos5l_nor2_1 _081_ (.A(W_GBUF_FEED_END[0]),
    .B(\Inst_SW_term_ConfigMem.Inst_frame0_bit24.Q ),
    .Y(_028_));
 sg13cmos5l_nor2b_1 _082_ (.A(W_GBUF_FEED_END[3]),
    .B_N(\Inst_SW_term_ConfigMem.Inst_frame0_bit24.Q ),
    .Y(_029_));
 sg13cmos5l_mux4_1 _083_ (.S0(\Inst_SW_term_ConfigMem.Inst_frame0_bit24.Q ),
    .A0(S_GBUF_FEED_END[0]),
    .A1(S_GBUF_FEED_END[1]),
    .A2(S_GBUF_FEED_END[2]),
    .A3(S_GBUF_FEED_END[3]),
    .S1(\Inst_SW_term_ConfigMem.Inst_frame0_bit25.Q ),
    .X(_030_));
 sg13cmos5l_nand2b_1 _084_ (.Y(_031_),
    .B(_001_),
    .A_N(_030_));
 sg13cmos5l_nor3_1 _085_ (.A(\Inst_SW_term_ConfigMem.Inst_frame0_bit25.Q ),
    .B(_027_),
    .C(_028_),
    .Y(_032_));
 sg13cmos5l_o21ai_1 _086_ (.B1(\Inst_SW_term_ConfigMem.Inst_frame0_bit25.Q ),
    .Y(_033_),
    .A1(W_GBUF_FEED_END[2]),
    .A2(\Inst_SW_term_ConfigMem.Inst_frame0_bit24.Q ));
 sg13cmos5l_o21ai_1 _087_ (.B1(\Inst_SW_term_ConfigMem.Inst_frame0_bit26.Q ),
    .Y(_034_),
    .A1(_029_),
    .A2(_033_));
 sg13cmos5l_o21ai_1 _088_ (.B1(_031_),
    .Y(_035_),
    .A1(_032_),
    .A2(_034_));
 sg13cmos5l_nor2_1 _089_ (.A(\Inst_SW_term_ConfigMem.Inst_frame0_bit24.Q ),
    .B(\Inst_SW_term_ConfigMem.Inst_frame0_bit25.Q ),
    .Y(_036_));
 sg13cmos5l_nand4_1 _090_ (.B(_001_),
    .C(\Inst_SW_term_ConfigMem.Inst_frame0_bit27.Q ),
    .A(SYS_RESET_RESET_top),
    .Y(_037_),
    .D(_036_));
 sg13cmos5l_o21ai_1 _091_ (.B1(_037_),
    .Y(_038_),
    .A1(\Inst_SW_term_ConfigMem.Inst_frame0_bit27.Q ),
    .A2(_035_));
 sg13cmos5l_xor2_1 _092_ (.B(_038_),
    .A(\Inst_GBUF_C_GBUF.ConfigBits[0] ),
    .X(GBUF_C_OUT));
 sg13cmos5l_nor2b_1 _093_ (.A(W_GBUF_FEED_END[1]),
    .B_N(\Inst_SW_term_ConfigMem.Inst_frame0_bit28.Q ),
    .Y(_039_));
 sg13cmos5l_nor2_1 _094_ (.A(W_GBUF_FEED_END[0]),
    .B(\Inst_SW_term_ConfigMem.Inst_frame0_bit28.Q ),
    .Y(_040_));
 sg13cmos5l_nor2b_1 _095_ (.A(W_GBUF_FEED_END[3]),
    .B_N(\Inst_SW_term_ConfigMem.Inst_frame0_bit28.Q ),
    .Y(_041_));
 sg13cmos5l_mux4_1 _096_ (.S0(\Inst_SW_term_ConfigMem.Inst_frame0_bit28.Q ),
    .A0(S_GBUF_FEED_END[0]),
    .A1(S_GBUF_FEED_END[1]),
    .A2(S_GBUF_FEED_END[2]),
    .A3(S_GBUF_FEED_END[3]),
    .S1(\Inst_SW_term_ConfigMem.Inst_frame0_bit29.Q ),
    .X(_042_));
 sg13cmos5l_nand2b_1 _097_ (.Y(_043_),
    .B(_002_),
    .A_N(_042_));
 sg13cmos5l_nor3_1 _098_ (.A(\Inst_SW_term_ConfigMem.Inst_frame0_bit29.Q ),
    .B(_039_),
    .C(_040_),
    .Y(_044_));
 sg13cmos5l_o21ai_1 _099_ (.B1(\Inst_SW_term_ConfigMem.Inst_frame0_bit29.Q ),
    .Y(_045_),
    .A1(W_GBUF_FEED_END[2]),
    .A2(\Inst_SW_term_ConfigMem.Inst_frame0_bit28.Q ));
 sg13cmos5l_o21ai_1 _100_ (.B1(\Inst_SW_term_ConfigMem.Inst_frame0_bit30.Q ),
    .Y(_046_),
    .A1(_041_),
    .A2(_045_));
 sg13cmos5l_o21ai_1 _101_ (.B1(_043_),
    .Y(_047_),
    .A1(_044_),
    .A2(_046_));
 sg13cmos5l_nor2_1 _102_ (.A(\Inst_SW_term_ConfigMem.Inst_frame0_bit28.Q ),
    .B(\Inst_SW_term_ConfigMem.Inst_frame0_bit29.Q ),
    .Y(_048_));
 sg13cmos5l_nand4_1 _103_ (.B(_002_),
    .C(\Inst_SW_term_ConfigMem.Inst_frame0_bit31.Q ),
    .A(SYS_RESET_RESET_top),
    .Y(_049_),
    .D(_048_));
 sg13cmos5l_o21ai_1 _104_ (.B1(_049_),
    .Y(_050_),
    .A1(\Inst_SW_term_ConfigMem.Inst_frame0_bit31.Q ),
    .A2(_047_));
 sg13cmos5l_xor2_1 _105_ (.B(_050_),
    .A(\Inst_GBUF_D_GBUF.ConfigBits[0] ),
    .X(GBUF_D_OUT));
 sg13cmos5l_dlhq_1 _106_ (.D(FrameData[12]),
    .GATE(FrameStrobe[0]),
    .Q(\Inst_GBUF_A_GBUF.ConfigBits[0] ));
 sg13cmos5l_dlhq_1 _107_ (.D(FrameData[13]),
    .GATE(FrameStrobe[0]),
    .Q(\Inst_GBUF_B_GBUF.ConfigBits[0] ));
 sg13cmos5l_dlhq_1 _108_ (.D(FrameData[14]),
    .GATE(FrameStrobe[0]),
    .Q(\Inst_GBUF_C_GBUF.ConfigBits[0] ));
 sg13cmos5l_dlhq_1 _109_ (.D(FrameData[15]),
    .GATE(FrameStrobe[0]),
    .Q(\Inst_GBUF_D_GBUF.ConfigBits[0] ));
 sg13cmos5l_dlhq_1 _110_ (.D(FrameData[16]),
    .GATE(FrameStrobe[0]),
    .Q(\Inst_SW_term_ConfigMem.Inst_frame0_bit16.Q ));
 sg13cmos5l_dlhq_1 _111_ (.D(FrameData[17]),
    .GATE(FrameStrobe[0]),
    .Q(\Inst_SW_term_ConfigMem.Inst_frame0_bit17.Q ));
 sg13cmos5l_dlhq_1 _112_ (.D(FrameData[18]),
    .GATE(FrameStrobe[0]),
    .Q(\Inst_SW_term_ConfigMem.Inst_frame0_bit18.Q ));
 sg13cmos5l_dlhq_1 _113_ (.D(FrameData[19]),
    .GATE(FrameStrobe[0]),
    .Q(\Inst_SW_term_ConfigMem.Inst_frame0_bit19.Q ));
 sg13cmos5l_dlhq_1 _114_ (.D(FrameData[20]),
    .GATE(FrameStrobe[0]),
    .Q(\Inst_SW_term_ConfigMem.Inst_frame0_bit20.Q ));
 sg13cmos5l_dlhq_1 _115_ (.D(FrameData[21]),
    .GATE(FrameStrobe[0]),
    .Q(\Inst_SW_term_ConfigMem.Inst_frame0_bit21.Q ));
 sg13cmos5l_dlhq_1 _116_ (.D(FrameData[22]),
    .GATE(FrameStrobe[0]),
    .Q(\Inst_SW_term_ConfigMem.Inst_frame0_bit22.Q ));
 sg13cmos5l_dlhq_1 _117_ (.D(FrameData[23]),
    .GATE(FrameStrobe[0]),
    .Q(\Inst_SW_term_ConfigMem.Inst_frame0_bit23.Q ));
 sg13cmos5l_dlhq_1 _118_ (.D(FrameData[24]),
    .GATE(FrameStrobe[0]),
    .Q(\Inst_SW_term_ConfigMem.Inst_frame0_bit24.Q ));
 sg13cmos5l_dlhq_1 _119_ (.D(FrameData[25]),
    .GATE(FrameStrobe[0]),
    .Q(\Inst_SW_term_ConfigMem.Inst_frame0_bit25.Q ));
 sg13cmos5l_dlhq_1 _120_ (.D(FrameData[26]),
    .GATE(FrameStrobe[0]),
    .Q(\Inst_SW_term_ConfigMem.Inst_frame0_bit26.Q ));
 sg13cmos5l_dlhq_1 _121_ (.D(FrameData[27]),
    .GATE(FrameStrobe[0]),
    .Q(\Inst_SW_term_ConfigMem.Inst_frame0_bit27.Q ));
 sg13cmos5l_dlhq_1 _122_ (.D(FrameData[28]),
    .GATE(FrameStrobe[0]),
    .Q(\Inst_SW_term_ConfigMem.Inst_frame0_bit28.Q ));
 sg13cmos5l_dlhq_1 _123_ (.D(FrameData[29]),
    .GATE(FrameStrobe[0]),
    .Q(\Inst_SW_term_ConfigMem.Inst_frame0_bit29.Q ));
 sg13cmos5l_dlhq_1 _124_ (.D(FrameData[30]),
    .GATE(FrameStrobe[0]),
    .Q(\Inst_SW_term_ConfigMem.Inst_frame0_bit30.Q ));
 sg13cmos5l_dlhq_1 _125_ (.D(FrameData[31]),
    .GATE(FrameStrobe[0]),
    .Q(\Inst_SW_term_ConfigMem.Inst_frame0_bit31.Q ));
 sg13cmos5l_buf_1 _126_ (.A(GBUF_A_OUT),
    .X(net1));
 sg13cmos5l_buf_1 _127_ (.A(GBUF_B_OUT),
    .X(net2));
 sg13cmos5l_buf_1 _128_ (.A(GBUF_C_OUT),
    .X(net3));
 sg13cmos5l_buf_1 _129_ (.A(GBUF_D_OUT),
    .X(net4));
 sg13cmos5l_buf_1 _130_ (.A(FrameData[0]),
    .X(net5));
 sg13cmos5l_buf_1 _131_ (.A(FrameData[1]),
    .X(net16));
 sg13cmos5l_buf_1 _132_ (.A(FrameData[2]),
    .X(net27));
 sg13cmos5l_buf_1 _133_ (.A(FrameData[3]),
    .X(net30));
 sg13cmos5l_buf_1 _134_ (.A(FrameData[4]),
    .X(net31));
 sg13cmos5l_buf_1 _135_ (.A(FrameData[5]),
    .X(net32));
 sg13cmos5l_buf_1 _136_ (.A(FrameData[6]),
    .X(net33));
 sg13cmos5l_buf_1 _137_ (.A(FrameData[7]),
    .X(net34));
 sg13cmos5l_buf_1 _138_ (.A(FrameData[8]),
    .X(net35));
 sg13cmos5l_buf_1 _139_ (.A(FrameData[9]),
    .X(net36));
 sg13cmos5l_buf_1 _140_ (.A(FrameData[10]),
    .X(net6));
 sg13cmos5l_buf_1 _141_ (.A(FrameData[11]),
    .X(net7));
 sg13cmos5l_buf_1 _142_ (.A(FrameData[12]),
    .X(net8));
 sg13cmos5l_buf_1 _143_ (.A(FrameData[13]),
    .X(net9));
 sg13cmos5l_buf_1 _144_ (.A(FrameData[14]),
    .X(net10));
 sg13cmos5l_buf_1 _145_ (.A(FrameData[15]),
    .X(net11));
 sg13cmos5l_buf_1 _146_ (.A(FrameData[16]),
    .X(net12));
 sg13cmos5l_buf_1 _147_ (.A(FrameData[17]),
    .X(net13));
 sg13cmos5l_buf_1 _148_ (.A(FrameData[18]),
    .X(net14));
 sg13cmos5l_buf_1 _149_ (.A(FrameData[19]),
    .X(net15));
 sg13cmos5l_buf_1 _150_ (.A(FrameData[20]),
    .X(net17));
 sg13cmos5l_buf_1 _151_ (.A(FrameData[21]),
    .X(net18));
 sg13cmos5l_buf_1 _152_ (.A(FrameData[22]),
    .X(net19));
 sg13cmos5l_buf_1 _153_ (.A(FrameData[23]),
    .X(net20));
 sg13cmos5l_buf_1 _154_ (.A(FrameData[24]),
    .X(net21));
 sg13cmos5l_buf_1 _155_ (.A(FrameData[25]),
    .X(net22));
 sg13cmos5l_buf_1 _156_ (.A(FrameData[26]),
    .X(net23));
 sg13cmos5l_buf_1 _157_ (.A(FrameData[27]),
    .X(net24));
 sg13cmos5l_buf_1 _158_ (.A(FrameData[28]),
    .X(net25));
 sg13cmos5l_buf_1 _159_ (.A(FrameData[29]),
    .X(net26));
 sg13cmos5l_buf_1 _160_ (.A(FrameData[30]),
    .X(net28));
 sg13cmos5l_buf_1 _161_ (.A(FrameData[31]),
    .X(net29));
 sg13cmos5l_buf_1 _162_ (.A(FrameStrobe[0]),
    .X(net37));
 sg13cmos5l_buf_1 _163_ (.A(FrameStrobe[1]),
    .X(net48));
 sg13cmos5l_buf_1 _164_ (.A(FrameStrobe[2]),
    .X(net49));
 sg13cmos5l_buf_1 _165_ (.A(FrameStrobe[3]),
    .X(net50));
 sg13cmos5l_buf_1 _166_ (.A(FrameStrobe[4]),
    .X(net51));
 sg13cmos5l_buf_1 _167_ (.A(FrameStrobe[5]),
    .X(net52));
 sg13cmos5l_buf_1 _168_ (.A(FrameStrobe[6]),
    .X(net53));
 sg13cmos5l_buf_1 _169_ (.A(FrameStrobe[7]),
    .X(net54));
 sg13cmos5l_buf_1 _170_ (.A(FrameStrobe[8]),
    .X(net55));
 sg13cmos5l_buf_1 _171_ (.A(FrameStrobe[9]),
    .X(net56));
 sg13cmos5l_buf_1 _172_ (.A(FrameStrobe[10]),
    .X(net38));
 sg13cmos5l_buf_1 _173_ (.A(FrameStrobe[11]),
    .X(net39));
 sg13cmos5l_buf_1 _174_ (.A(FrameStrobe[12]),
    .X(net40));
 sg13cmos5l_buf_1 _175_ (.A(FrameStrobe[13]),
    .X(net41));
 sg13cmos5l_buf_1 _176_ (.A(FrameStrobe[14]),
    .X(net42));
 sg13cmos5l_buf_1 _177_ (.A(FrameStrobe[15]),
    .X(net43));
 sg13cmos5l_buf_1 _178_ (.A(FrameStrobe[16]),
    .X(net44));
 sg13cmos5l_buf_1 _179_ (.A(FrameStrobe[17]),
    .X(net45));
 sg13cmos5l_buf_1 _180_ (.A(FrameStrobe[18]),
    .X(net46));
 sg13cmos5l_buf_1 _181_ (.A(FrameStrobe[19]),
    .X(net47));
 sg13cmos5l_buf_1 _182_ (.A(GBUF_A_OUT),
    .X(net57));
 sg13cmos5l_buf_1 _183_ (.A(GBUF_B_OUT),
    .X(net58));
 sg13cmos5l_buf_1 _184_ (.A(GBUF_C_OUT),
    .X(net59));
 sg13cmos5l_buf_1 _185_ (.A(GBUF_D_OUT),
    .X(net60));
 sg13cmos5l_buf_1 output1 (.A(net1),
    .X(E_GBUF_BEG[0]));
 sg13cmos5l_buf_1 output10 (.A(net10),
    .X(FrameData_O[14]));
 sg13cmos5l_buf_1 output11 (.A(net11),
    .X(FrameData_O[15]));
 sg13cmos5l_buf_1 output12 (.A(net12),
    .X(FrameData_O[16]));
 sg13cmos5l_buf_1 output13 (.A(net13),
    .X(FrameData_O[17]));
 sg13cmos5l_buf_1 output14 (.A(net14),
    .X(FrameData_O[18]));
 sg13cmos5l_buf_1 output15 (.A(net15),
    .X(FrameData_O[19]));
 sg13cmos5l_buf_1 output16 (.A(net16),
    .X(FrameData_O[1]));
 sg13cmos5l_buf_1 output17 (.A(net17),
    .X(FrameData_O[20]));
 sg13cmos5l_buf_1 output18 (.A(net18),
    .X(FrameData_O[21]));
 sg13cmos5l_buf_1 output19 (.A(net19),
    .X(FrameData_O[22]));
 sg13cmos5l_buf_1 output2 (.A(net2),
    .X(E_GBUF_BEG[1]));
 sg13cmos5l_buf_1 output20 (.A(net20),
    .X(FrameData_O[23]));
 sg13cmos5l_buf_1 output21 (.A(net21),
    .X(FrameData_O[24]));
 sg13cmos5l_buf_1 output22 (.A(net22),
    .X(FrameData_O[25]));
 sg13cmos5l_buf_1 output23 (.A(net23),
    .X(FrameData_O[26]));
 sg13cmos5l_buf_1 output24 (.A(net24),
    .X(FrameData_O[27]));
 sg13cmos5l_buf_1 output25 (.A(net25),
    .X(FrameData_O[28]));
 sg13cmos5l_buf_1 output26 (.A(net26),
    .X(FrameData_O[29]));
 sg13cmos5l_buf_1 output27 (.A(net27),
    .X(FrameData_O[2]));
 sg13cmos5l_buf_1 output28 (.A(net28),
    .X(FrameData_O[30]));
 sg13cmos5l_buf_1 output29 (.A(net29),
    .X(FrameData_O[31]));
 sg13cmos5l_buf_1 output3 (.A(net3),
    .X(E_GBUF_BEG[2]));
 sg13cmos5l_buf_1 output30 (.A(net30),
    .X(FrameData_O[3]));
 sg13cmos5l_buf_1 output31 (.A(net31),
    .X(FrameData_O[4]));
 sg13cmos5l_buf_1 output32 (.A(net32),
    .X(FrameData_O[5]));
 sg13cmos5l_buf_1 output33 (.A(net33),
    .X(FrameData_O[6]));
 sg13cmos5l_buf_1 output34 (.A(net34),
    .X(FrameData_O[7]));
 sg13cmos5l_buf_1 output35 (.A(net35),
    .X(FrameData_O[8]));
 sg13cmos5l_buf_1 output36 (.A(net36),
    .X(FrameData_O[9]));
 sg13cmos5l_buf_1 output37 (.A(net37),
    .X(FrameStrobe_O[0]));
 sg13cmos5l_buf_1 output38 (.A(net38),
    .X(FrameStrobe_O[10]));
 sg13cmos5l_buf_1 output39 (.A(net39),
    .X(FrameStrobe_O[11]));
 sg13cmos5l_buf_1 output4 (.A(net4),
    .X(E_GBUF_BEG[3]));
 sg13cmos5l_buf_1 output40 (.A(net40),
    .X(FrameStrobe_O[12]));
 sg13cmos5l_buf_1 output41 (.A(net41),
    .X(FrameStrobe_O[13]));
 sg13cmos5l_buf_1 output42 (.A(net42),
    .X(FrameStrobe_O[14]));
 sg13cmos5l_buf_1 output43 (.A(net43),
    .X(FrameStrobe_O[15]));
 sg13cmos5l_buf_1 output44 (.A(net44),
    .X(FrameStrobe_O[16]));
 sg13cmos5l_buf_1 output45 (.A(net45),
    .X(FrameStrobe_O[17]));
 sg13cmos5l_buf_1 output46 (.A(net46),
    .X(FrameStrobe_O[18]));
 sg13cmos5l_buf_1 output47 (.A(net47),
    .X(FrameStrobe_O[19]));
 sg13cmos5l_buf_1 output48 (.A(net48),
    .X(FrameStrobe_O[1]));
 sg13cmos5l_buf_1 output49 (.A(net49),
    .X(FrameStrobe_O[2]));
 sg13cmos5l_buf_1 output5 (.A(net5),
    .X(FrameData_O[0]));
 sg13cmos5l_buf_1 output50 (.A(net50),
    .X(FrameStrobe_O[3]));
 sg13cmos5l_buf_1 output51 (.A(net51),
    .X(FrameStrobe_O[4]));
 sg13cmos5l_buf_1 output52 (.A(net52),
    .X(FrameStrobe_O[5]));
 sg13cmos5l_buf_1 output53 (.A(net53),
    .X(FrameStrobe_O[6]));
 sg13cmos5l_buf_1 output54 (.A(net54),
    .X(FrameStrobe_O[7]));
 sg13cmos5l_buf_1 output55 (.A(net55),
    .X(FrameStrobe_O[8]));
 sg13cmos5l_buf_1 output56 (.A(net56),
    .X(FrameStrobe_O[9]));
 sg13cmos5l_buf_1 output57 (.A(net57),
    .X(N_GBUF_BEG[0]));
 sg13cmos5l_buf_1 output58 (.A(net58),
    .X(N_GBUF_BEG[1]));
 sg13cmos5l_buf_1 output59 (.A(net59),
    .X(N_GBUF_BEG[2]));
 sg13cmos5l_buf_1 output6 (.A(net6),
    .X(FrameData_O[10]));
 sg13cmos5l_buf_1 output60 (.A(net60),
    .X(N_GBUF_BEG[3]));
 sg13cmos5l_buf_1 output7 (.A(net7),
    .X(FrameData_O[11]));
 sg13cmos5l_buf_1 output8 (.A(net8),
    .X(FrameData_O[12]));
 sg13cmos5l_buf_1 output9 (.A(net9),
    .X(FrameData_O[13]));
endmodule
