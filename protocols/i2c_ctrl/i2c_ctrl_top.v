// I2C controller user design (provisional user-design interface, DECISIONS D-014).
//
// Pins:    open drain. sda_oe / scl_oe = 1 pulls the line low; 0 releases it (external pull-up).
//          sda_i / scl_i read the bus (two-flop synchronized inside).
// Timing:  each SCL low and high phase lasts 2*Q clocks (plus the synchronizer delay when the
//          controller waits for SCL to go high, which is also how clock stretching is honoured).
//          SCL ~= clk / (4*Q + 3). Q >= 2.
// Host:    command bytes on h_w* (h_wlast is ignored):
//            8'b00xx_xxxx  START (a repeated START when the bus is already ours)
//            8'b01xx_xxxx  WRITE: the next byte on h_w* is sent; reply 8'h00 = ACK, 8'h01 = NACK
//            8'b10xx_xxx0  READ, then ACK  (more bytes follow); reply = the byte read
//            8'b10xx_xxx1  READ, then NACK (last byte);         reply = the byte read
//            8'b11xx_xxxx  STOP
//          WRITE / READ / repeated START without a bus START first, and STOP on a free bus, are
//          ignored and set the sticky `err` status bit.
//          Replies arrive in a one-byte holding register on h_r*.
//          h_status = {4'b0, err, overrun, last_nack, bus_owned}.
// Limits:  single controller (no arbitration), 7-bit addressing is the host's job (it sends the
//          address byte with WRITE), no 10-bit addressing helpers.
`default_nettype none

module i2c_ctrl_top #(
    parameter Q = 4
) (
    input  wire       clk,
    input  wire       rst_n,
    // pins (open drain)
    input  wire       sda_i,
    input  wire       scl_i,
    output reg        sda_oe,
    output reg        scl_oe,
    output wire [1:0] out_o,      // pin output values: always 0 (open drain)
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
    localparam integer T2 = 2 * Q;
    localparam CW = $clog2(T2 + 1);
    localparam integer T2_M1_I = T2 - 1;
    localparam integer Q_M1_I  = Q - 1;
    localparam [CW-1:0] T2_M1 = T2_M1_I[CW-1:0];
    localparam [CW-1:0] Q_M1  = Q_M1_I[CW-1:0];

    localparam [4:0] S_IDLE  = 5'd0,   // bus free, both lines released
                     S_ACT   = 5'd1,   // bus owned, SCL held low, waiting for a command
                     S_WDATA = 5'd2,   // WRITE: waiting for the data byte
                     S_ST_A  = 5'd3,   // START: SDA low, wait
                     S_ST_B  = 5'd4,   // START: SCL low, wait
                     S_RS_A  = 5'd5,   // repeated START: SDA released, wait
                     S_RS_B  = 5'd6,   // repeated START: SCL released, wait for it to be high
                     S_RS_C  = 5'd7,   // repeated START: SCL high, wait
                     S_SP_A  = 5'd8,   // STOP: SDA low, wait
                     S_SP_B  = 5'd9,   // STOP: SCL released, wait for it to be high
                     S_SP_C  = 5'd10,  // STOP: SCL high, wait
                     S_SP_D  = 5'd11,  // STOP: SDA released, bus free time
                     S_B_LOW = 5'd12,  // bit: SCL low, SDA set
                     S_B_WHI = 5'd13,  // bit: SCL released, wait for it to be high (stretching)
                     S_B_HI  = 5'd14,  // bit: SCL high, sample SDA at the end
                     S_B_SET = 5'd15;  // bit: SCL low for Q clocks before SDA may change

    reg [4:0]    state;
    reg [CW-1:0] cnt;
    reg [7:0]    out_bits;   // bits still to send after the current one (data, then ACK); 1 = release
    reg [8:0]    in_bits;
    reg [3:0]    nbit;
    reg          is_read;
    reg [1:0]    sda_s, scl_s;
    reg          owned, err_q, overrun_q, nack_q;

    wire ready  = (state == S_IDLE) || (state == S_ACT) || (state == S_WDATA);
    wire accept = h_wvalid && ready;
    wire [1:0] op = h_wdata[7:6];
    wire done  = (cnt == 0);

    assign h_wready = ready;
    assign out_o    = 2'b00;

    // push a reply byte to the host (drop it and flag overrun if the last one wasn't taken)
    task push(input [7:0] b);
        begin
            if (h_rvalid && !h_rready) overrun_q <= 1'b1;
            else begin
                h_rdata  <= b;
                h_rvalid <= 1'b1;
            end
        end
    endtask

    always @(posedge clk) begin
        if (!rst_n) begin
            state     <= S_IDLE;
            cnt       <= {CW{1'b0}};
            out_bits  <= 8'hFF;
            in_bits   <= 9'h000;
            nbit      <= 4'd0;
            is_read   <= 1'b0;
            sda_s     <= 2'b11;
            scl_s     <= 2'b11;
            sda_oe    <= 1'b0;
            scl_oe    <= 1'b0;
            owned     <= 1'b0;
            err_q     <= 1'b0;
            overrun_q <= 1'b0;
            nack_q    <= 1'b0;
            h_rdata   <= 8'h00;
            h_rvalid  <= 1'b0;
        end else begin
            sda_s <= {sda_s[0], sda_i};
            scl_s <= {scl_s[0], scl_i};
            if (h_rvalid && h_rready) h_rvalid <= 1'b0;
            if (!done) cnt <= cnt - 1'b1;

            case (state)
                S_IDLE: if (accept) begin
                    if (op == 2'b00) begin            // START
                        sda_oe <= 1'b1;
                        cnt    <= T2_M1;
                        state  <= S_ST_A;
                    end else err_q <= 1'b1;
                end

                S_ACT: if (accept) begin
                    case (op)
                        2'b00: begin                  // repeated START
                            sda_oe <= 1'b0;
                            cnt    <= Q_M1;
                            state  <= S_RS_A;
                        end
                        2'b01: state <= S_WDATA;      // WRITE
                        2'b10: begin                  // READ
                            out_bits <= {7'h7F, h_wdata[0]};
                            is_read  <= 1'b1;
                            nbit     <= 4'd0;
                            sda_oe   <= 1'b0;
                            cnt      <= T2_M1;
                            state    <= S_B_LOW;
                        end
                        default: begin                // STOP
                            sda_oe <= 1'b1;
                            cnt    <= Q_M1;
                            state  <= S_SP_A;
                        end
                    endcase
                end

                S_WDATA: if (accept) begin
                    out_bits <= {h_wdata[6:0], 1'b1};
                    is_read  <= 1'b0;
                    nbit     <= 4'd0;
                    sda_oe   <= !h_wdata[7];
                    cnt      <= T2_M1;
                    state    <= S_B_LOW;
                end

                S_ST_A: if (done) begin
                    scl_oe <= 1'b1;
                    cnt    <= T2_M1;
                    state  <= S_ST_B;
                end

                S_ST_B: if (done) begin
                    owned <= 1'b1;
                    state <= S_ACT;
                end

                S_RS_A: if (done) begin
                    scl_oe <= 1'b0;
                    state  <= S_RS_B;
                end

                S_RS_B: if (scl_s[1]) begin
                    cnt   <= T2_M1;
                    state <= S_RS_C;
                end

                S_RS_C: if (done) begin
                    sda_oe <= 1'b1;                   // SDA falls while SCL is high
                    cnt    <= T2_M1;
                    state  <= S_ST_A;
                end

                S_SP_A: if (done) begin
                    scl_oe <= 1'b0;
                    state  <= S_SP_B;
                end

                S_SP_B: if (scl_s[1]) begin
                    cnt   <= T2_M1;
                    state <= S_SP_C;
                end

                S_SP_C: if (done) begin
                    sda_oe <= 1'b0;                   // SDA rises while SCL is high
                    cnt    <= T2_M1;
                    state  <= S_SP_D;
                end

                S_SP_D: if (done) begin
                    owned <= 1'b0;
                    state <= S_IDLE;
                end

                S_B_LOW: if (done) begin
                    scl_oe <= 1'b0;
                    state  <= S_B_WHI;
                end

                S_B_WHI: if (scl_s[1]) begin
                    cnt   <= T2_M1;
                    state <= S_B_HI;
                end

                S_B_HI: if (done) begin
                    in_bits <= {in_bits[7:0], sda_s[1]};
                    scl_oe  <= 1'b1;                  // SCL falls; SDA changes only Q clocks later
                    cnt     <= Q_M1;
                    state   <= S_B_SET;
                end

                S_B_SET: if (done) begin
                    if (nbit == 4'd8) begin
                        // 9 bits done: in_bits[8:1] = data, in_bits[0] = the ACK bit
                        sda_oe <= 1'b0;               // release SDA; SCL stays low between commands
                        if (is_read) push(in_bits[8:1]);
                        else begin
                            push({7'b0, in_bits[0]});
                            nack_q <= in_bits[0];
                        end
                        state <= S_ACT;
                    end else begin
                        nbit     <= nbit + 1'b1;
                        sda_oe   <= !out_bits[7];     // next bit, while SCL is low
                        out_bits <= {out_bits[6:0], 1'b1};
                        cnt      <= Q_M1;
                        state    <= S_B_LOW;
                    end
                end

                default: state <= S_IDLE;
            endcase
        end
    end

    wire _unused = &{h_wlast, 1'b0};
    assign h_status = {4'b0, err_q, overrun_q, nack_q, owned};
endmodule
