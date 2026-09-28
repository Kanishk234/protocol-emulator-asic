// CAN 2.0A controller user design: held-out protocol H4 (docs/design/HELDOUT.md), written after
// hw-freeze for the frozen chip (phase 4). Base frames, data frames only.
//
// Bus:   rx_i reads the bus (from a transceiver's RXD; synchronized by the shell). The node drives
//        dominant with tx_oe = 1 (the pin's value is 0); released it reads recessive through a
//        pull-up (the transceiver's TXD input). Put it on a bidirectional pin: a `uo_out` pin
//        parks at 0 = dominant while the chip is stopped and would block the bus (BUGS #19).
// Bits:  BIT clocks per bit, sampled at mid-bit (hard synchronization on the frame's start edge;
//        no resynchronization inside a frame, so both ends need close clocks).
// Frame: SOF, 11-bit ID, RTR, IDE, r0, DLC, 0-8 data bytes, CRC-15, delimiters, ACK, EOF,
//        intermission; stuff bits after 5 equal bits from SOF through the CRC.
// Host:  transmit: the bytes on h_w* are the frame's bits after SOF, MSB first, up to the end of
//        the data (ID, RTR, IDE, r0, DLC, data = 18 + 8 x DLC bits in 3 + DLC bytes; the last
//        byte's top 2 bits are used); h_wlast on the last. The first byte starts a frame when
//        the bus is idle; the host must deliver each next byte within 8 bit times.
//        receive: every frame on the bus (including our own) comes back on h_r*, packed the
//        same way (the last byte holds 2 bits in its low bits); h_status tells whether it was
//        good.
//        On lost arbitration or a late byte the node stops driving and drops the rest of that
//        frame's host bytes (up to h_wlast); the host retries.
//        h_status = {crc_ok, acked, arb_lost, err, overrun, underrun, tx, busy}; the flags
//        refer to the last frame and clear when the next one starts.
// Uses:  two WP_TIMERs (sample point; bit boundary) and a WP_SHIFT (the bytes), ARCHITECTURE §8.
`default_nettype none

module can_top #(
    parameter BIT   = 20,
    parameter PRIMS = 0
) (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       rx_i,
    output reg        tx_oe,
    output wire       tx_o,
    // host -> design
    input  wire [7:0] h_wdata,
    input  wire       h_wlast,
    input  wire       h_wvalid,
    output wire       h_wready,
    // design -> host
    output wire [7:0] h_rdata,
    output reg        h_rvalid,
    input  wire       h_rready,
    output wire [7:0] h_status
);
    localparam [2:0] S_IDLE = 3'd0, S_FRAME = 3'd1, S_CRCDEL = 3'd2, S_ACK = 3'd3,
                     S_ACKDEL = 3'd4, S_EOF = 3'd5, S_FLUSH = 3'd6;

    reg  [2:0]  state;
    reg  [6:0]  pos;               // destuffed bits sampled in this frame (SOF = 1)
    reg  [3:0]  dlc;
    reg  [14:0] crc;
    reg  [2:0]  run;               // equal bits in a row (1..5)
    reg         last;              // the last destuffed bit
    reg         stuff_due;         // the next bit is a stuff bit
    reg  [3:0]  cnt;               // idle / EOF bits
    reg         tx_on;             // we are the transmitter
    reg         drive;             // our next level (0 = dominant)
    reg         crc_ok, acked, arb_lost, err_q, overrun_q, underrun_q;

    wire sample;                   // mid-bit
    wire boundary;                 // bit boundary
    wire sr_sout;
    wire [7:0] sr_q;

    wire bus     = rx_i;
    wire [6:0] data_end = 7'd18 + {dlc, 3'b000};        // last stream bit index
    wire [6:0] crc_end  = data_end + 7'd15;             // last CRC bit (SOF = 0 .. index)
    wire in_frame = state == S_FRAME;
    wire idle_ok  = cnt == 4'd11;
    // frame start: our own byte on an idle bus, or someone's SOF
    wire start_tx = state == S_IDLE && idle_ok && h_wvalid && !h_rvalid;
    wire start_rx = state == S_IDLE && !bus;
    wire start    = start_tx || start_rx;
    // stream bits (after SOF, to the end of the data) go through the shift register
    wire is_stream = in_frame && !stuff_due && pos >= 7'd1 && pos <= data_end;
    wire take_byte = boundary && in_frame && tx_on && !stuff_due && pos <= data_end
                     && pos[2:0] == 3'd1 && pos != 7'd1;        // next byte at stream bits 8k
    wire sr_step = sample && is_stream;

    assign h_wready = start_tx || take_byte || (state == S_FLUSH && h_wvalid);
    assign h_rdata  = sr_q;
    assign tx_o     = 1'b0;
    assign h_status = {crc_ok, acked, arb_lost, err_q, overrun_q, underrun_q, tx_on, state != S_IDLE};

    generate
        if (PRIMS != 0) begin : g_prims
            localparam integer R_I = BIT - 1;
            localparam integer H_I = BIT / 2 - 1;
            localparam [15:0]  R = R_I[15:0];
            localparam [15:0]  H = H_I[15:0];
            wire done_unused;
            // mid-bit sampling: loaded at the start edge with half, then periodic
            WP_TIMER #(.RELOAD(R), .ONESHOT(1'b0)) u_sample (
                .clk(clk), .rst(!rst_n), .load(start || state == S_IDLE), .half(1'b1), .en(1'b1),
                .tc(sample));
            // bit boundary: half a bit after each sample
            WP_TIMER #(.RELOAD(H), .ONESHOT(1'b1)) u_bound (
                .clk(clk), .rst(!rst_n), .load(sample), .half(1'b0), .en(1'b1), .tc(boundary));
            WP_SHIFT #(.LEN(4'd8), .MSB_FIRST(1'b1)) u_bytes (
                .clk(clk), .rst(!rst_n), .load(start_tx || take_byte), .step(sr_step), .sin(bus),
                .d(h_wdata), .sout(sr_sout), .done(done_unused), .q(sr_q));
            wire _unused_p = &{done_unused, 1'b0};
        end else begin : g_logic
            localparam integer W = $clog2(BIT);
            localparam integer R_I = BIT - 1;
            localparam integer H_I = BIT / 2 - 1;
            localparam [W-1:0] R = R_I[W-1:0];
            localparam [W-1:0] H = H_I[W-1:0];
            reg [W-1:0] sc, bc;
            reg         barmed;
            reg [7:0]   sr;
            always @(posedge clk) begin
                if (!rst_n) begin
                    sc <= R; bc <= H; barmed <= 1'b0; sr <= 8'h00;
                end else begin
                    if (start || state == S_IDLE) sc <= {1'b0, R[W-1:1]};
                    else if (sc == 0)             sc <= R;
                    else                          sc <= sc - 1'b1;
                    if (sample) begin bc <= H; barmed <= 1'b1; end
                    else if (barmed) begin
                        if (bc == 0) barmed <= 1'b0;
                        else         bc <= bc - 1'b1;
                    end
                    if (start_tx || take_byte) sr <= h_wdata;
                    else if (sr_step)          sr <= {sr[6:0], bus};
                end
            end
            assign sample   = state != S_IDLE && state != S_FLUSH && sc == 0;
            assign boundary = barmed && bc == 0;
            assign sr_sout  = sr[7];
            assign sr_q     = sr;
        end
    endgenerate

    // the level we drove for the bit being sampled; the last host byte of our frame
    reg drive_q, h_wlast_seen;
    always @(posedge clk) begin
        if (!rst_n) begin
            drive_q <= 1'b1; h_wlast_seen <= 1'b0;
        end else begin
            if (start) begin
                drive_q <= !start_tx;
                h_wlast_seen <= 1'b0;
            end else if (boundary) drive_q <= tx_on ? next_level : 1'b1;
            if (h_wready && h_wlast) h_wlast_seen <= 1'b1;
        end
    end
    // idle bit counting: one tick per bit time while idle (the sample timer runs free then)
    localparam integer IW = $clog2(BIT);
    localparam integer ID_I = BIT - 1;
    localparam [IW-1:0] IDR = ID_I[IW-1:0];
    reg [IW-1:0] idle_div;
    wire sample_idle = idle_div == {IW{1'b0}};
    always @(posedge clk) begin
        if (!rst_n || state != S_IDLE || !bus || sample_idle) idle_div <= IDR;
        else idle_div <= idle_div - 1'b1;
    end
    // the level we put on the bus for the next bit
    wire next_level = !tx_on                     ? 1'b1 :
                      stuff_due                  ? !last :
                      pos <= data_end            ? (take_byte ? h_wdata[7] : sr_sout) :
                                                   crc[14];

    always @(posedge clk) begin
        if (!rst_n) begin
            state <= S_IDLE; pos <= 7'd0; dlc <= 4'd0; crc <= 15'd0; run <= 3'd0; last <= 1'b1;
            stuff_due <= 1'b0; cnt <= 4'd0; tx_on <= 1'b0; drive <= 1'b1; tx_oe <= 1'b0;
            crc_ok <= 1'b0; acked <= 1'b0; arb_lost <= 1'b0; err_q <= 1'b0; overrun_q <= 1'b0;
            underrun_q <= 1'b0; h_rvalid <= 1'b0;
        end else begin
            if (h_rvalid && h_rready) h_rvalid <= 1'b0;
            case (state)
                S_IDLE: begin
                    // bus integration: 11 recessive bits (counted in bit times) before sending
                    if (!bus) cnt <= 4'd0;
                    else if (sample_idle && !idle_ok) cnt <= cnt + 1'b1;
                    if (start) begin
                        state <= S_FRAME;
                        pos <= 7'd0; crc <= 15'd0; run <= 3'd0; last <= 1'b1; stuff_due <= 1'b0;
                        crc_ok <= 1'b0; acked <= 1'b0; arb_lost <= 1'b0; err_q <= 1'b0;
                        underrun_q <= 1'b0;
                        tx_on <= start_tx;
                        tx_oe <= start_tx;                         // SOF: dominant
                    end
                end

                S_FRAME: begin
                    if (sample) begin
                        if (tx_on && bus != drive_q) begin         // we sent 1, the bus says 0
                            if (pos >= 7'd1 && pos <= 7'd12 && drive_q) begin
                                tx_on <= 1'b0; arb_lost <= 1'b1; tx_oe <= 1'b0;
                            end else begin
                                err_q <= 1'b1; tx_on <= 1'b0; tx_oe <= 1'b0; cnt <= 4'd0;
                                state <= S_FLUSH;
                            end
                        end
                        if (stuff_due) begin                       // a stuff bit: check, drop
                            if (bus == last) begin                 // stuff error
                                err_q <= 1'b1; tx_oe <= 1'b0; cnt <= 4'd0;
                                state <= tx_on ? S_FLUSH : S_IDLE;
                            end
                            stuff_due <= 1'b0;
                            last <= bus;
                            run  <= 3'd1;
                        end else begin
                            run  <= (bus == last) ? run + 1'b1 : 3'd1;
                            stuff_due <= (bus == last) && run == 3'd4;
                            last <= bus;
                            pos  <= pos + 1'b1;
                            crc  <= {crc[13:0], 1'b0} ^ ((bus ^ crc[14]) ? 15'h4599 : 15'h0);
                            if (pos >= 7'd15 && pos <= 7'd18) dlc <= {dlc[2:0], bus};
                            // a received byte is complete at stream bits 8k (and at the data end)
                            if (pos >= 7'd8 && pos <= data_end && (pos[2:0] == 3'd0 || pos == data_end)) begin
                                if (h_rvalid && !h_rready) overrun_q <= 1'b1;
                                h_rvalid <= 1'b1;
                            end
                            if (pos == crc_end) begin
                                crc_ok <= ({crc[13:0], 1'b0} ^ ((bus ^ crc[14]) ? 15'h4599 : 15'h0)) == 15'd0;
                                if (!((bus == last) && run == 3'd4)) state <= S_CRCDEL;
                            end
                        end
                        if (stuff_due && pos == crc_end + 7'd1) state <= S_CRCDEL;   // stuff after the CRC
                    end
                    if (boundary && state == S_FRAME) begin
                        if (take_byte && !h_wvalid) begin          // host late: stop sending
                            underrun_q <= 1'b1; tx_on <= 1'b0; tx_oe <= 1'b0;
                        end else if (tx_on) tx_oe <= !next_level;
                    end
                end

                S_CRCDEL: begin
                    if (boundary) tx_oe <= 1'b0;
                    if (sample) begin
                        if (!bus) err_q <= 1'b1;
                        state <= S_ACK;
                    end
                end

                S_ACK: begin
                    if (boundary) tx_oe <= !tx_on && crc_ok;       // receivers acknowledge
                    if (sample) begin
                        if (tx_on) acked <= !bus;
                        state <= S_ACKDEL;
                    end
                end

                S_ACKDEL: begin
                    if (boundary) tx_oe <= 1'b0;
                    if (sample) begin
                        cnt   <= 4'd0;
                        state <= S_EOF;
                    end
                end

                S_EOF: if (sample) begin                           // 7 EOF + 3 intermission
                    if (cnt == 4'd9) begin
                        cnt   <= 4'd11;
                        state <= (tx_on || arb_lost || underrun_q) && !h_wlast_seen ? S_FLUSH : S_IDLE;
                    end else cnt <= cnt + 1'b1;
                end

                S_FLUSH: begin                                     // drop the rest of our frame
                    tx_oe <= 1'b0;
                    if (h_wvalid && h_wlast) begin
                        cnt   <= 4'd0;
                        state <= S_IDLE;
                    end
                end

                default: state <= S_IDLE;
            endcase
        end
    end

    wire _unused = &{drive, 1'b0};
endmodule
