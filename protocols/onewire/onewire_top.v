// 1-Wire controller (master) user design: held-out protocol H2 (docs/design/HELDOUT.md),
// written after hw-freeze for the frozen chip (phase 4). Standard speed.
//
// Line:  one open-drain pin: dq_oe = 1 pulls the line low, 0 releases it (external pull-up);
//        dq_i reads it (synchronized by the shell). dq_o is always 0.
// Slots (AN126 timings; microseconds):
//        reset: low 480, release, presence sampled 70 after the release, then 960 of recovery;
//        write: low from 0, released at 6 (a 1) or 60 (a 0), slot ends at 70;
//        read:  low 0-6, released, the line sampled at 15, slot ends at 70.
//        Bits LSB first.
// Host:  command bytes on h_w*, decoded on bits 7:6:
//          2'b00  RESET: the line reset; afterwards h_status[3] = presence (a device answered)
//          2'b01  WRITE: the next byte on h_w* goes out in 8 write slots
//          2'b10  READ: 8 read slots; the byte is the reply on h_r*
//          2'b11  ignored, sets the sticky `err` bit
//        The host waits for h_status[0] (busy) to clear before the next command.
//        h_status = {4'b0, presence, err, 1'b0, busy}.
// Uses:  two WP_TIMERs: a 1 us tick, and a microsecond one-shot (RELOAD 959 us; its half load
//        is the 480 us reset pulse) for the reset; a WP_SHIFT for the byte (ARCHITECTURE §8).
//        PRIMS = 0: the same in plain logic. US = clocks per microsecond (50 at 50 MHz).
`default_nettype none

module onewire_top #(
    parameter US    = 50,
    parameter PRIMS = 0
) (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       dq_i,
    output reg        dq_oe,
    output wire       dq_o,
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
    localparam [2:0] S_IDLE = 3'd0, S_WDATA = 3'd1, S_RLOW = 3'd2, S_RWAIT = 3'd3,
                     S_WBIT = 3'd4, S_RBIT = 3'd5;

    reg  [2:0] state;
    reg  [6:0] t;                  // microseconds into a slot (or since the reset's release)
    reg  [2:0] nslot;              // slots done in this byte
    reg        presence, psampled, err_q;

    wire us_tick;                  // one per microsecond
    wire long_tc;                  // the reset one-shot has run out
    wire sr_bit;                   // the bit to write now
    wire [7:0] sr_q;

    wire idle     = state == S_IDLE || state == S_WDATA;
    wire accept   = h_wvalid && idle;
    wire cmd_rst  = accept && state == S_IDLE && h_wdata[7:6] == 2'b00;
    wire start_w  = accept && state == S_WDATA;
    wire start_r  = accept && state == S_IDLE && h_wdata[7:6] == 2'b10;
    wire slot_end = us_tick && t == 7'd69;
    wire in_slot  = state == S_WBIT || state == S_RBIT;
    wire rsample  = us_tick && t == 7'd14 && state == S_RBIT;
    wire sr_step  = (state == S_WBIT && slot_end) || rsample;
    // the reset one-shot: half load (480 us) at the command, full load (960 us) at the release
    wire long_load = cmd_rst || (state == S_RLOW && long_tc);

    assign h_wready = accept;
    assign dq_o     = 1'b0;
    assign h_rdata  = sr_q;
    assign h_status = {4'b0, presence, err_q, 1'b0, !idle};

    generate
        if (PRIMS != 0) begin : g_prims
            localparam integer R_I = US - 1;
            localparam [15:0]  R   = R_I[15:0];
            wire sout, done_unused;
            WP_TIMER #(.RELOAD(R), .ONESHOT(1'b0)) u_us (
                .clk(clk), .rst(!rst_n), .load(idle), .half(1'b0), .en(1'b1), .tc(us_tick));
            WP_TIMER #(.RELOAD(16'd959), .ONESHOT(1'b1)) u_long (
                .clk(clk), .rst(!rst_n), .load(long_load), .half(cmd_rst), .en(us_tick),
                .tc(long_tc));
            WP_SHIFT #(.LEN(4'd8), .MSB_FIRST(1'b0)) u_byte (
                .clk(clk), .rst(!rst_n), .load(start_w || start_r), .step(sr_step), .sin(dq_i),
                .d(h_wdata), .sout(sout), .done(done_unused), .q(sr_q));
            assign sr_bit = sout;
            wire _unused_p = &{done_unused, 1'b0};
        end else begin : g_logic
            localparam integer UW = $clog2(US);
            localparam integer R_I = US - 1;
            localparam [UW-1:0] R = R_I[UW-1:0];
            reg [UW-1:0] ucnt;
            reg [9:0]    lcnt;
            reg          larmed;
            reg [7:0]    sr;
            always @(posedge clk) begin
                if (!rst_n) begin
                    ucnt <= R; lcnt <= 10'd959; larmed <= 1'b0; sr <= 8'h00;
                end else begin
                    if (idle || ucnt == 0) ucnt <= R;
                    else                   ucnt <= ucnt - 1'b1;
                    if (long_load) begin
                        lcnt   <= cmd_rst ? 10'd479 : 10'd959;
                        larmed <= 1'b1;
                    end else if (us_tick && larmed) begin
                        if (lcnt == 0) larmed <= 1'b0;
                        else           lcnt <= lcnt - 1'b1;
                    end
                    if (start_w || start_r) sr <= h_wdata;
                    else if (sr_step)       sr <= {dq_i, sr[7:1]};
                end
            end
            assign us_tick = !idle && ucnt == 0;
            assign long_tc = us_tick && larmed && lcnt == 0;
            assign sr_bit  = sr[0];
            assign sr_q    = sr;
        end
    endgenerate

    always @(posedge clk) begin
        if (!rst_n) begin
            state    <= S_IDLE;
            t        <= 7'd0;
            nslot    <= 3'd0;
            dq_oe    <= 1'b0;
            presence <= 1'b0;
            psampled <= 1'b0;
            err_q    <= 1'b0;
            h_rvalid <= 1'b0;
        end else begin
            if (h_rvalid && h_rready) h_rvalid <= 1'b0;
            if (us_tick) t <= t + 1'b1;

            case (state)
                S_IDLE: if (accept) begin
                    t     <= 7'd0;
                    nslot <= 3'd0;
                    case (h_wdata[7:6])
                        2'b00: begin state <= S_RLOW; dq_oe <= 1'b1; end
                        2'b01: state <= S_WDATA;
                        2'b10: begin state <= S_RBIT; dq_oe <= 1'b1; end
                        default: err_q <= 1'b1;
                    endcase
                end

                S_WDATA: if (accept) begin                   // the data byte
                    t     <= 7'd0;
                    dq_oe <= 1'b1;
                    state <= S_WBIT;
                end

                S_RLOW: if (long_tc) begin                   // 480 us low: release
                    dq_oe    <= 1'b0;
                    t        <= 7'd0;
                    psampled <= 1'b0;
                    state    <= S_RWAIT;
                end

                S_RWAIT: begin                               // presence at 70 us, then recovery
                    // once, 70 us after the release (t wraps during the recovery)
                    if (us_tick && t == 7'd69 && !psampled) begin
                        presence <= !dq_i;
                        psampled <= 1'b1;
                    end
                    if (long_tc) state <= S_IDLE;
                end

                S_WBIT, S_RBIT: if (us_tick) begin
                    if (t == 7'd5 && (state == S_RBIT || sr_bit)) dq_oe <= 1'b0;
                    if (t == 7'd59) dq_oe <= 1'b0;
                    if (t == 7'd69) begin                    // slot end
                        t     <= 7'd0;
                        nslot <= nslot + 1'b1;
                        if (nslot == 3'd7) begin
                            if (state == S_RBIT) h_rvalid <= 1'b1;
                            state <= S_IDLE;
                        end else dq_oe <= 1'b1;              // next slot
                    end
                end

                default: state <= S_IDLE;
            endcase
        end
    end

    wire _unused = &{in_slot, 1'b0};
endmodule
