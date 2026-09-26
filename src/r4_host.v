// R4 spike (branch spike/r4-floorplan only): host SPI slave stub, the §9 transaction format.
//   SPI mode 0; CS_n, SCK, MOSI arrive through the chip's 2-FF synchronisers (SCK <= clk/8).
//   CMD[7:0] (bit 7 = write), ADDR[15:0], then 16-bit words, MSB first, auto-increment.
//   Write: each word -> one `wr` pulse with (wr_addr, wr_data).
//   Read: one dummy byte, then words. `rd_req` asks for rd_addr right after the address (and after
//   each word is loaded); the chip answers on `rd_data` within 60 clocks. At the last rise of the
//   dummy byte / of a word, rd_data is loaded into the output shift register and `rd_ack` pulses (side
//   effects such as a HOST_OUT pop happen there). MISO changes after SCK falls.
`default_nettype none

module r4_host (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        csn,
    input  wire        sck,
    input  wire        mosi,
    output reg         miso,
    output reg         wr,
    output reg  [15:0] wr_addr,
    output reg  [15:0] wr_data,
    output reg         rd_req,
    output reg  [15:0] rd_addr,
    input  wire [15:0] rd_data,
    output reg         rd_ack
);
    localparam P_CMD = 3'd0, P_AH = 3'd1, P_AL = 3'd2, P_DUMMY = 3'd3, P_DATA = 3'd4;
    reg        sck_q;
    reg [2:0]  ph;
    reg [3:0]  cnt;             // bits of the current byte/word so far
    reg        is_wr;
    reg [15:0] sin, sout, addr;

    wire rise = sck && !sck_q;
    wire fall = !sck && sck_q;
    wire [15:0] nxt = {sin[14:0], mosi};
    wire last8  = (cnt == 4'd7);
    wire last16 = (cnt == 4'd15);

    always @(posedge clk) begin
        if (!rst_n) begin
            sck_q <= 1'b0;  ph <= P_CMD;  cnt <= 4'd0;  is_wr <= 1'b0;
            sin <= 16'd0;  sout <= 16'd0;  addr <= 16'd0;  miso <= 1'b0;
            wr <= 1'b0;  wr_addr <= 16'd0;  wr_data <= 16'd0;
            rd_req <= 1'b0;  rd_addr <= 16'd0;  rd_ack <= 1'b0;
        end else begin
            sck_q  <= sck;
            wr     <= 1'b0;
            rd_req <= 1'b0;
            rd_ack <= 1'b0;
            if (csn) begin
                ph   <= P_CMD;
                cnt  <= 4'd0;
                miso <= 1'b0;             // idle between transactions (and no stale prefetch)
                sout <= 16'd0;
            end else if (rise) begin
                sin <= nxt;
                cnt <= cnt + 4'd1;
                case (ph)
                    P_CMD:   if (last8) begin is_wr <= nxt[7]; ph <= P_AH; cnt <= 4'd0; end
                    P_AH:    if (last8) begin ph <= P_AL; cnt <= 4'd0; end
                    P_AL:    if (last8) begin
                                 addr <= nxt;                 // {ADDR[15:8], ADDR[7:0]}
                                 cnt  <= 4'd0;
                                 if (is_wr) begin
                                     ph <= P_DATA;
                                 end else begin
                                     ph <= P_DUMMY;
                                     rd_req  <= 1'b1;
                                     rd_addr <= nxt;
                                 end
                             end
                    P_DUMMY: if (last8) begin
                                 ph <= P_DATA;  cnt <= 4'd0;
                                 sout <= rd_data;  rd_ack <= 1'b1;
                             end
                    default: if (last16) begin
                                 cnt <= 4'd0;
                                 if (is_wr) begin
                                     wr <= 1'b1;  wr_addr <= addr;  wr_data <= nxt;
                                     addr <= addr + 16'd1;
                                 end else begin
                                     sout <= rd_data;  rd_ack <= 1'b1;
                                 end
                             end
                endcase
            end else if (fall) begin
                miso <= sout[15];
                sout <= {sout[14:0], 1'b0};
            end
            // the next read word is asked for right after one is loaded
            if (rd_ack) begin
                rd_req  <= 1'b1;
                rd_addr <= rd_addr + 16'd1;
            end
        end
    end
    wire _unused = &{1'b0, sin[15]};
endmodule
