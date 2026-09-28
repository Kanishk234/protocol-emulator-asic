#!/usr/bin/env bash
# L7-style mutation check of the pin unit: each mutant is one injected bug in a copy of src/; the L1
# suite must fail on every one. Usage (in the venv): [FULL=1] [ONLY=<text>] test_internal/pin/mutate.sh
# (the milestone B mutants, labelled "B1:", need FULL=1: FULL=1 ONLY=B1 test_internal/pin/mutate.sh)
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
WORK="$(mktemp -d)"
# file # sed expression # what it breaks
MUTANTS=(
  "trw_pin_tx.v#s/(!m_pulse \&\& tail \&\& (bt_i <= 16'd1))/(!m_pulse \&\& tail \&\& (bt_i == 16'd0))/#P3: take one clock late after a shift"
  "trw_pin_tx.v#s/assign late_set = tk_late/assign late_set = 1'b0 \&\& tk_late/#P4: LATE never set"
  "trw_pin_tx.v#s/wire \[FRAC-1:0\] p_frac = tk_late ? {FRAC{1'b0}} : cf_b;/wire [FRAC-1:0] p_frac = {FRAC{1'b0}};/#P4: cursor fraction dropped"
  "trw_pin_rx.v#s/wire taint = ftaint_b || echo;/wire taint = ftaint_b;/#P13: echo taint ignored"
  "trw_pin_rx.v#s/wire ev = edge_ok \&\& qual_ok;/wire ev = edge_ok;/#P8: EV_QUAL ignored"
  "trw_pin_rx.v#s/(want \&\& !rx_free) || //#4.5: OVERRUN on a full producer"
  "trw_pin_tx.v#s/end else if (!p_first \&\& stretch) begin/end else if (1'b0) begin/#P11: STRETCH ignored"
  "trw_pin_tx.v#s/lk_pre <= tk \&\& h_lk \&\& tx_preload/lk_pre <= 1'b0 \&\& tx_preload/#P9: preload ignored"
  "trw_pin_tx.v#s/wire lk_abort = linked \&\& sel_fall/wire lk_abort = 1'b0 \&\& sel_fall/#P15: deselect abort ignored"
  "trw_pin_rx.v#s/wire \[RW-1:0\] rt_cur = start ? sofs : rt;/wire [RW-1:0] rt_cur = start ? sofs + 24'd256 : rt;/#P5: sample one clock late"
  "trw_pin_tx.v#s/wire w_fire = w_v \&\& (w_rise ? b_rise : b_fall);/wire w_fire = w_v \&\& (b_rise || b_fall);/#P16: WAIT on either edge"
  "trw_pin_tx.v#s/wire \[0:0\] nlvx = d_hi ? (d_hi_v ^ idle) : due_lvl_v ? (due_lvl ^ idle) : d_lo ? 1'b0 : lvx;/wire [0:0] nlvx = d_hi ? (d_hi_v ^ idle) : d_lo ? 1'b0 : due_lvl_v ? (due_lvl ^ idle) : lvx;/#P4: return-to-IDLE beats a LEVEL on its edge"
  "trw_pin_tx.v#s/    wire clk_run = m_clk \&\& p_act; /    wire clk_run = m_clk \&\& p_act \&\& !p_end; /#P34: a CLK in the release clock starts a new burst"
  "trw_pin_rx.v#s/    wire        evr      = ev \&\& ev_reset;/    wire        evr      = 1'b0;/; s/    wire rst_fr = !sel || rxset; /    wire rst_fr = !sel || rxset || (ev \&\& ev_reset); /#P38: EV_RESET after the event clock's sample"
  "trw_pin_tx.v#s/    wire linked  = m_shift \&\& ((tx_edge == \`TRW_PCE_TX_EDGE_RISE) || (tx_edge == \`TRW_PCE_TX_EDGE_FALL));/    wire linked  = m_shift \&\& (tx_edge != 2'd0);/#P43: TX_EDGE 3 acts as linked"
  "trw_pin_tx.v#s/                else if (lk_idle || (lk_edge/                else if (due_lvl_v || lk_idle || (lk_edge/#P44: a LEVEL cancels the pending return to IDLE"
  "trw_pin_tx.v#s/    wire d_hi_v = (s_bit || lk_bit) ? bit_o : pb1 ? pl_first : pb2 ? !pl_first : (ph ? !idle : idle);/    wire d_hi_v = (s_bit || lk_bit) ? bit_o : pb1 ? pl_first : pb2 ? pl_first : (ph ? !idle : idle);/#B1: P17 PULSE second level not inverted"
  "trw_pin_tx.v#s/                    ps    <= (p_tn == 12'd0) ? 8'd0 : presc;/                    ps    <= 8'd0;/#B1: P17 PULSE phases ignore PRESC"
  "trw_pin_tx.v#s/                || (p_tail \&\& (pt == 12'd0) \&\& (ps <= 8'd1)) || (p_lastb \&\& p_t2one);/                ;/#B1: P17 back-to-back PULSE tokens leave a gap"
  "trw_pin_tx.v#s/            end else if (!lvx) begin/            end else if (1'b0) begin/#B1: P30 carrier phase does not restart"
  "trw_pin_tx.v#s/                ct  <= ct + {1'b0, carrier} - 25'd512;/                ct  <= {ct[24:9], 9'd0} + {1'b0, carrier} - 25'd512;/#B1: P30 carrier fraction dropped"
  "trw_pin_tx.v#s/    wire m_pulse = (FULL != 0) \&\& (txmode == \`TRW_PCE_TXMODE_PULSE);/    wire m_pulse = (txmode == \`TRW_PCE_TXMODE_PULSE);/#B1: D-040 a lean unit runs PULSE"
  "trw_pin_bs.v#s/    wire        rs_do = rs_edge \&\& (d != 25'd0);/    wire        rs_do = 1'b0 \&\& rs_edge \&\& (d != 25'd0);/#B2: P22 no resync"
  "trw_pin_bs.v#s/    wire hsync   = f_start;/    wire hsync   = 1'b0;/#B2: P21 no hard sync of the bit clock"
  "trw_pin_bs.v#s/    wire        done = !hsync \&\& smp_done;/    wire        done = smp_done;/#B2: P21 hard sync does not re-arm the sample"
  "trw_pin_bs.v#s/    wire        goes_idle = smp \&\& rec \&\& (icnt_r >= idle_bits)/    wire        goes_idle = 1'b0 \&\& smp \&\& rec \&\& (icnt_r >= idle_bits)/#B2: P20 idle never ends a frame"
  "trw_pin_bs.v#s/    wire \[15:0\] w1       = order ? {w\[14:0\], bit_in} : (w | ({15'd0, bit_in} << wn));/    wire [15:0] w1       = {w[14:0], bit_in};/#B2: RX word ORDER ignored"
  "trw_pin_bs.v#s/    wire \[24:0\] d    = !smp_done ? ((e < sj) ? e : sj)/    wire [24:0] d    = !smp_done ? sj/#B2: P22 resync moves by SJW, not by the phase error"
  "trw_pin_bs.v#s/    wire        fbit     = smp \&\& in_frame \&\& !goes_idle;/    wire        fbit     = smp \&\& in_frame;/#B2: P-G29 the idle-making sample completes a word"
  "trw_pin_bs.v#s/    wire        dbit     = fbit \&\& !s_due \&\& open_fr;/    wire        dbit     = fbit \&\& !s_err \&\& open_fr;/#B2: P23 stuff bits not removed"
  "trw_pin_bs.v#s/    wire        s_err    = fbit \&\& s_due \&\& (bit_in == rl);/    wire        s_err    = 1'b0;/#B2: P23 stuff errors not detected"
  "trw_pin_bs.v#s/crc\[ctop\] ? crc_poly : 16'd0/crc[ctop] ? 16'd1 : 16'd0/g#B2: P24 CRC polynomial ignored"
  "trw_pin_bs.v#s/    wire        v_tok    = at_n \&\& words_on;/    wire        v_tok    = 1'b0;/#B2: P24 no verdict at FRAME's n"
  "trw_pin_bs.v#s/                        post     <= 1'b1;/                        post     <= 1'b0;/#B2: P24 no stuff check right after bit n"
  "trw_pin_bs.v#s/    wire        lvl_ok   = !stuff_lvl\[1\] || (rl == stuff_lvl\[0\]);/    wire        lvl_ok   = 1'b1;/#B2: P23 STUFF_LVL ignored"
  "trw_pin_bs.v#s/    wire        c_in     = dbit \&\& (dcnt >= {6'd0, crc_skip})/    wire        c_in     = dbit/#B2: P24 CRC_SKIP ignored"
  "trw_pin_bs.v#s/    assign late_set = f_now \&\& (!in_frame || !words_on || (dcnt >= arg\[10:0\]));/    assign late_set = 1'b0;/#B2: P24 FRAME never LATE"
  "trw_pin_bs.v#s/    wire own_lvl = drv \&\& (a_in == tlv);/    wire own_lvl = 1'b0;/#B2: P22 resync on the echo of our own edges"
  "trw_pin_bs.v#s/(idle_bits != 5'd0) \&\& !drv;/(idle_bits != 5'd0);/#B2: P20 idle ends a frame while we drive a bit"
  "trw_pin_bs.v#s/    wire        jn       = f_start/    wire        jn       = 1'b0 \&\& f_start/#B2: P21 no join of another node's frame start"
  "trw_pin_bs.v#s/(q_any \&\& (!sync_p || bus_idle))/q_any/#B2: P21 a SYNC frame does not wait for bus idle"
  "trw_pin_bs.v#s/            if (f_start || o_start) begin/            if (f_start) begin/#B2: P21 our frame start left to the echo (hard sync on our own edge)"
  "trw_pin_bs.v#s/    wire        sync_ev  = ((o_start \&\& sync_p) || jn) \&\& live;/    wire        sync_ev  = 1'b0 \&\& live;/#B2: P21 no EVENT 0x9001"
  "trw_pin_bs.v#s/    wire        ts_due   = ts_on \&\&/    wire        ts_due   = 1'b0 \&\& ts_on \&\&/#B2: P25 no TX stuffing"
  "trw_pin_bs.v#s/                ts_on <= arg\[2\];/                ts_on <= arg[2];  if (!arg[2]) ts_p <= 1'b0;/#B2: P25 a LINE drops the stuff bit due before it"
  "trw_pin_bs.v#s/k_crc ? ((crc_src ^ crc_xor) \& cmask)/k_crc ? (crc_src \& cmask)/#B2: P25 CRC_XOR ignored"
  "trw_pin_bs.v#s/    wire \[15:0\] crc_src  = arg\[6\] ? (crc_init \& cmask) : tcrc;/    wire [15:0] crc_src  = tcrc;/#B2: P25 LINE [3] before [6]"
  "trw_pin_bs.v#s/                if (arg\[6\])$/                if (1'b0)/#B2: P25 LINE [6] does not reset the TX CRC"
  "trw_pin_bs.v#s/: (order ? pay : pay_r);/: pay;/#B2: P25 TX ORDER ignored"
  "trw_pin_bs.v#s/    wire \[4:0\]  nb       = (tx_lentok ? /    wire [4:0]  nb       = (1'b0 ? /#B2: P25 TX_LENTOK ignored"
  "trw_pin_bs.v#s/    wire        tx_ok   = (qn == 5'd0) \&\& /    wire        tx_ok   = /#B2: P25 a TX token taken while bits are queued"
  "trw_pin_bs.v#s/            if (k_wait)$/            if (1'b0)/#B2: P25 WAIT [1] ignored"
  "trw_pin_bs.v#s/(qn == 5'd0) \&\& (!wt_p || smp);/(qn == 5'd0) \&\& !wt_p;/#B2: P-G31 WAIT [1] releases a clock after the sample point"
)
killed=0
survived=0
for m in "${MUTANTS[@]}"; do
  IFS="#" read -r file expr what <<< "$m"
  [ -n "${ONLY:-}" ] && [[ "$what" != *"$ONLY"* ]] && continue
  # milestone B feature mutants need the full build; the D-040 fallback mutant needs the lean one
  if [ "${FULL:-0}" = 1 ]; then [[ "$what" == "B1: D-040"* ]] && continue; else [[ "$what" == B[0-9]*": P"* ]] && continue; fi      # ONLY=<text>: just the matching mutants
  rm -rf "$WORK/src"; cp -r "$ROOT/src" "$WORK/src"
  sed -i "$expr" "$WORK/src/$file"
  if cmp -s "$ROOT/src/$file" "$WORK/src/$file"; then echo "NOT APPLIED: $what"; continue; fi
  (cd "$HERE" && make FULL="${FULL:-0}" SRC_DIR="$WORK/src" SIM_BUILD="$WORK/build" COCOTB_RESULTS_FILE="$WORK/r.xml" >"$WORK/log" 2>&1)
  if grep -q "FAIL=0" "$WORK/log"; then echo "SURVIVED: $what"; survived=$((survived+1)); else
    echo "killed ($(grep -o 'FAIL=[0-9]*' "$WORK/log")): $what"; killed=$((killed+1)); fi
done
echo "mutation: $killed killed, $survived survived (FULL=${FULL:-0})"
rm -rf "$WORK"
