// R1 risk spike (throwaway): one lane, 12 reflex slots, EVAL/EXEC, shared ALU.
//
// Written from ISA.md §2-§5 and ARCHITECTURE.md §5, §14 (L1-L7, R4) only.
//   EVAL (clock n): all 12 ready() terms (§4.2) -> group mask (§4.3) -> one priority encoder ->
//                   static updates at edge n: STATE := NS, dequeue, output reservation, PEND[DF] := 1,
//                   CALL sets RB; the selected action fields, the A input head (or time) are latched.
//   EXEC (clock n+1): registers and K read, ALU, write r[d] / load O0|O1 / f[DF] (clears PEND[DF]).
// A waiting routine step (RIR, from the sequencer) competes at EVAL: urgent ready slots beat it,
// it beats non-urgent slots (§4.3, §5.3). It executes in EXEC like a slot action.
// Out of scope for the spike: the routine sequencer (RPC, fetch, BR/LD/ST, the SRAM rotation), the
// host debug path, and the R1 fallback (fire every other clock).
`default_nettype none
`include "trw_defs.vh"

module trw_lane (
    input  wire                         clk,
    input  wire                         rst_n,
    input  wire                         run,
    input  wire [12*`TRW_SLOT_BITS-1:0] slots,
    input  wire [63:0]                  k,             // {K3, K2, K1, K0}
    input  wire [15:0]                  time_now,
    // input ports I0, I1 (from consumer ports): {I1, I0}, each {tag[1:0], data[15:0]}
    input  wire [1:0]                   in_avail,
    input  wire [35:0]                  in_head,
    output wire [1:0]                   in_take,
    // output ports O0, O1 (producer registers, depth 1): {O1, O0}
    input  wire [1:0]                   out_all_taken, // §4.4, from the subscribers' registered state
    output reg  [1:0]                   out_valid,
    output reg  [1:0]                   out_seq,
    output reg  [35:0]                  out_tok,
    // routine interface (the sequencer is outside the spike)
    input  wire                         rir_valid,
    input  wire [15:0]                  rir,
    output wire                         rt_take,       // the step won EVAL; it executes next clock
    output wire                         rt_nz,         // DJNZ in EXEC: the decremented value != 0
    output reg                          rz,
    output reg                          call_req,
    output reg  [4:0]                   call_idx,
    output wire                         rb_o,
    // host debug read (ARCHITECTURE.md §9, lane register block): {pend, f3..f0, state, r3..r0}
    output wire [74:0]                  dbg
);
    localparam SB = `TRW_SLOT_BITS;

    // ---------------------------------------------------------------- lane state
    reg [63:0] regs;        // {r3, r2, r1, r0}
    reg [3:0]  state;
    reg [2:0]  f;           // f2..f0
    reg        rb;          // f3: routine busy
    reg [2:0]  pend;        // PEND for f2..f0
    reg [1:0]  resv;        // output reservations

    // EXEC stage, loaded at EVAL
    reg        ex_slot, ex_rt;
    reg [3:0]  ex_op;
    reg [2:0]  ex_dst, ex_asrc;
    reg [1:0]  ex_bsel, ex_df, ex_ot;
    reg [7:0]  ex_imm;
    reg        ex_dfe, ex_kt;
    reg [15:0] a_lat;       // slot: A input head data or time; routine step: the instruction word
    reg [1:0]  a_tag;

    wire [3:0] flags = {rb, f};
    assign rb_o = rb;
    assign dbg  = {pend, flags, state, regs};

    // ---------------------------------------------------------------- EVAL
    // L7: an output is free when it is not reserved and its producer is free (F3).
    wire [1:0] ofree;
    assign ofree[0] = !resv[0] && (!out_valid[0] || out_all_taken[0]);
    assign ofree[1] = !resv[1] && (!out_valid[1] || out_all_taken[1]);

    wire [11:0] ready, urgent;
    genvar i;
    generate
        for (i = 0; i < 12; i = i + 1) begin : g_cond
            /* verilator lint_off UNUSEDSIGNAL */   // the action fields are used after selection
            wire [SB-1:0] s    = slots[i*SB +: SB];
            /* verilator lint_on UNUSEDSIGNAL */
            wire       v       = s[`TRW_SLOT_V_LSB];
            wire       se      = s[`TRW_SLOT_SE_LSB];
            wire [3:0] sv      = s[`TRW_SLOT_SV_MSB:`TRW_SLOT_SV_LSB];
            wire [3:0] fm      = s[`TRW_SLOT_FM_MSB:`TRW_SLOT_FM_LSB];
            wire [3:0] fv      = s[`TRW_SLOT_FV_MSB:`TRW_SLOT_FV_LSB];
            wire       te      = s[`TRW_SLOT_TE_LSB];
            wire [1:0] tag     = s[`TRW_SLOT_TAG_MSB:`TRW_SLOT_TAG_LSB];
            wire       he      = s[`TRW_SLOT_HE_LSB];
            wire       hv      = s[`TRW_SLOT_HV_LSB];
            wire       hs      = s[`TRW_SLOT_HS_LSB];
            wire [3:0] op      = s[`TRW_SLOT_OP_MSB:`TRW_SLOT_OP_LSB];
            wire [2:0] dst     = s[`TRW_SLOT_DST_MSB:`TRW_SLOT_DST_LSB];
            wire [2:0] asrc    = s[`TRW_SLOT_ASRC_MSB:`TRW_SLOT_ASRC_LSB];

            wire       a_in    = (asrc[2:1] == 2'b10);          // I0 or I1
            wire       hsel    = asrc[0];
            wire       h_av    = hsel ? in_avail[1] : in_avail[0];
            wire [1:0] h_tag   = hsel ? in_head[35:34] : in_head[17:16];
            wire       h_bit   = hs ? (hsel ? in_head[18] : in_head[0])      // data[0]
                                    : (hsel ? in_head[33] : in_head[15]);    // data[15]
            // O0 or O1; CALL ignores DST, so it never waits for an output (§14 L10)
            wire       d_out   = (dst[2:1] == 2'b10) && (op != `TRW_OP_CALL);

            wire explicit_ok = v
                            && (!se || (state == sv))
                            && (((flags ^ fv) & fm) == 4'd0)
                            && (({1'b0, pend} & fm) == 4'd0);                // pending rule
            wire in_ok   = !a_in || (h_av && (!te || (h_tag == tag)) && (!he || (h_bit == hv)));
            wire out_ok  = !d_out || ofree[dst[0]];
            wire call_ok = (op != `TRW_OP_CALL) || !rb;

            assign ready[i]  = run && explicit_ok && in_ok && out_ok && call_ok;
            assign urgent[i] = s[`TRW_SLOT_U_LSB];
        end
    endgenerate

    // A routine OUT step is a candidate only while its output is free (it stays in RIR and retries).
    wire rt_is_out = rir[15] && (rir[14:12] == `TRW_RT_SUB_OUT);
    wire rt_ok     = run && rir_valid && (!rt_is_out || ofree[rir[11]]);

    // §4.3: with a step waiting only urgent slots can beat it; one lowest-index encoder either way.
    wire [11:0] cand   = ready & (rt_ok ? urgent : 12'hFFF);
    wire [11:0] onehot = cand & (~cand + 12'd1);
    wire        fire   = |cand;
    assign rt_take     = rt_ok && !fire;

    reg [SB-1:0] ss;        // the selected slot
    integer j;
    always @* begin
        ss = {SB{1'b0}};
        for (j = 0; j < 12; j = j + 1)
            ss = ss | ({SB{onehot[j]}} & slots[j*SB +: SB]);
    end

    wire [3:0] s_op   = ss[`TRW_SLOT_OP_MSB:`TRW_SLOT_OP_LSB];
    wire [2:0] s_dst  = ss[`TRW_SLOT_DST_MSB:`TRW_SLOT_DST_LSB];
    wire [2:0] s_asrc = ss[`TRW_SLOT_ASRC_MSB:`TRW_SLOT_ASRC_LSB];
    wire       s_dq   = ss[`TRW_SLOT_DQ_LSB];
    wire [1:0] s_bsel = ss[`TRW_SLOT_BSEL_MSB:`TRW_SLOT_BSEL_LSB];
    wire [7:0] s_imm  = ss[`TRW_SLOT_IMM_MSB:`TRW_SLOT_IMM_LSB];
    wire       s_nse  = ss[`TRW_SLOT_NSE_LSB];
    wire [3:0] s_ns   = ss[`TRW_SLOT_NS_MSB:`TRW_SLOT_NS_LSB];
    wire       s_dfe  = ss[`TRW_SLOT_DFE_LSB];
    wire [1:0] s_df   = ss[`TRW_SLOT_DF_MSB:`TRW_SLOT_DF_LSB];
    wire [1:0] s_ot   = ss[`TRW_SLOT_OT_MSB:`TRW_SLOT_OT_LSB];
    wire       s_kt   = ss[`TRW_SLOT_KT_LSB];

    wire s_a_in  = (s_asrc[2:1] == 2'b10);
    // §14 L10: CALL ignores DST (no reservation, no output load) and DFE (no PEND, no flag write).
    wire s_is_call = (s_op == `TRW_OP_CALL);
    wire s_d_out   = (s_dst[2:1] == 2'b10) && !s_is_call;
    wire s_fw      = s_dfe && (s_df != 2'd3) && !s_is_call;
    assign in_take[0] = fire && s_dq && s_a_in && !s_asrc[0];
    assign in_take[1] = fire && s_dq && s_a_in &&  s_asrc[0];

    wire [15:0] head_data = s_asrc[0] ? in_head[33:18] : in_head[15:0];
    wire [1:0]  head_tag  = s_asrc[0] ? in_head[35:34] : in_head[17:16];

    // ---------------------------------------------------------------- EXEC
    // Routine word fields (ISA.md §5.1); the word is in a_lat while ex_rt.
    wire       rt_ctl  = a_lat[15];
    wire [2:0] rt_sub  = a_lat[14:12];
    wire [1:0] rt_rd_a = a_lat[10:9];    // ALU word
    wire [1:0] rt_rd_c = a_lat[11:10];   // LDI, LDIH, DJNZ
    wire [1:0] rt_ra   = a_lat[8:7];     // ALU word, OUT
    wire       rt_bs   = a_lat[6];
    wire [5:0] rt_b    = a_lat[5:0];
    wire [3:0] rt_fn   = a_lat[11:8];
    wire [7:0] rt_arg  = a_lat[7:0];
    wire       rt_djnz = ex_rt && rt_ctl && (rt_sub == `TRW_RT_SUB_DJNZ);

    reg  [3:0]  alu_op;
    reg  [15:0] alu_a, alu_b;
    reg  [7:0]  alu_f;
    always @* begin
        if (ex_rt) begin
            if (rt_ctl) begin                   // DJNZ: rd - 1 (other control words do not use the ALU)
                alu_op = `TRW_OP_SUB;
                alu_a  = regs[16*rt_rd_c +: 16];
                alu_b  = 16'd1;
                alu_f  = 8'd0;
            end else begin
                alu_op = a_lat[14:11];
                alu_a  = regs[16*rt_ra +: 16];
                alu_b  = rt_bs ? {10'd0, rt_b} : regs[16*rt_b[1:0] +: 16];
                alu_f  = rt_bs ? {2'd0, rt_b}  : regs[16*rt_b[1:0] +: 8];
            end
        end else begin
            alu_op = ex_op;
            alu_a  = !ex_asrc[2] ? regs[16*ex_asrc[1:0] +: 16]
                   : (ex_asrc == `TRW_ASRC_ZERO) ? 16'd0 : a_lat;
            // B source index: IMM[1:0] for BSEL reg / k (not stated in ISA.md; see the R1 report).
            case (ex_bsel)
                `TRW_BSEL_REG: alu_b = regs[16*ex_imm[1:0] +: 16];
                `TRW_BSEL_IMM: alu_b = {8'd0, ex_imm};
                `TRW_BSEL_K:   alu_b = k[16*ex_imm[1:0] +: 16];
                default:       alu_b = 16'd0;
            endcase
            alu_f  = ex_imm;
        end
    end

    wire [15:0] alu_rf = regs[16*alu_f[5:4] +: 16];
    wire [15:0] alu_m  = alu_f[4] ? k[16*alu_f[1:0] +: 16] : regs[16*alu_f[1:0] +: 16];
    wire [15:0] alu_v  = alu_f[4] ? k[16*alu_f[3:2] +: 16] : regs[16*alu_f[3:2] +: 16];
    wire [15:0] alu_d;
    wire        alu_r;

    trw_alu u_alu (
        .op (alu_op), .a (alu_a), .b (alu_b), .f (alu_f), .rf (alu_rf), .m (alu_m), .v (alu_v),
        .d  (alu_d),  .r (alu_r)
    );
    assign rt_nz = rt_djnz && !alu_r;

    wire       ex_d_reg  = ex_slot && !ex_dst[2] && (ex_op != `TRW_OP_CALL);
    wire       ex_d_out  = ex_slot && (ex_dst[2:1] == 2'b10) && (ex_op != `TRW_OP_CALL);
    // §14 L8: MKCTL always emits CTRL; KT keeps the latched head tag only when ASRC is I0 or I1,
    // otherwise KT is ignored and OT gives the tag.
    wire       ex_a_in   = (ex_asrc[2:1] == 2'b10);
    wire [1:0] ex_out_tag = (ex_op == `TRW_OP_MKCTL) ? `TRW_TAG_CTRL
                          : (ex_kt && ex_a_in)       ? a_tag
                          :                            ex_ot;
    wire       ex_fw     = ex_slot && ex_dfe && (ex_df != 2'd3) && (ex_op != `TRW_OP_CALL);

    wire rt_alu  = ex_rt && !rt_ctl && (a_lat[14:11] != `TRW_OP_CALL);
    wire rt_ldi  = ex_rt &&  rt_ctl && (rt_sub == `TRW_RT_SUB_LDI);
    wire rt_ldih = ex_rt &&  rt_ctl && (rt_sub == `TRW_RT_SUB_LDIH);
    wire rt_out  = ex_rt &&  rt_ctl && (rt_sub == `TRW_RT_SUB_OUT);
    wire rt_sys  = ex_rt &&  rt_ctl && (rt_sub == `TRW_RT_SUB_SYS);
    wire [1:0] rt_fi = rt_arg[1:0];

    // ---------------------------------------------------------------- registers
    always @(posedge clk) begin
        if (!rst_n) begin
            regs      <= 64'd0;
            state     <= 4'd0;
            f         <= 3'd0;
            rb        <= 1'b0;
            pend      <= 3'd0;
            resv      <= 2'd0;
            ex_slot   <= 1'b0;
            ex_rt     <= 1'b0;
            ex_op     <= 4'd0;
            ex_dst    <= 3'd0;
            ex_asrc   <= 3'd0;
            ex_bsel   <= 2'd0;
            ex_df     <= 2'd0;
            ex_ot     <= 2'd0;
            ex_imm    <= 8'd0;
            ex_dfe    <= 1'b0;
            ex_kt     <= 1'b0;
            a_lat     <= 16'd0;
            a_tag     <= 2'd0;
            out_valid <= 2'd0;
            out_seq   <= 2'd0;
            out_tok   <= 36'd0;
            rz        <= 1'b0;
            call_req  <= 1'b0;
            call_idx  <= 5'd0;
        end else begin
            // ---- EXEC writes (L5); EVAL's static updates below win where both apply
            if (ex_d_reg)
                regs[16*ex_dst[1:0] +: 16] <= alu_d;
            if (ex_d_out) begin
                out_valid[ex_dst[0]]         <= 1'b1;
                out_seq[ex_dst[0]]           <= ~out_seq[ex_dst[0]];
                out_tok[18*ex_dst[0] +: 18]  <= {ex_out_tag, alu_d};
                resv[ex_dst[0]]              <= 1'b0;
            end
            if (ex_fw) begin
                f[ex_df]    <= alu_r;
                pend[ex_df] <= 1'b0;
            end
            if (rt_alu) begin
                regs[16*rt_rd_a +: 16] <= alu_d;
                rz <= alu_r;
            end
            if (rt_ldi)
                regs[16*rt_rd_c +: 16] <= {6'd0, a_lat[9:0]};
            if (rt_ldih)
                regs[16*rt_rd_c +: 16] <= {a_lat[5:0], regs[16*rt_rd_c +: 10]};
            if (rt_djnz)
                regs[16*rt_rd_c +: 16] <= alu_d;
            if (rt_out) begin
                out_valid[a_lat[11]]        <= 1'b1;
                out_seq[a_lat[11]]          <= ~out_seq[a_lat[11]];
                out_tok[18*a_lat[11] +: 18] <= {a_lat[10:9], regs[16*rt_ra +: 16]};
                resv[a_lat[11]]             <= 1'b0;
            end
            if (rt_sys) begin
                case (rt_fn)
                    `TRW_SYS_RET:   rb    <= 1'b0;
                    `TRW_SYS_SETST: state <= rt_arg[3:0];
                    `TRW_SYS_SETF:  if (rt_fi != 2'd3) f[rt_fi] <= 1'b1;
                    `TRW_SYS_CLRF:  if (rt_fi != 2'd3) f[rt_fi] <= 1'b0;
                    `TRW_SYS_TSTF:  rz <= flags[rt_fi];
                    `TRW_SYS_CPYF:  if (rt_fi != 2'd3) f[rt_fi] <= rz;
                    `TRW_SYS_GETT:  regs[16*rt_fi +: 16] <= time_now;
                    `TRW_SYS_GETK:  regs[16*rt_fi +: 16] <= k[16*rt_arg[3:2] +: 16];
                    default: ;
                endcase
            end

            // ---- EVAL static updates (L4, L6)
            ex_slot  <= fire;
            ex_rt    <= rt_take;
            call_req <= fire && (s_op == `TRW_OP_CALL);
            if (fire) begin
                ex_op   <= s_op;
                ex_dst  <= s_dst;
                ex_asrc <= s_asrc;
                ex_bsel <= s_bsel;
                ex_imm  <= s_imm;
                ex_dfe  <= s_dfe;
                ex_df   <= s_df;
                ex_ot   <= s_ot;
                ex_kt   <= s_kt;
                a_lat   <= (s_asrc == `TRW_ASRC_TIME) ? time_now : head_data;
                a_tag   <= head_tag;
                if (s_nse)
                    state <= s_ns;                              // R4: the reflex update wins
                if (s_d_out)
                    resv[s_dst[0]] <= 1'b1;
                if (s_fw)
                    pend[s_df] <= 1'b1;                         // a new pending result wins
                if (s_op == `TRW_OP_CALL) begin
                    rb       <= 1'b1;
                    call_idx <= s_imm[4:0];
                end
            end else if (rt_take) begin
                a_lat <= rir;
                if (rt_is_out)
                    resv[rir[11]] <= 1'b1;
            end
        end
    end

    wire _unused = &{1'b0, rt_arg[7:4], ss[`TRW_SLOT_V_LSB], ss[`TRW_SLOT_U_LSB],
                     ss[`TRW_SLOT_SE_LSB], ss[`TRW_SLOT_SV_MSB:`TRW_SLOT_SV_LSB],
                     ss[`TRW_SLOT_FV_MSB:`TRW_SLOT_FM_LSB], ss[`TRW_SLOT_TE_LSB],
                     ss[`TRW_SLOT_TAG_MSB:`TRW_SLOT_TAG_LSB], ss[`TRW_SLOT_HE_LSB],
                     ss[`TRW_SLOT_HV_LSB], ss[`TRW_SLOT_HS_LSB]};
endmodule
