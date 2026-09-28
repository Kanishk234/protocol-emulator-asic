// I2C controller user design (provisional user-design interface, DECISIONS D-014).
//
// Pins:    open drain. sda_oe / scl_oe = 1 pulls the line low; 0 releases it (external pull-up).
//          sda_i / scl_i read the bus; the shell synchronizes them (ARCHITECTURE §6), so the design
//          has no synchronizers of its own (simulated alone, drive them synchronously).
// Timing:  each SCL low and high phase lasts 2*Q clocks (plus the time until SCL reads high after
//          it is released, which is also how clock stretching is honoured: on the chip, the shell's
//          output register and input synchronizer add a few clocks). SCL ~= clk / (4*Q + a few).
//          Q >= 2.
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
// PRIMS:   1: phase timing in a WARP hard timer (one-shot, RELOAD = 2Q-1; a half load gives Q-1)
//          and the data byte in a hard shift register (ARCHITECTURE §8, D-026); 0: plain logic.
//          Same behaviour at the pins either way.
`default_nettype none

module i2c_ctrl_top #(
    parameter Q     = 4,
    parameter PRIMS = 0
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

    // In the states marked (high), SCL is released and the phase time counts only once SCL reads
    // high (clock stretching); until then the timer is held at its start.
    localparam [3:0] S_IDLE  = 4'd0,   // bus free, both lines released
                     S_ACT   = 4'd1,   // bus owned, SCL held low, waiting for a command
                     S_WDATA = 4'd2,   // WRITE: waiting for the data byte
                     S_ST_A  = 4'd3,   // START: SDA low, wait
                     S_ST_B  = 4'd4,   // START: SCL low, wait
                     S_RS_A  = 4'd5,   // repeated START: SDA released, wait
                     S_RS_C  = 4'd6,   // repeated START: SCL released (high), wait
                     S_SP_A  = 4'd7,   // STOP: SDA low, wait
                     S_SP_C  = 4'd8,   // STOP: SCL released (high), wait
                     S_SP_D  = 4'd9,   // STOP: SDA released, bus free time
                     S_B_LOW = 4'd10,  // bit: SCL low, SDA set
                     S_B_HI  = 4'd11,  // bit: SCL released (high), sample SDA at the end
                     S_B_SET = 4'd12;  // bit: SCL low for Q clocks before SDA may change

    reg [3:0]    state;
    reg          is_read;
    reg          owned, err_q, overrun_q, nack_q;

    wire ready  = (state == S_IDLE) || (state == S_ACT) || (state == S_WDATA);
    wire accept = h_wvalid && ready;
    wire [1:0] op = h_wdata[7:6];
    wire scl_hi = scl_i;
    wire done;                 // the phase timer has run out

    // Phase timer loads (2Q-1 or Q-1 clocks until `done`), from the state machine below.
    wire high  = (state == S_RS_C) || (state == S_SP_C) || (state == S_B_HI);
    wire ld_t2 = (state == S_IDLE  && accept && op == 2'b00) ||
                 (state == S_ACT   && accept && op == 2'b10) ||
                 (state == S_WDATA && accept) ||
                 (state == S_ST_A  && done) || (state == S_RS_C && done) ||
                 (state == S_SP_C  && done) ||
                 (state == S_RS_A  && done) || (state == S_SP_A && done) ||
                 (state == S_B_LOW && done) ||
                 (high && !scl_hi);
    wire last;                 // the current bit is the 9th (ACK) bit
    wire ld_q  = (state == S_ACT   && accept && (op == 2'b00 || op == 2'b11)) ||
                 (state == S_B_HI  && done) ||
                 (state == S_B_SET && done && !last);

    // Bit events: a byte starts (WRITE data or READ), a bit is sampled, the next bit is set.
    wire start_w = (state == S_WDATA) && accept;
    wire start_r = (state == S_ACT) && accept && (op == 2'b10);
    wire sample  = (state == S_B_HI) && done;
    wire next    = (state == S_B_SET) && done && !last;
    wire       next_oe;        // SDA drive for the next bit
    wire [7:0] rbyte;          // READ: the byte read (valid at the end of the ACK bit)
    wire       ack_in;         // WRITE: the ACK bit read (1 = NACK)

    assign h_wready = ready;
    assign out_o    = 2'b00;

    generate
        if (PRIMS != 0) begin : g_prims
            localparam integer RELOAD_I = T2 - 1;
            localparam [15:0]  RELOAD   = RELOAD_I[15:0];
            reg        ackph;      // in the ACK bit
            reg        ack_out;    // READ: the ACK bit to send (1 = NACK)
            reg        ack_q;
            wire       sout, sdone;
            wire [7:0] q;
            WP_TIMER #(.RELOAD(RELOAD), .ONESHOT(1'b1)) u_timer (
                .clk(clk), .rst(!rst_n), .load(ld_t2 || ld_q), .half(ld_q), .en(1'b1), .tc(done));
            // WRITE: the byte shifts out MSB first while the sampled bits shift in. READ: SDA is
            // released for the data bits (the register's contents are not sent) and the register
            // ends holding the byte read.
            WP_SHIFT #(.LEN(4'd8), .MSB_FIRST(1'b1)) u_shift (
                .clk(clk), .rst(!rst_n), .load(start_w || start_r), .step(sample && !ackph),
                .sin(sda_i), .d(h_wdata), .sout(sout), .done(sdone), .q(q));
            always @(posedge clk) begin
                if (!rst_n) begin
                    ackph   <= 1'b0;
                    ack_out <= 1'b1;
                    ack_q   <= 1'b0;
                end else begin
                    if (start_w || start_r) ackph <= 1'b0;
                    else if (next && sdone) ackph <= 1'b1;
                    if (start_r) ack_out <= h_wdata[0];
                    if (sample && ackph) ack_q <= sda_i;
                end
            end
            assign last    = ackph;
            assign next_oe = is_read ? (sdone && !ack_out) : (!sdone && !sout);
            assign rbyte   = q;
            assign ack_in  = ack_q;
        end else begin : g_logic
            localparam CW = $clog2(T2 + 1);
            localparam integer T2_M1_I = T2 - 1;
            localparam integer Q_M1_I  = Q - 1;
            localparam [CW-1:0] T2_M1 = T2_M1_I[CW-1:0];
            localparam [CW-1:0] Q_M1  = Q_M1_I[CW-1:0];
            reg [CW-1:0] cnt;
            reg [7:0]    out_bits;   // bits still to send after the current one (data, then ACK); 1 = release
            reg [8:0]    in_bits;
            reg [3:0]    nbit;
            always @(posedge clk) begin
                if (!rst_n) begin
                    cnt      <= {CW{1'b0}};
                    out_bits <= 8'hFF;
                    in_bits  <= 9'h000;
                    nbit     <= 4'd0;
                end else begin
                    if (ld_t2)      cnt <= T2_M1;
                    else if (ld_q)  cnt <= Q_M1;
                    else if (!done) cnt <= cnt - 1'b1;
                    if (start_w) out_bits <= {h_wdata[6:0], 1'b1};
                    if (start_r) out_bits <= {7'h7F, h_wdata[0]};
                    if (start_w || start_r) nbit <= 4'd0;
                    if (sample) in_bits <= {in_bits[7:0], sda_i};
                    if (next) begin
                        nbit     <= nbit + 1'b1;
                        out_bits <= {out_bits[6:0], 1'b1};
                    end
                end
            end
            assign done    = (cnt == 0);
            assign last    = (nbit == 4'd8);
            assign next_oe = !out_bits[7];
            assign rbyte   = in_bits[8:1];
            assign ack_in  = in_bits[0];
        end
    endgenerate

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
            is_read   <= 1'b0;
            sda_oe    <= 1'b0;
            scl_oe    <= 1'b0;
            owned     <= 1'b0;
            err_q     <= 1'b0;
            overrun_q <= 1'b0;
            nack_q    <= 1'b0;
            h_rdata   <= 8'h00;
            h_rvalid  <= 1'b0;
        end else begin
            if (h_rvalid && h_rready) h_rvalid <= 1'b0;

            case (state)
                S_IDLE: if (accept) begin
                    if (op == 2'b00) begin            // START
                        sda_oe <= 1'b1;
                        state  <= S_ST_A;
                    end else err_q <= 1'b1;
                end

                S_ACT: if (accept) begin
                    case (op)
                        2'b00: begin                  // repeated START
                            sda_oe <= 1'b0;
                            state  <= S_RS_A;
                        end
                        2'b01: state <= S_WDATA;      // WRITE
                        2'b10: begin                  // READ
                            is_read <= 1'b1;
                            sda_oe  <= 1'b0;
                            state   <= S_B_LOW;
                        end
                        default: begin                // STOP
                            sda_oe <= 1'b1;
                            state  <= S_SP_A;
                        end
                    endcase
                end

                S_WDATA: if (accept) begin
                    is_read <= 1'b0;
                    sda_oe  <= !h_wdata[7];
                    state   <= S_B_LOW;
                end

                S_ST_A: if (done) begin
                    scl_oe <= 1'b1;
                    state  <= S_ST_B;
                end

                S_ST_B: if (done) begin
                    owned <= 1'b1;
                    state <= S_ACT;
                end

                S_RS_A: if (done) begin
                    scl_oe <= 1'b0;
                    state  <= S_RS_C;
                end

                S_RS_C: if (done) begin
                    sda_oe <= 1'b1;                   // SDA falls while SCL is high
                    state  <= S_ST_A;
                end

                S_SP_A: if (done) begin
                    scl_oe <= 1'b0;
                    state  <= S_SP_C;
                end

                S_SP_C: if (done) begin
                    sda_oe <= 1'b0;                   // SDA rises while SCL is high
                    state  <= S_SP_D;
                end

                S_SP_D: if (done) begin
                    owned <= 1'b0;
                    state <= S_IDLE;
                end

                S_B_LOW: if (done) begin
                    scl_oe <= 1'b0;
                    state  <= S_B_HI;
                end

                S_B_HI: if (done) begin
                    scl_oe <= 1'b1;                   // SCL falls; SDA changes only Q clocks later
                    state  <= S_B_SET;
                end

                S_B_SET: if (done) begin
                    if (last) begin
                        // 9 bits done: data byte and the ACK bit
                        sda_oe <= 1'b0;               // release SDA; SCL stays low between commands
                        if (is_read) push(rbyte);
                        else begin
                            push({7'b0, ack_in});
                            nack_q <= ack_in;
                        end
                        state <= S_ACT;
                    end else begin
                        sda_oe <= next_oe;            // next bit, while SCL is low
                        state  <= S_B_LOW;
                    end
                end

                default: state <= S_IDLE;
            endcase
        end
    end

    wire _unused = &{h_wlast, 1'b0};
    assign h_status = {4'b0, err_q, overrun_q, nack_q, owned};
endmodule
