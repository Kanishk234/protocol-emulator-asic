module eFPGA_top
    #(
        parameter include_eFPGA=1,
        parameter NumberOfRows=2,
        parameter NumberOfCols=2,
        parameter FrameBitsPerRow=32,
        parameter MaxFramesPerCol=20,
        parameter desync_flag=20,
        parameter FrameSelectWidth=5,
        parameter RowSelectWidth=5
    )
    (
        input ReloadHold,
        //External IO port
        output  [7:0] A_config_C,
        output  [7:0] B_config_C,
        output  [3:0] I_top,
        input  [3:0] O_top,
        output  [3:0] T_top,
        //Config related ports
        input  CLK,
        input  resetn,
        input  SelfWriteStrobe,
        input  [31:0] SelfWriteData,
        input  Rx,
        output  ComActive,
        output  ReceiveLED,
        input  s_clk,
        input  s_data
);

 //Signal declarations
wire[(NumberOfRows*FrameBitsPerRow)-1:0] FrameRegister;
wire[(MaxFramesPerCol*NumberOfCols)-1:0] FrameSelect;
wire[(FrameBitsPerRow*(NumberOfRows+2))-1:0] FrameData;
wire[FrameBitsPerRow-1:0] FrameAddressRegister;
wire LongFrameStrobe;
wire[31:0] LocalWriteData;
wire LocalWriteStrobe;
wire[RowSelectWidth-1:0] RowSelect;
`ifndef EMULATION

// ANISH-D8: management owns configuration; serial bypass is omitted.
assign LocalWriteData = SelfWriteData;
assign LocalWriteStrobe = SelfWriteStrobe;
assign ComActive = 1'b0;
assign ReceiveLED = 1'b0;
ConfigFSM #(
    .NumberOfRows(NumberOfRows), .RowSelectWidth(RowSelectWidth),
    .FrameBitsPerRow(FrameBitsPerRow), .desync_flag(desync_flag)
) word_config_inst (
    .CLK(CLK), .reset_n(resetn),
    .write_data(SelfWriteData), .write_strobe(SelfWriteStrobe),
    .fsm_reset(1'b0), .frame_address_register(FrameAddressRegister),
    .long_frame_strobe(LongFrameStrobe), .row_select(RowSelect)
);


Frame_Data_Reg
    #(
    .FrameBitsPerRow(FrameBitsPerRow),
    .RowSelectWidth(RowSelectWidth),
    .Row(1)
    )
    inst_Frame_Data_Reg_0
    (
    .FrameData_I(LocalWriteData),
    .FrameData_O(FrameRegister[0*FrameBitsPerRow+FrameBitsPerRow-1:0*FrameBitsPerRow]),
    .RowSelect(RowSelect),
    .CLK(CLK)
);

Frame_Data_Reg
    #(
    .FrameBitsPerRow(FrameBitsPerRow),
    .RowSelectWidth(RowSelectWidth),
    .Row(2)
    )
    inst_Frame_Data_Reg_1
    (
    .FrameData_I(LocalWriteData),
    .FrameData_O(FrameRegister[1*FrameBitsPerRow+FrameBitsPerRow-1:1*FrameBitsPerRow]),
    .RowSelect(RowSelect),
    .CLK(CLK)
);


Frame_Select
    #(
    .MaxFramesPerCol(MaxFramesPerCol),
    .FrameSelectWidth(FrameSelectWidth),
    .Col(0)
    )
    inst_Frame_Select_0
    (
    .FrameStrobe_I(FrameAddressRegister[MaxFramesPerCol-1:0]),
    .FrameStrobe_O(FrameSelect[0*MaxFramesPerCol+MaxFramesPerCol-1:0*MaxFramesPerCol]),
    .FrameSelect(FrameAddressRegister[FrameBitsPerRow-1:FrameBitsPerRow-FrameSelectWidth]),
    .FrameStrobe(LongFrameStrobe)
);

Frame_Select
    #(
    .MaxFramesPerCol(MaxFramesPerCol),
    .FrameSelectWidth(FrameSelectWidth),
    .Col(1)
    )
    inst_Frame_Select_1
    (
    .FrameStrobe_I(FrameAddressRegister[MaxFramesPerCol-1:0]),
    .FrameStrobe_O(FrameSelect[1*MaxFramesPerCol+MaxFramesPerCol-1:1*MaxFramesPerCol]),
    .FrameSelect(FrameAddressRegister[FrameBitsPerRow-1:FrameBitsPerRow-FrameSelectWidth]),
    .FrameStrobe(LongFrameStrobe)
);


`endif
eFPGA eFPGA_inst (
    .ReloadHold(ReloadHold),
    .Tile_X0Y2_A_config_C_bit0(A_config_C[0]),
    .Tile_X0Y2_A_config_C_bit1(A_config_C[1]),
    .Tile_X0Y2_A_config_C_bit2(A_config_C[2]),
    .Tile_X0Y2_A_config_C_bit3(A_config_C[3]),
    .Tile_X0Y1_A_config_C_bit0(A_config_C[4]),
    .Tile_X0Y1_A_config_C_bit1(A_config_C[5]),
    .Tile_X0Y1_A_config_C_bit2(A_config_C[6]),
    .Tile_X0Y1_A_config_C_bit3(A_config_C[7]),
    .Tile_X0Y2_B_config_C_bit0(B_config_C[0]),
    .Tile_X0Y2_B_config_C_bit1(B_config_C[1]),
    .Tile_X0Y2_B_config_C_bit2(B_config_C[2]),
    .Tile_X0Y2_B_config_C_bit3(B_config_C[3]),
    .Tile_X0Y1_B_config_C_bit0(B_config_C[4]),
    .Tile_X0Y1_B_config_C_bit1(B_config_C[5]),
    .Tile_X0Y1_B_config_C_bit2(B_config_C[6]),
    .Tile_X0Y1_B_config_C_bit3(B_config_C[7]),
    .Tile_X0Y2_B_I_top(I_top[0]),
    .Tile_X0Y2_A_I_top(I_top[1]),
    .Tile_X0Y1_B_I_top(I_top[2]),
    .Tile_X0Y1_A_I_top(I_top[3]),
    .Tile_X0Y2_B_O_top(O_top[0]),
    .Tile_X0Y2_A_O_top(O_top[1]),
    .Tile_X0Y1_B_O_top(O_top[2]),
    .Tile_X0Y1_A_O_top(O_top[3]),
    .Tile_X0Y2_B_T_top(T_top[0]),
    .Tile_X0Y2_A_T_top(T_top[1]),
    .Tile_X0Y1_B_T_top(T_top[2]),
    .Tile_X0Y1_A_T_top(T_top[3]),
    .UserCLK(CLK),
    .FrameData(FrameData),
    .FrameStrobe(FrameSelect)
);


assign FrameData = {32'h12345678,FrameRegister,32'h12345678};
endmodule
