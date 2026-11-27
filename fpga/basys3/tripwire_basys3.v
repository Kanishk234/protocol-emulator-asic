// Basys 3 board adapter. JA carries ui_in, JB carries uo_out and JC carries uio.
`default_nettype none
module tripwire_basys3 (
    input wire clk100,
    input wire reset_button,
    input wire [7:0] ja,
    output wire [7:0] jb,
    inout wire [7:0] jc
);
    wire feedback, feedback_buf, clk50_unbuf, clk50, locked;
    MMCME2_BASE #(
        .CLKIN1_PERIOD(10.0),
        .DIVCLK_DIVIDE(1),
        .CLKFBOUT_MULT_F(10.0),
        .CLKOUT0_DIVIDE_F(20.0)
    ) u_clock (
        .CLKIN1(clk100), .CLKFBIN(feedback_buf), .CLKFBOUT(feedback),
        .CLKOUT0(clk50_unbuf), .LOCKED(locked),
        .PWRDWN(1'b0), .RST(1'b0)
    );
    BUFG u_feedback (.I(feedback), .O(feedback_buf));
    BUFG u_clock_buffer (.I(clk50_unbuf), .O(clk50));

    wire reset_request = reset_button || !locked;
    (* ASYNC_REG = "TRUE" *) reg [1:0] reset_sync;
    always @(posedge clk50 or posedge reset_request) begin
        if (reset_request)
            reset_sync <= 2'b00;
        else
            reset_sync <= {reset_sync[0], 1'b1};
    end
    // Keep the core reset, including the BRAM enable gate, synchronous.
    reg core_rst_n;
    always @(posedge clk50)
        core_rst_n <= reset_sync[1];

    wire [7:0] pad_in, pad_out, pad_oe;
    genvar bit_index;
    generate
        for (bit_index = 0; bit_index < 8; bit_index = bit_index + 1) begin : g_pad
            IOBUF u_pad (
                .I(pad_out[bit_index]), .T(!pad_oe[bit_index] || !core_rst_n || reset_request),
                .O(pad_in[bit_index]), .IO(jc[bit_index])
            );
        end
    endgenerate

    tt_um_tripwire u_tripwire (
        .ui_in(ja), .uo_out(jb), .uio_in(pad_in),
        .uio_out(pad_out), .uio_oe(pad_oe),
        .ena(1'b1), .clk(clk50), .rst_n(core_rst_n)
    );
endmodule
