// Area-estimate building blocks (phase 2 task 2.0). NOT chip RTL: each module is a
// representative datapath piece, written from ARCHITECTURE.md §4, §7, §9 and §14, sized to
// what the spec needs, and synthesized alone onto the cmos5l cells to get an area per piece.
// spikes/area/estimate.py multiplies them by the counts each chip block needs.
// Configuration values arrive on ports: their storage is priced separately (per bit).
`default_nettype none

// 16.8 scheduler: next event time accumulates PERIOD (bit clock, sample point, carrier).
module ae_timer (
    input  wire        clk, rst_n, load, step,
    input  wire [23:0] base, period,
    input  wire [15:0] now,
    output wire        due,
    output wire [23:0] t
);
    reg [23:0] nxt;
    always @(posedge clk)
        if (!rst_n)    nxt <= 24'd0;
        else if (load) nxt <= base;
        else if (step) nxt <= nxt + period;
    assign due = (nxt[23:8] == now);
    assign t = nxt;
endmodule

// TX cursor (P4): cursor := max(cursor + delta, earliest), delta in 1/256 clocks, plus the
// PRESC tick prescaler and a 12-bit tick countdown for delay·PRESC without a multiplier.
module ae_cursor (
    input  wire        clk, rst_n, adv, tick_start,
    input  wire [23:0] delta,
    input  wire [15:0] now,
    input  wire [7:0]  presc_m1,
    input  wire [11:0] ticks,
    output wire        late, ticks_done,
    output wire [23:0] cur
);
    reg [23:0] c;
    reg [7:0]  pc;
    reg [11:0] tc;
    wire [23:0] sum = c + delta;
    wire [23:0] earliest = {now + 16'd1, 8'd0};
    wire        past = sum < earliest;
    always @(posedge clk)
        if (!rst_n) begin c <= 0; pc <= 0; tc <= 0; end
        else begin
            if (adv) c <= past ? earliest : sum;
            if (tick_start) begin tc <= ticks; pc <= presc_m1; end
            else if (tc != 0) begin
                if (pc == 0) begin pc <= presc_m1; tc <= tc - 12'd1; end
                else pc <= pc - 8'd1;
            end
        end
    assign late = adv && past;
    assign ticks_done = (tc == 0);
    assign cur = c;
endmodule

// TX shifter: 16-bit load, LSB/MSB order, 5-bit bit counter against NBITS (or length-in-token).
module ae_txshift (
    input  wire        clk, rst_n, load, shift, msb, lentok,
    input  wire [15:0] d,
    input  wire [4:0]  nbits,
    output wire        bit_out, done
);
    reg [15:0] s;
    reg [4:0]  n;
    wire [4:0] len = lentok ? {1'b0, d[15:12]} + 5'd1 : nbits;
    always @(posedge clk)
        if (!rst_n) begin s <= 0; n <= 0; end
        else if (load) begin s <= lentok ? {4'd0, d[11:0]} : d; n <= len; end
        else if (shift && n != 0) begin
            s <= msb ? {s[14:0], 1'b0} : {1'b0, s[15:1]};
            n <= n - 5'd1;
        end
    // MSB order starts at bit len-1 of the loaded word
    wire [4:0] top = n - 5'd1;
    assign bit_out = msb ? s[top[3:0]] : s[0];
    assign done = (n == 0);
endmodule

// RX framing (P13): bit written at its index (LSB order) or shifted in (MSB order), word
// length RX_NBITS / RX_NBITS2 / SETN override, taint bit, word-complete strobe.
module ae_rxframe (
    input  wire        clk, rst_n, clr, samp, bit_in, msb, taint_in, setn,
    input  wire [4:0]  nb1, nb2, nset,
    output reg  [15:0] w,
    output wire        full,
    output reg         tainted
);
    reg [4:0] cnt, ovr;
    reg       phase, use_ovr;
    wire [4:0] len = use_ovr ? ovr : (phase && nb2 != 0) ? nb2 : nb1;
    assign full = samp && (cnt + 5'd1 == len);
    always @(posedge clk)
        if (!rst_n) begin w <= 0; cnt <= 0; phase <= 0; tainted <= 0; ovr <= 0; use_ovr <= 0; end
        else if (clr || setn) begin
            cnt <= 0; phase <= 0; tainted <= 0;
            if (setn) begin ovr <= nset; use_ovr <= 1'b1; end
        end
        else if (samp) begin
            if (msb) w <= {w[14:0], bit_in};
            else     w[cnt[3:0]] <= bit_in;
            tainted <= (full ? 1'b0 : tainted) | taint_in;
            if (full) begin cnt <= 0; phase <= ~phase; end
            else cnt <= cnt + 5'd1;
        end
endmodule

// Runtime-configurable CRC (P24/P25): MSB-first LFSR, width 1..16, poly/init/res from config.
module ae_crc (
    input  wire        clk, rst_n, init, en, bit_in,
    input  wire [15:0] poly, init_v, res,
    input  wire [4:0]  width,
    output wire        match,
    output wire [15:0] r_out
);
    reg  [15:0] r;
    wire [3:0]  top = width[3:0] - 4'd1;
    wire [15:0] mask = (width >= 5'd16) ? 16'hFFFF : ((16'd1 << width) - 16'd1);
    wire        fb = r[top] ^ bit_in;
    always @(posedge clk)
        if (!rst_n)    r <= 0;
        else if (init) r <= init_v & mask;
        else if (en)   r <= (({r[14:0], 1'b0}) ^ (fb ? poly : 16'd0)) & mask;
    assign match = ((r ^ res) & mask) == 16'd0;
    assign r_out = r;
endmodule

// BITSYNC bit-level control (P20–P23, P27–P29): stuff run counters (TX and RX), idle counter,
// destuffed frame counter against FRAME n, resync step limited by SJW, NRZI state, JAM counter.
module ae_bitsync (
    input  wire        clk, rst_n, bitstart, samp, lvl, txbit, edge_, frame_set,
    input  wire [3:0]  stuff_n,
    input  wire [4:0]  idle_bits,
    input  wire [10:0] frame_n,
    input  wire [23:0] sjw, phase_err,
    input  wire [3:0]  jam_n,
    output wire        stuff_due_tx, stuff_due_rx, idle, frame_end, jam_on,
    output wire [23:0] adj
);
    reg [3:0]  run_tx, run_rx, jam_c;
    reg        last_tx, last_rx, nrzi;
    reg [4:0]  idle_c;
    reg [10:0] fcnt;
    always @(posedge clk)
        if (!rst_n) begin
            run_tx <= 0; run_rx <= 0; last_tx <= 0; last_rx <= 0; idle_c <= 0; fcnt <= 0;
            nrzi <= 0; jam_c <= 0;
        end else begin
            if (bitstart) begin
                run_tx <= (txbit == last_tx) ? run_tx + 4'd1 : 4'd1; last_tx <= txbit;
                nrzi <= nrzi ^ ~txbit;
                if (jam_c != 0) jam_c <= jam_c - 4'd1;
            end
            if (samp) begin
                run_rx <= (lvl == last_rx) ? run_rx + 4'd1 : 4'd1; last_rx <= lvl;
                idle_c <= lvl ? ((idle_c == 5'd31) ? idle_c : idle_c + 5'd1) : 5'd0;
                if (!stuff_due_rx) fcnt <= fcnt + 11'd1;
            end
            if (frame_set) begin fcnt <= 0; jam_c <= jam_n; end
        end
    assign stuff_due_tx = (stuff_n != 0) && (run_tx == stuff_n);
    assign stuff_due_rx = (stuff_n != 0) && (run_rx == stuff_n);
    assign idle = (idle_c >= idle_bits);
    assign frame_end = (fcnt == frame_n);
    assign jam_on = (jam_c != 0);
    // resync: move the bit start by min(|phase error|, SJW) toward the edge
    wire [23:0] mag = phase_err[23] ? -phase_err : phase_err;
    wire [23:0] lim = (mag > sjw) ? sjw : mag;
    assign adj = edge_ ? (phase_err[23] ? -lim : lim) : 24'd0;
endmodule

// PULSE symbol timer (P17): two 12-bit tick phases per bit, chosen by the bit value.
module ae_pulse (
    input  wire        clk, rst_n, start, tick, b,
    input  wire [11:0] s0t1, s0t2, s1t1, s1t2,
    output reg         ph,
    output wire        bit_done
);
    reg [11:0] c;
    wire [11:0] t1 = b ? s1t1 : s0t1;
    wire [11:0] t2 = b ? s1t2 : s0t2;
    always @(posedge clk)
        if (!rst_n) begin c <= 0; ph <= 0; end
        else if (start) begin c <= t1; ph <= 0; end
        else if (tick) begin
            if (c <= 12'd1) begin
                if (!ph) begin ph <= 1'b1; c <= t2; end
                else c <= 0;
            end else c <= c - 12'd1;
        end
    assign bit_done = ph && (c == 0);
endmodule

// Pad select for one unit input (pin A, B, C or S): 5-bit pad number, 19 synchronized pads,
// plus the unit's own edge detector on it.
module ae_padsel (
    input  wire        clk, rst_n,
    input  wire [18:0] pads,
    input  wire [4:0]  sel,
    output wire        v, rise, fall
);
    wire cur = (sel < 5'd19) ? pads[sel] : 1'b0;
    reg  prev;
    always @(posedge clk) if (!rst_n) prev <= 1'b0; else prev <= cur;
    assign v = cur; assign rise = cur & ~prev; assign fall = ~cur & prev;
endmodule

// Event generator (P8): 15-bit tick counter with prescaler, qualifier history, token word.
module ae_event (
    input  wire        clk, rst_n, tick, a_edge, a_lvl, b_lvl, qual_en, qual_lvl,
    output wire        fire,
    output wire [15:0] tok
);
    reg [14:0] tcnt;
    reg        bprev;
    always @(posedge clk)
        if (!rst_n) begin tcnt <= 0; bprev <= 0; end
        else begin bprev <= b_lvl; if (tick) tcnt <= tcnt + 15'd1; end
    assign fire = a_edge && (!qual_en || (b_lvl == qual_lvl && bprev == qual_lvl));
    assign tok = {a_lvl, tcnt};
endmodule

// Producer register (§4.2): valid, tag, data, seq; free when every blocking subscriber took it.
module ae_prod (
    input  wire        clk, rst_n, load, all_taken,
    input  wire [17:0] d,
    output reg  [17:0] q,
    output reg         valid, seq,
    output wire        free
);
    assign free = !valid || all_taken;
    always @(posedge clk)
        if (!rst_n) begin q <= 0; valid <= 0; seq <= 0; end
        else if (load && free) begin q <= d; valid <= 1'b1; seq <= ~seq; end
endmodule

// Consumer port (§4.3, F7) with N legal sources: source mux, availability, accept filter,
// last_seq, tap DROPPED counter. sel/en/mode/accept are configuration (priced per bit).
module ae_port #(parameter N = 8) (
    input  wire          clk, rst_n, take, en, tap,
    input  wire [3:0]    sel, accept,
    input  wire [N*18-1:0] src_d,
    input  wire [N-1:0]  src_v, src_seq,
    output wire          avail,
    output wire [17:0]   head,
    output wire          taken_me,
    output reg  [7:0]    dropped
);
    reg        last;
    wire       sv  = (sel < N) ? src_v[sel]   : 1'b0;
    wire       ss  = (sel < N) ? src_seq[sel] : 1'b0;
    assign head    = (sel < N) ? src_d[sel*18 +: 18] : 18'd0;
    wire       new_ = en && sv && (last != ss);
    wire       ok  = accept[head[17:16]];
    assign avail   = new_ && ok;
    assign taken_me = (last == ss);
    reg        prev_seq;
    always @(posedge clk)
        if (!rst_n) begin last <= 0; dropped <= 0; prev_seq <= 0; end
        else begin
            prev_seq <= ss;
            if ((avail && take) || (new_ && !ok)) last <= ss;
            // a new token replaced one this tap never took
            if (tap && sv && (ss != prev_seq) && (last != prev_seq) && dropped != 8'hFF)
                dropped <= dropped + 8'd1;
        end
endmodule

// Output pad driver (§7.1, trw_pins): owner register selects one of 6 units' value/OE; open drain.
module ae_padout (
    input  wire [5:0] u_val, u_oe,
    input  wire [2:0] owner,
    input  wire       od,
    output wire       val, oe
);
    wire v = (owner < 3'd6) ? u_val[owner] : 1'b0;
    wire e = (owner < 3'd6) ? u_oe[owner]  : 1'b0;
    assign val = od ? 1'b0 : v;
    assign oe  = od ? (e & ~v) : e;
endmodule

// Configuration storage: N bits written 16 at a time by the host (flop version; the latch
// version is priced from the R1 slot array).
module ae_cfg #(parameter W = 22) (
    input  wire          clk, rst_n, we,
    input  wire [4:0]    addr,
    input  wire [15:0]   wd,
    output wire [W*16-1:0] q
);
    reg [15:0] r [0:W-1];
    genvar i;
    generate for (i = 0; i < W; i = i + 1) begin : g
        always @(posedge clk)
            if (!rst_n) r[i] <= 16'd0;
            else if (we && addr == i) r[i] <= wd;
        assign q[i*16 +: 16] = r[i];
    end endgenerate
endmodule

// Host read-back mux: W 16-bit words onto the SPI read path.
module ae_rdmux #(parameter W = 22) (
    input  wire [W*16-1:0] words,
    input  wire [7:0]      addr,
    output wire [15:0]     rd
);
    assign rd = (addr < W) ? words[addr*16 +: 16] : 16'd0;
endmodule

// Host SPI slave (§9): input synchronizers, byte shifter, command, 16-bit auto-increment
// address, 16-bit data shifter in both directions, word strobes.
module ae_spi (
    input  wire        clk, rst_n, csn_p, sck_p, mosi_p,
    input  wire [15:0] rdata,
    output wire        miso,
    output reg         wr_stb, rd_stb,
    output reg  [15:0] addr, wdata,
    output reg  [7:0]  cmd
);
    reg [2:0] s_cs, s_sck, s_mosi;
    always @(posedge clk) begin
        s_cs <= {s_cs[1:0], csn_p}; s_sck <= {s_sck[1:0], sck_p}; s_mosi <= {s_mosi[1:0], mosi_p};
    end
    wire rise = s_sck[1] & ~s_sck[2];
    wire fall = ~s_sck[1] & s_sck[2];
    wire cs = ~s_cs[1];
    reg [15:0] sh, tx;
    reg [5:0]  bitc;
    reg [2:0]  st;
    always @(posedge clk)
        if (!rst_n || !cs) begin sh <= 0; bitc <= 0; st <= 0; wr_stb <= 0; rd_stb <= 0; tx <= 0; end
        else begin
            wr_stb <= 0; rd_stb <= 0;
            if (rise) begin
                sh <= {sh[14:0], s_mosi[1]};
                bitc <= bitc + 6'd1;
                if (st == 0 && bitc == 6'd7)  begin cmd <= {sh[6:0], s_mosi[1]}; st <= 1; bitc <= 0; end
                if (st == 1 && bitc == 6'd15) begin addr <= {sh[14:0], s_mosi[1]}; st <= cmd[7] ? 3'd2 : 3'd3; bitc <= 0; end
                if (st == 3 && bitc == 6'd7)  begin st <= 3'd2; bitc <= 0; rd_stb <= 1'b1; end
                if (st == 2 && bitc == 6'd15) begin
                    bitc <= 0; addr <= addr + 16'd1;
                    if (cmd[7]) begin wdata <= {sh[14:0], s_mosi[1]}; wr_stb <= 1'b1; end
                    else rd_stb <= 1'b1;
                end
            end
            if (rd_stb) tx <= rdata;
            else if (fall && st == 2) tx <= {tx[14:0], 1'b0};
        end
    assign miso = tx[15];
endmodule
