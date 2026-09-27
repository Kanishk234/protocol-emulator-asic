`default_nettype none
// Test fixture only: real pinned configuration loader and row registers.
// No programmable fabric; constant user outputs exercise wrapper parking.
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
    eFPGA_Config #(.NumberOfRows(14),.RowSelectWidth(5)) config_loader (
        .CLK(CLK),.resetn(resetn),.Rx(Rx),.s_clk(s_clk),.s_data(s_data),
        .SelfWriteData(SelfWriteData),.SelfWriteStrobe(SelfWriteStrobe),
        .ComActive(ComActive),.ReceiveLED(ReceiveLED),
        .ConfigWriteData(LocalWriteData),.ConfigWriteStrobe(LocalWriteStrobe),
        .FrameAddressRegister(FrameAddressRegister),.LongFrameStrobe(LongFrameStrobe),
        .RowSelect(RowSelect)
    );
    genvar row;
    generate for(row=0;row<14;row=row+1) begin: rows
        Frame_Data_Reg #(.Row(row+1)) data_register (
            .CLK(CLK),.FrameData_I(LocalWriteData),
            .FrameData_O(FrameRegister[row*32+:32]),.RowSelect(RowSelect)
        );
    end endgenerate
    assign I_top=28'h5a5a5a5;
    assign T_top=28'hffffffe;
    assign A_config_C=0;
    assign B_config_C=0;
    wire unused = &{1'b0,ReloadHold,O_top};
endmodule
`resetall
