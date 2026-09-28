// WS2812 (NeoPixel) transmitter user design: held-out protocol H1 (docs/design/HELDOUT.md),
// written after hw-freeze for the frozen chip (phase 4).
//
// Line:  dout_o, idle low. Each bit: high for T1H clocks (a 1) or about T1H/2 clocks (a 0),
//        then low for the rest of a TBIT-clock period; bytes MSB first (the host sends G, R, B
//        per LED). A frame ends with the line low for RESET_BITS bit periods (the LEDs latch).
// Host:  h_w* bytes to send, streamed: the design has no pixel buffer (the fabric has no room
//        for one), so the host must deliver the next byte within one byte time (8 x TBIT
//        clocks, 10 us at the standard rate). h_wlast = 1 marks a frame's last byte: after it,
//        the reset gap. If the next byte is late inside a frame, the line stays low (the LEDs
//        latch what they have) and the sticky `underrun` flag is set; sending continues when
//        the byte arrives, as a new frame.
//        h_status = {6'b0, underrun, busy}.
// Uses:  two WP_TIMERs (bit period; high time, whose `half` load gives the 0-bit's pulse from
//        the 1-bit's RELOAD) and one WP_SHIFT (the byte), ARCHITECTURE §8. PRIMS = 0: the same
//        in plain logic.
// Rate:  at 50 MHz: TBIT = 62 (1.24 us), T1H = 40 (0.80 us; a 0 is 0.40 us), RESET_BITS = 45.
`default_nettype none

module ws2812_top #(
    parameter TBIT       = 62,
    parameter T1H        = 40,
    parameter RESET_BITS = 45,
    parameter PRIMS      = 0
) (
    input  wire       clk,
    input  wire       rst_n,
    output reg        dout_o,
    // host -> design
    input  wire [7:0] h_wdata,
    input  wire       h_wlast,
    input  wire       h_wvalid,
    output wire       h_wready,
    output wire [7:0] h_status
);
    localparam [1:0] S_IDLE = 2'd0, S_SEND = 2'd1, S_GAP = 2'd2;
    localparam integer GW = $clog2(RESET_BITS + 1);
    localparam integer RB_I = RESET_BITS;
    localparam [GW-1:0] RB = RB_I[GW-1:0];

    reg [1:0]    state;
    reg          last_q, underrun_q;
    reg [GW-1:0] gap;

    wire bit_tick;             // a bit period ends (state SEND/GAP)
    wire high_end;             // the current bit's high time ends
    wire byte_done;            // all bits of the current byte have been started
    wire cur_bit;              // the next bit of the current byte
    // a byte is taken when the line is idle, or right at the end of a byte
    wire take  = h_wvalid && (state == S_IDLE ||
                              (state == S_SEND && bit_tick && byte_done && !last_q));
    wire nextb = state == S_SEND && bit_tick && !byte_done;   // the next bit of this byte
    // the bit that starts now: bit 7 of a byte just taken, else the shift register's next bit
    wire start_bit = take ? h_wdata[7] : cur_bit;
    wire bit_start = take || nextb;

    assign h_wready = take;
    assign h_status = {6'b0, underrun_q, state != S_IDLE};

    generate
        if (PRIMS != 0) begin : g_prims
            localparam integer P_I = TBIT - 1;
            localparam integer H_I = T1H - 1;
            localparam [15:0]  P_R = P_I[15:0];
            localparam [15:0]  H_R = H_I[15:0];
            wire [7:0] q_unused;
            wire       sout;
            // bit period: held at its start while idle (load keeps tc low), free running
            // otherwise; en is tied high so tc does not depend on the state logic (timing)
            WP_TIMER #(.RELOAD(P_R), .ONESHOT(1'b0)) u_period (
                .clk(clk), .rst(!rst_n), .load(state == S_IDLE), .half(1'b0),
                .en(1'b1), .tc(bit_tick));
            // high time: one shot per bit; half load for a 0
            WP_TIMER #(.RELOAD(H_R), .ONESHOT(1'b1)) u_high (
                .clk(clk), .rst(!rst_n), .load(bit_start), .half(!start_bit),
                .en(1'b1), .tc(high_end));
            // the byte's bits 6..0 (bit 7 goes out as the byte is taken)
            WP_SHIFT #(.LEN(4'd7), .MSB_FIRST(1'b1)) u_bits (
                .clk(clk), .rst(!rst_n), .load(take), .step(nextb), .sin(1'b0),
                .d({h_wdata[6:0], 1'b0}), .sout(sout), .done(byte_done), .q(q_unused));
            assign cur_bit = sout;
            wire _unused_p = &{q_unused, 1'b0};
        end else begin : g_logic
            localparam integer PW = $clog2(TBIT);
            localparam integer HW = $clog2(T1H);
            localparam integer P_I = TBIT - 1;
            localparam integer H_I = T1H - 1;
            localparam [PW-1:0] P_R = P_I[PW-1:0];
            localparam [HW-1:0] H_R = H_I[HW-1:0];
            reg [PW-1:0] pcnt;
            reg [HW-1:0] hcnt;
            reg          harmed;
            reg [7:0]    sr;
            reg [2:0]    n;
            always @(posedge clk) begin
                if (!rst_n) begin
                    pcnt <= P_R; hcnt <= H_R; harmed <= 1'b0; sr <= 8'h00; n <= 3'd0;
                end else begin
                    if (state == S_IDLE)     pcnt <= P_R;
                    else if (pcnt == 0)      pcnt <= P_R;
                    else                     pcnt <= pcnt - 1'b1;
                    if (bit_start) begin
                        hcnt   <= start_bit ? H_R : {1'b0, H_R[HW-1:1]};
                        harmed <= 1'b1;
                    end else if (harmed) begin
                        if (hcnt == 0) harmed <= 1'b0;
                        else           hcnt <= hcnt - 1'b1;
                    end
                    if (take) begin
                        sr <= {h_wdata[6:0], 1'b0};
                        n  <= 3'd0;
                    end else if (nextb) begin
                        sr <= {sr[6:0], 1'b0};
                        if (n != 3'd7) n <= n + 1'b1;
                    end
                end
            end
            assign bit_tick  = state != S_IDLE && pcnt == 0;
            assign high_end  = harmed && hcnt == 0;
            assign byte_done = n == 3'd7;
            assign cur_bit   = sr[7];
        end
    endgenerate

    always @(posedge clk) begin
        if (!rst_n) begin
            state      <= S_IDLE;
            dout_o     <= 1'b0;
            last_q     <= 1'b0;
            underrun_q <= 1'b0;
            gap        <= {GW{1'b0}};
        end else begin
            if (bit_start)     dout_o <= 1'b1;
            else if (high_end) dout_o <= 1'b0;
            if (take) begin
                state  <= S_SEND;
                last_q <= h_wlast;
            end else begin
                case (state)
                    S_SEND: if (bit_tick && byte_done) begin     // byte finished, no next byte
                        if (!last_q) underrun_q <= 1'b1;
                        gap   <= RB;
                        state <= S_GAP;
                    end
                    S_GAP: if (bit_tick) begin
                        if (gap == 0) state <= S_IDLE;
                        else          gap <= gap - 1'b1;
                    end
                    default: ;
                endcase
            end
        end
    end
endmodule
