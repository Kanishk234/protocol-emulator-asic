// SWD host bit engine (Arm Serial Wire Debug) user design: held-out protocol H3
// (docs/design/HELDOUT.md), written after hw-freeze for the frozen chip (phase 4).
//
// The fabric does SWD's physical layer: SWCLK, SWDIO driven / released / sampled at the right
// edges, turnaround cycles, bits LSB first. Packets (request bits, parity, ACK decisions, WAIT
// retries, posted AP reads) are the host's: tools/board/swd.py, like a debug probe's firmware.
//
// Pins:  swclk_o (FAB_OUT0); swdio on FAB_IO0: swdio_o / swdio_oe out, swdio_i in (synchronized
//        by the shell). One SWCLK cycle = HALF clocks low, then HALF clocks high; the host's
//        data changes at the falling edge, the target samples at the rising edge; the target's
//        data is sampled at the end of the low half (just before the rising edge).
// Host:  command bytes on h_w*: bits 7:5 op, bits 2:0 = n - 1 (1..8 bits):
//          3'b000  WRITE n bits: the next byte on h_w* is driven, LSB first
//          3'b001  READ n bits: SWDIO released; the reply on h_r* holds the bits in its top n
//                  bits (the host shifts right by 8 - n)
//          3'b010  TURN: one SWCLK cycle with SWDIO released (a turnaround)
//          other   ignored, sets the sticky `err` bit
//        Between commands SWCLK stays low and SWDIO keeps its last state. A command is taken
//        only when the previous READ's reply has been read.
//        h_status = {5'b0, err, 1'b0, busy}.
// Uses:  a WP_TIMER (the SWCLK half period) and a WP_SHIFT (the byte), ARCHITECTURE §8.
//        PRIMS = 0: the same in plain logic.
`default_nettype none

module swd_top #(
    parameter HALF  = 4,
    parameter PRIMS = 0
) (
    input  wire       clk,
    input  wire       rst_n,
    output reg        swclk_o,
    output wire       swdio_o,
    output reg        swdio_oe,
    input  wire       swdio_i,
    // host -> design
    input  wire [7:0] h_wdata,
    input  wire       h_wvalid,
    output wire       h_wready,
    // design -> host
    output wire [7:0] h_rdata,
    output reg        h_rvalid,
    input  wire       h_rready,
    output wire [7:0] h_status
);
    localparam [1:0] S_IDLE = 2'd0, S_WDATA = 2'd1, S_RUN = 2'd2;

    reg  [1:0] state;
    reg  [1:0] op;                 // 0 write, 1 read, 2 turn
    reg  [2:0] nm1, cnt;           // bits - 1, bits done
    reg        ph;                 // 0: SWCLK low half, 1: high half
    reg        err_q;

    wire tick;                     // a half period ends
    wire sr_sout;
    wire [7:0] sr_q;

    wire can_take = (state == S_IDLE && !h_rvalid) || state == S_WDATA;
    wire accept   = h_wvalid && can_take;
    wire cmd_ok   = h_wdata[7:5] <= 3'd2;
    wire start_w  = accept && state == S_WDATA;
    wire start_rt = accept && state == S_IDLE && cmd_ok && h_wdata[7:5] != 3'd0;
    wire rise     = state == S_RUN && tick && !ph;     // end of the low half
    wire fall     = state == S_RUN && tick && ph;      // end of the high half
    wire last     = cnt == nm1;
    wire sr_load  = start_w || (accept && state == S_IDLE && h_wdata[7:5] == 3'd1);
    wire sr_step  = (op == 2'd0 && fall) || (op == 2'd1 && rise);

    assign h_wready = accept;
    assign h_rdata  = sr_q;
    assign swdio_o  = sr_sout;
    assign h_status = {5'b0, err_q, 1'b0, state != S_IDLE};

    generate
        if (PRIMS != 0) begin : g_prims
            localparam integer R_I = HALF - 1;
            localparam [15:0]  R   = R_I[15:0];
            wire done_unused;
            WP_TIMER #(.RELOAD(R), .ONESHOT(1'b0)) u_half (
                .clk(clk), .rst(!rst_n), .load(state != S_RUN), .half(1'b0), .en(1'b1), .tc(tick));
            WP_SHIFT #(.LEN(4'd8), .MSB_FIRST(1'b0)) u_bits (
                .clk(clk), .rst(!rst_n), .load(sr_load), .step(sr_step), .sin(swdio_i),
                .d(h_wdata), .sout(sr_sout), .done(done_unused), .q(sr_q));
            wire _unused_p = &{done_unused, 1'b0};
        end else begin : g_logic
            localparam integer W = (HALF > 1) ? $clog2(HALF) : 1;
            localparam integer R_I = HALF - 1;
            localparam [W-1:0] R = R_I[W-1:0];
            reg [W-1:0] hc;
            reg [7:0]   sr;
            always @(posedge clk) begin
                if (!rst_n) begin
                    hc <= R; sr <= 8'h00;
                end else begin
                    if (state != S_RUN || hc == 0) hc <= R;
                    else                           hc <= hc - 1'b1;
                    if (sr_load)      sr <= h_wdata;
                    else if (sr_step) sr <= {swdio_i, sr[7:1]};
                end
            end
            assign tick    = state == S_RUN && hc == 0;
            assign sr_sout = sr[0];
            assign sr_q    = sr;
        end
    endgenerate

    always @(posedge clk) begin
        if (!rst_n) begin
            state    <= S_IDLE;
            op       <= 2'd0;
            nm1      <= 3'd0;
            cnt      <= 3'd0;
            ph       <= 1'b0;
            swclk_o  <= 1'b0;
            swdio_oe <= 1'b0;
            err_q    <= 1'b0;
            h_rvalid <= 1'b0;
        end else begin
            if (h_rvalid && h_rready) h_rvalid <= 1'b0;
            case (state)
                S_IDLE: if (accept) begin
                    nm1 <= h_wdata[2:0];
                    cnt <= 3'd0;
                    ph  <= 1'b0;
                    op  <= h_wdata[6:5];
                    if (!cmd_ok) err_q <= 1'b1;
                    else if (h_wdata[7:5] == 3'd0) state <= S_WDATA;
                    else begin
                        swdio_oe <= 1'b0;                  // READ / TURN: released
                        state    <= S_RUN;
                    end
                end

                S_WDATA: if (accept) begin
                    swdio_oe <= 1'b1;                      // WRITE: drive from the first bit
                    state    <= S_RUN;
                end

                S_RUN: if (tick) begin
                    if (!ph) begin                         // rising edge
                        swclk_o <= 1'b1;
                        ph      <= 1'b1;
                    end else begin                         // falling edge
                        swclk_o <= 1'b0;
                        ph      <= 1'b0;
                        cnt     <= cnt + 1'b1;
                        if (last) begin
                            if (op == 2'd1) h_rvalid <= 1'b1;
                            state <= S_IDLE;
                        end
                    end
                end

                default: state <= S_IDLE;
            endcase
        end
    end

    wire _unused = &{start_rt, 1'b0};
endmodule
