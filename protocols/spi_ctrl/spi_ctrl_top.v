// SPI controller user design (provisional user-design interface, DECISIONS D-014).
//
// Mode:  CPOL = SCK idle level; CPHA = 0: sample on the leading edge, change on the trailing edge
//        (first bit valid before the first edge); CPHA = 1: change on leading, sample on trailing.
//        MSB first, 8-bit bytes, full duplex. All fixed in the bitstream (parameters).
// Speed: SCK half period = HALF clocks, HALF >= 4 (SCK <= clk/8). MISO goes through a two-flop
//        synchronizer (2 clocks) and a target may take up to 1 clock after its change edge, so the
//        sampling edge must come at least 4 clocks after the change edge.
// Host:  h_w*  bytes to send; h_wlast = 1 ends the transaction after this byte (CS released).
//        While CS is held between bytes, SCK stays idle until the next byte arrives.
//        h_r*  the byte received during each transfer (one-byte holding register).
//        h_status = {6'b0, overrun, cs_active}; overrun is sticky until reset (the new byte is dropped).
// Pins:  sck_o, mosi_o, cs_n_o outputs (always driven); miso_i input.
`default_nettype none

module spi_ctrl_top #(
    parameter CPOL = 0,
    parameter CPHA = 0,
    parameter HALF = 4
) (
    input  wire       clk,
    input  wire       rst_n,
    // pins
    output reg        sck_o,
    output reg        mosi_o,
    output reg        cs_n_o,
    input  wire       miso_i,
    output wire [2:0] out_oe,     // sck, mosi, cs_n
    // host -> design
    input  wire [7:0] h_wdata,
    input  wire       h_wlast,
    input  wire       h_wvalid,
    output wire       h_wready,
    // design -> host
    output reg  [7:0] h_rdata,
    output reg        h_rvalid,
    input  wire       h_rready,
    output wire [7:0] h_status
);
    localparam [2:0] S_IDLE = 3'd0,  // CS high
                     S_XFER = 3'd1,  // shifting a byte
                     S_HOLD = 3'd2,  // CS low, waiting for the next byte
                     S_END  = 3'd3,  // last byte done, CS still low for half a period
                     S_GAP  = 3'd4;  // CS high for half a period before the next transaction

    localparam CW = (HALF > 1) ? $clog2(HALF) : 1;
    localparam integer  HALF_M1_I = HALF - 1;
    localparam [CW-1:0] HALF_M1   = HALF_M1_I[CW-1:0];
    localparam CPOL_B = (CPOL != 0);
    localparam CPHA_B = (CPHA != 0);

    reg [2:0]    state;
    reg [CW-1:0] cnt;
    reg [3:0]    nedge;   // edges done in this byte, 0..15
    reg [7:0]    tx, rx;
    reg          last_q;
    reg [1:0]    miso_s;
    reg          overrun_q;

    wire ready    = (state == S_IDLE) || (state == S_HOLD);
    wire accept   = h_wvalid && ready;
    wire tick     = (cnt == 0);
    wire leading  = (nedge[0] == 1'b0);            // even-numbered edges leave the idle level
    wire sample_e = leading ? !CPHA_B : CPHA_B;    // is this edge the sampling edge?

    assign h_wready = ready;
    assign out_oe   = 3'b111;

    always @(posedge clk) begin
        if (!rst_n) begin
            state     <= S_IDLE;
            cnt       <= {CW{1'b0}};
            nedge     <= 4'd0;
            tx        <= 8'h00;
            rx        <= 8'h00;
            last_q    <= 1'b0;
            miso_s    <= 2'b11;
            sck_o     <= CPOL_B;
            mosi_o    <= 1'b1;
            cs_n_o    <= 1'b1;
            h_rdata   <= 8'h00;
            h_rvalid  <= 1'b0;
            overrun_q <= 1'b0;
        end else begin
            miso_s <= {miso_s[0], miso_i};
            if (h_rvalid && h_rready) h_rvalid <= 1'b0;

            case (state)
                S_IDLE, S_HOLD: begin
                    if (accept) begin
                        state  <= S_XFER;
                        cs_n_o <= 1'b0;
                        tx     <= h_wdata;
                        last_q <= h_wlast;
                        nedge  <= 4'd0;
                        cnt    <= HALF_M1;
                        if (!CPHA_B) mosi_o <= h_wdata[7];   // first bit before the first edge
                    end
                end

                S_XFER: begin
                    if (!tick) begin
                        cnt <= cnt - 1'b1;
                    end else begin
                        cnt   <= HALF_M1;
                        sck_o <= !sck_o;
                        nedge <= nedge + 1'b1;
                        if (sample_e) begin
                            rx <= {rx[6:0], miso_s[1]};
                        end else if (CPHA_B) begin               // CPHA 1: change on leading
                            mosi_o <= tx[7];
                            tx     <= {tx[6:0], 1'b0};
                        end else if (nedge != 4'd15) begin      // CPHA 0: change on trailing
                            mosi_o <= tx[6];
                            tx     <= {tx[6:0], 1'b0};
                        end
                        if (nedge == 4'd15) begin               // byte complete after this edge
                            if (h_rvalid && !h_rready) overrun_q <= 1'b1;
                            else begin
                                h_rdata  <= sample_e ? {rx[6:0], miso_s[1]} : rx;
                                h_rvalid <= 1'b1;
                            end
                            state <= last_q ? S_END : S_HOLD;
                        end
                    end
                end

                S_END: begin
                    if (!tick) cnt <= cnt - 1'b1;
                    else begin
                        cnt    <= HALF_M1;
                        cs_n_o <= 1'b1;
                        mosi_o <= 1'b1;
                        state  <= S_GAP;
                    end
                end

                S_GAP: begin
                    if (!tick) cnt <= cnt - 1'b1;
                    else       state <= S_IDLE;
                end

                default: state <= S_IDLE;
            endcase
        end
    end

    assign h_status = {6'b0, overrun_q, !cs_n_o};
endmodule
