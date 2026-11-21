// For an arbitrary output pad, check owner readback, A-over-N selection,
// and output enable against an independent selected-owner reference.
module pad_ownership(input wire clk);
    localparam NU = 4;
    (* anyseq *) reg rst_n, own_we;
    (* anyseq *) reg [3:0] own_waddr;
    (* anyseq *) reg [2:0] own_wdata;
    (* anyconst *) reg [3:0] pad;
    (* anyseq *) reg [NU-1:0] a_out, a_oe, n_out, n_oe;
    (* anyseq *) reg [5*NU-1:0] pin_a, pin_n;
    wire [2:0] owner;
    wire [15:0] pad_out, pad_oe;
    trw_pins #(.NU(NU)) dut (
        .clk(clk), .rst_n(rst_n), .own_we(own_we),
        .own_waddr(own_waddr), .own_wdata(own_wdata), .own_raddr(pad),
        .own_q(owner), .a_out(a_out), .a_oe(a_oe), .n_out(n_out),
        .n_oe(n_oe), .pin_a(pin_a), .pin_n(pin_n),
        .pad_out(pad_out), .pad_oe(pad_oe)
    );

    reg initialized = 0;
    reg [2:0] expected_owner;
    wire [4:0] pad_number = {1'b0,pad} + 5'd8;
    wire [1:0] selected = expected_owner[1:0];
    wire use_a = expected_owner < NU && pin_a[5*selected +: 5] == pad_number;
    wire use_n = expected_owner < NU && !use_a && pin_n[5*selected +: 5] == pad_number;
    always @(posedge clk) begin
        if (!initialized) assume(!rst_n);
        initialized <= 1;
        if (!rst_n)
            expected_owner <= 7;
        else if (own_we && own_waddr == pad && pad != 3 && pad != 6)
            expected_owner <= own_wdata;

        if (initialized) begin
            assert(owner == expected_owner);
            assert(pad_out[pad] == (use_a ? a_out[selected] : use_n ? n_out[selected] : 1'b0));
            assert(pad_oe[pad] == (use_a ? a_oe[selected] : use_n ? n_oe[selected] : 1'b0));
            cover(use_a && pad_oe[pad]);
            cover(use_n && pad_oe[pad]);
        end
    end
endmodule
