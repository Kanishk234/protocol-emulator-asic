`default_nettype none
// Test fixture only: real pinned configuration loader and row registers.
// No programmable fabric. LOADER_BOUNDARY keeps row data observable for
// synthesis through an opaque fabric-boundary module; normal mode is RTL only.
module eFPGA_top (
    input wire CLK, resetn, ReloadHold, SelfWriteStrobe,
    input wire [31:0] SelfWriteData,
    input wire [27:0] O_top,
    output wire [27:0] I_top, T_top,
    output wire [55:0] A_config_C, B_config_C,
    input wire Rx, s_clk, s_data,
    output wire ComActive, ReceiveLED
);
    wire [31:0] LocalWriteData, FrameAddressRegister;
    wire LocalWriteStrobe, LongFrameStrobe;
    wire [4:0] RowSelect;
    wire [447:0] FrameRegister;
`ifdef WORD_ONLY_LOADER
    // Experimental management-owned word port: omit inactive serial frontends.
    // Keep the pinned FSM and row-register behavior unchanged.
    assign LocalWriteData=SelfWriteData;
    assign LocalWriteStrobe=SelfWriteStrobe;
    assign ComActive=1'b0;
    assign ReceiveLED=1'b0;
    ConfigFSM #(.NumberOfRows(14),.RowSelectWidth(5)) config_loader (
        .CLK(CLK),.reset_n(resetn),.write_data(SelfWriteData),
        .write_strobe(SelfWriteStrobe),.fsm_reset(1'b0),
        .frame_address_register(FrameAddressRegister),
        .long_frame_strobe(LongFrameStrobe),.row_select(RowSelect)
    );
    wire unused_serial=&{1'b0,Rx,s_clk,s_data};
`else
    eFPGA_Config #(.NumberOfRows(14),.RowSelectWidth(5)) config_loader (
        .CLK(CLK),.resetn(resetn),.Rx(Rx),.s_clk(s_clk),.s_data(s_data),
        .SelfWriteData(SelfWriteData),.SelfWriteStrobe(SelfWriteStrobe),
        .ComActive(ComActive),.ReceiveLED(ReceiveLED),
        .ConfigWriteData(LocalWriteData),.ConfigWriteStrobe(LocalWriteStrobe),
        .FrameAddressRegister(FrameAddressRegister),.LongFrameStrobe(LongFrameStrobe),
        .RowSelect(RowSelect)
    );
`endif
    genvar row;
    generate for(row=0;row<14;row=row+1) begin: rows
        Frame_Data_Reg #(.Row(row+1)) data_register (
            .CLK(CLK),.FrameData_I(LocalWriteData),
            .FrameData_O(FrameRegister[row*32+:32]),.RowSelect(RowSelect)
        );
    end endgenerate
`ifdef LOADER_BOUNDARY
    wp_loader_boundary boundary (
        .CLK(CLK),.ReloadHold(ReloadHold),.O_top(O_top),
        .I_top(I_top),.T_top(T_top),.A_config_C(A_config_C),.B_config_C(B_config_C),
        .FrameRegister(FrameRegister),.FrameAddressRegister(FrameAddressRegister),
        .LongFrameStrobe(LongFrameStrobe)
    );
`else
    assign I_top=28'h5a5a5a5;
    assign T_top=28'hffffffe;
    assign A_config_C=0;
    assign B_config_C=0;
    wire unused = &{1'b0,ReloadHold,O_top};
`endif
endmodule
`resetall
