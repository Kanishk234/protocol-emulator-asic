// One lane (ARCHITECTURE.md §5, §6, §14 L1-L12, R1-R6, H1-H2; ISA.md §2-§5): 12 reflex slots, the
// EVAL -> EXEC pipeline with the shared ALU, r0-r3, STATE, f0-f2, RB (f3), PEND, the output producer
// registers O0/O1, and the routine controller (RPC, RIR, CALL, BR, DJNZ, LD/ST, OUT, SYS) on the SRAM
// rotation. Reflex path from the R1 spike (spikes/r1_lane, D-030), with D-035's rules added.
//
// Timing contract (clock n = the cycle edge n ends, §14 conventions):
//   - EVAL in clock n: the 12 ready() terms (ISA §4.2) and a waiting routine step compete (§4.3, L2);
//     static updates at edge n (L4, L6): STATE := NS, the input take, output reservation, PEND[DF] := 1,
//     CALL sets RB and requests the entry-table read. The input head and time are latched (L3).
//   - EXEC in clock n+1: registers and K are read, the ALU runs, writes land at edge n+1 (L5, L11).
//   - EVAL runs while `run`, or for exactly one clock on `step` while halted (H2). An action selected
//     before RUN drops still executes.
//   - SRAM (R1-R3): `my_slot` is this lane's rotation clock. The lane drives mem_* combinationally in
//     that clock; `mem_rdata` is the macro's registered output, valid in the clock after a read. A word
//     read on slot k is usable in clock k+1: a fetched step or an LD result competes at EVAL in k+1.
//     Fetches and data accesses happen only while `run` (or in a STEP clock).
//   - Outputs: `out_load` is the producer load at this edge (for tap drop counting, F4). `in_take` is
//     combinational from EVAL.
//   - Host (E2): r0-r3 and STATE are written only while halted (`host_we` is ignored while running).
`default_nettype none
`include "trw_defs.vh"

module trw_lane #(
    parameter AW = 9                                   // SRAM address bits (512 words)
) (
    input  wire                         clk,
    input  wire                         rst_n,
    input  wire                         run,
    input  wire                         step,          // one EVAL while halted (H2); ignored while running
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
    output wire [1:0]                   out_load,
    // SRAM rotation slot
    input  wire                         my_slot,
    input  wire [15:0]                  mem_rdata,
    output wire                         mem_en,
    output wire                         mem_we,
    output wire [AW-1:0]                mem_addr,
    output wire [15:0]                  mem_wdata,
    // host (E2): sel 0-3 = r0-r3, 4 = STATE
    input  wire                         host_we,
    input  wire [2:0]                   host_sel,
    input  wire [15:0]                  host_wdata,
    // debug readback (§9 lane register block)
    output wire [63:0]                  dbg_regs,      // {r3, r2, r1, r0}
    output wire [3:0]                   dbg_state,
    output wire [3:0]                   dbg_flags,     // {RB, f2, f1, f0}
    output wire [2:0]                   dbg_pend,
    output wire [AW-1:0]                dbg_rpc,
    output wire                         dbg_rir_valid,
    output wire [15:0]                  dbg_rir,
    output wire                         dbg_rz
);
    localparam SB = `TRW_SLOT_BITS;

    // ---------------------------------------------------------------- lane state
    reg [63:0] regs;        // {r3, r2, r1, r0}
    reg [3:0]  state;
    reg [2:0]  f;           // f2..f0
    reg        rb;          // f3: routine busy
    reg [2:0]  pend;        // PEND for f2..f0
    reg [1:0]  resv;        // output reservations
    reg        rz;

    // routine controller
    reg [AW-1:0] rpc;
    reg          rir_v;     // RIR holds a step: an instruction, or an LD result (rir_ld)
    reg          rir_ld;
    reg [15:0]   rir;
    reg          acc_v;     // a data access is pending (R3)
    reg [1:0]    acc_kind;  // 0 entry-table read, 1 LD, 2 ST
    reg [AW-1:0] acc_addr;
    reg [15:0]   acc_wd;
    reg [1:0]    ld_rd;     // LD destination, from the LD step to its result step
    reg [1:0]    ret;       // what mem_rdata holds this clock: 0 nothing, 1 fetch, 2 entry, 3 LD data

    // EXEC stage, loaded at EVAL
    reg        ex_slot, ex_rt, ex_ld;
    reg [3:0]  ex_op;
    reg [2:0]  ex_dst, ex_asrc;
    reg [1:0]  ex_bsel, ex_df, ex_ot;
    reg [7:0]  ex_imm;
    reg        ex_dfe, ex_kt;
    reg [15:0] a_lat;       // slot: A input head data or time; routine step: the word (or LD data)
    reg [1:0]  a_tag;
    reg [15:0] t_lat;       // routine step: the time at its EVAL (GETT, R3)

    wire [3:0] flags = {rb, f};
    wire       eval_en = run || step;

    assign dbg_regs = regs;       assign dbg_state = state;   assign dbg_flags = flags;
    assign dbg_pend = pend;       assign dbg_rpc   = rpc;     assign dbg_rir_valid = rir_v;
    assign dbg_rir  = rir;        assign dbg_rz    = rz;

    // ---------------------------------------------------------------- EVAL: reflex slots
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

            wire       a_in    = (asrc == `TRW_ASRC_I0) || (asrc == `TRW_ASRC_I1);
            wire       hsel    = asrc[0];
            wire       h_av    = hsel ? in_avail[1] : in_avail[0];
            wire [1:0] h_tag   = hsel ? in_head[35:34] : in_head[17:16];
            wire       h_bit   = hs ? (hsel ? in_head[18] : in_head[0])      // data[0]
                                    : (hsel ? in_head[33] : in_head[15]);    // data[15]
            // O0 or O1; CALL ignores DST, so it never waits for an output (L10). DST 6/7: none (L12).
            wire       d_out   = ((dst == `TRW_DST_O0) || (dst == `TRW_DST_O1)) && (op != `TRW_OP_CALL);

            wire explicit_ok = v
                            && (!se || (state == sv))
                            && (((flags ^ fv) & fm) == 4'd0)
                            && (({1'b0, pend} & fm) == 4'd0);                // pending rule
            wire in_ok   = !a_in || (h_av && (!te || (h_tag == tag)) && (!he || (h_bit == hv)));
            wire out_ok  = !d_out || ofree[dst[0]];
            wire call_ok = (op != `TRW_OP_CALL) || !rb;

            assign ready[i]  = eval_en && explicit_ok && in_ok && out_ok && call_ok;
            assign urgent[i] = s[`TRW_SLOT_U_LSB];
        end
    endgenerate

    // ---------------------------------------------------------------- EVAL: the waiting routine step
    // A word read on the previous rotation slot is usable now (R1): it competes this clock and goes into
    // RIR at the edge if it is not selected.
    wire        st_v   = rir_v || (ret == 2'd1) || (ret == 2'd3);
    wire        st_ld  = rir_v ? rir_ld : (ret == 2'd3);
    wire [15:0] st_w   = rir_v ? rir : mem_rdata;
    wire        st_ctl = st_w[15];
    wire [2:0]  st_sub = st_w[`TRW_RT_SUB_MSB:`TRW_RT_SUB_LSB];
    wire        st_out = !st_ld && st_ctl && (st_sub == `TRW_RT_SUB_OUT);
    wire        st_prt = st_w[`TRW_RT_OUT_PORT_LSB];
    // R5: a waiting OUT whose output is not free is not a candidate.
    wire        rt_ok  = eval_en && st_v && (!st_out || ofree[st_prt]);

    // §4.3: with a step waiting only urgent slots can beat it; one lowest-index encoder either way.
    wire [11:0] cand   = ready & (rt_ok ? urgent : 12'hFFF);
    wire [11:0] onehot = cand & (~cand + 12'd1);
    wire        fire   = |cand;
    wire        rt_take = rt_ok && !fire;

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

    wire s_a_in    = (s_asrc == `TRW_ASRC_I0) || (s_asrc == `TRW_ASRC_I1);
    // L10: CALL ignores DST (no reservation, no output load) and DFE (no PEND, no flag write).
    wire s_is_call = (s_op == `TRW_OP_CALL);
    wire s_d_out   = ((s_dst == `TRW_DST_O0) || (s_dst == `TRW_DST_O1)) && !s_is_call;
    wire s_fw      = s_dfe && (s_df != 2'd3) && !s_is_call;
    assign in_take[0] = fire && s_dq && s_a_in && !s_asrc[0];
    assign in_take[1] = fire && s_dq && s_a_in &&  s_asrc[0];

    wire [15:0] head_data = s_asrc[0] ? in_head[33:18] : in_head[15:0];
    wire [1:0]  head_tag  = s_asrc[0] ? in_head[35:34] : in_head[17:16];

    // ---------------------------------------------------------------- EXEC
    // Routine word fields (ISA.md §5.1); the word is in a_lat while ex_rt (and not ex_ld).
    wire       rt_ctl  = a_lat[15];
    wire [2:0] rt_sub  = a_lat[`TRW_RT_SUB_MSB:`TRW_RT_SUB_LSB];
    wire [3:0] rt_aop  = a_lat[`TRW_RT_ALU_OP_MSB:`TRW_RT_ALU_OP_LSB];
    wire [1:0] rt_ard  = a_lat[`TRW_RT_ALU_RD_MSB:`TRW_RT_ALU_RD_LSB];
    wire [1:0] rt_ara  = a_lat[`TRW_RT_ALU_RA_MSB:`TRW_RT_ALU_RA_LSB];
    wire       rt_bs   = a_lat[`TRW_RT_ALU_BS_LSB];
    wire [5:0] rt_b    = a_lat[`TRW_RT_ALU_B_MSB:`TRW_RT_ALU_B_LSB];
    wire [1:0] rt_crd  = a_lat[11:10];                  // rd of LDI, LDIH, DJNZ, LD, ST (same field)
    wire [9:0] rt_imm  = a_lat[`TRW_RT_LDI_IMM_MSB:`TRW_RT_LDI_IMM_LSB];
    wire [2:0] rt_cond = a_lat[`TRW_RT_BR_COND_MSB:`TRW_RT_BR_COND_LSB];
    wire [8:0] rt_boff = a_lat[`TRW_RT_BR_OFF_MSB:`TRW_RT_BR_OFF_LSB];
    wire [9:0] rt_joff = a_lat[`TRW_RT_DJNZ_OFF_MSB:`TRW_RT_DJNZ_OFF_LSB];
    wire [1:0] rt_mra  = a_lat[`TRW_RT_LD_RA_MSB:`TRW_RT_LD_RA_LSB];
    wire [7:0] rt_moff = a_lat[`TRW_RT_LD_OFF_MSB:`TRW_RT_LD_OFF_LSB];
    wire       rt_port = a_lat[`TRW_RT_OUT_PORT_LSB];
    wire [1:0] rt_otag = a_lat[`TRW_RT_OUT_TAG_MSB:`TRW_RT_OUT_TAG_LSB];
    wire [1:0] rt_ora  = a_lat[`TRW_RT_OUT_RA_MSB:`TRW_RT_OUT_RA_LSB];
    wire [3:0] rt_fn   = a_lat[`TRW_RT_SYS_FN_MSB:`TRW_RT_SYS_FN_LSB];
    wire [7:0] rt_arg  = a_lat[`TRW_RT_SYS_ARG_MSB:`TRW_RT_SYS_ARG_LSB];
    wire [1:0] rt_fi   = rt_arg[1:0];

    wire rt_word = ex_rt && !ex_ld;
    wire rt_alu  = rt_word && !rt_ctl && (rt_aop != `TRW_OP_CALL);     // L12: op 14 is a NOP here
    wire rt_ldi  = rt_word &&  rt_ctl && (rt_sub == `TRW_RT_SUB_LDI);
    wire rt_ldih = rt_word &&  rt_ctl && (rt_sub == `TRW_RT_SUB_LDIH);
    wire rt_br   = rt_word &&  rt_ctl && (rt_sub == `TRW_RT_SUB_BR);
    wire rt_djnz = rt_word &&  rt_ctl && (rt_sub == `TRW_RT_SUB_DJNZ);
    wire rt_ldw  = rt_word &&  rt_ctl && (rt_sub == `TRW_RT_SUB_LD);
    wire rt_stw  = rt_word &&  rt_ctl && (rt_sub == `TRW_RT_SUB_ST);
    wire rt_out  = rt_word &&  rt_ctl && (rt_sub == `TRW_RT_SUB_OUT);
    wire rt_sys  = rt_word &&  rt_ctl && (rt_sub == `TRW_RT_SUB_SYS);

    reg  [3:0]  alu_op;
    reg  [15:0] alu_a, alu_b;
    reg  [7:0]  alu_f;
    always @* begin
        if (ex_rt) begin
            if (rt_ctl) begin                   // DJNZ: rd - 1 (other control words do not use the ALU)
                alu_op = `TRW_OP_SUB;
                alu_a  = regs[16*rt_crd +: 16];
                alu_b  = 16'd1;
                alu_f  = 8'd0;
            end else begin
                alu_op = rt_aop;
                alu_a  = regs[16*rt_ara +: 16];
                alu_b  = rt_bs ? {10'd0, rt_b} : regs[16*rt_b[1:0] +: 16];
                alu_f  = rt_bs ? {2'd0, rt_b}  : regs[16*rt_b[1:0] +: 8];
            end
        end else begin
            alu_op = ex_op;
            alu_a  = !ex_asrc[2] ? regs[16*ex_asrc[1:0] +: 16]
                   : (ex_asrc == `TRW_ASRC_ZERO) ? 16'd0 : a_lat;
            // L8: B = r[IMM[1:0]], K[IMM[1:0]] or IMM; L12: BSEL 3 means IMM.
            case (ex_bsel)
                `TRW_BSEL_REG: alu_b = regs[16*ex_imm[1:0] +: 16];
                `TRW_BSEL_K:   alu_b = k[16*ex_imm[1:0] +: 16];
                default:       alu_b = {8'd0, ex_imm};
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

    wire       ex_d_reg  = ex_slot && !ex_dst[2] && (ex_op != `TRW_OP_CALL);
    wire       ex_d_out  = ex_slot && ((ex_dst == `TRW_DST_O0) || (ex_dst == `TRW_DST_O1))
                                   && (ex_op != `TRW_OP_CALL);
    // L8: MKCTL always emits CTRL; KT keeps the latched head tag only when ASRC is I0 or I1.
    wire       ex_a_in   = (ex_asrc == `TRW_ASRC_I0) || (ex_asrc == `TRW_ASRC_I1);
    wire [1:0] ex_out_tag = (ex_op == `TRW_OP_MKCTL) ? `TRW_TAG_CTRL
                          : (ex_kt && ex_a_in)       ? a_tag
                          :                            ex_ot;
    wire       ex_fw     = ex_slot && ex_dfe && (ex_df != 2'd3) && (ex_op != `TRW_OP_CALL);

    // Branches (R6, ISA §5.1): offsets are signed, relative to the next word (RPC was advanced at the
    // fetch). L12: BR conditions 3-7 are never taken.
    wire br_go   = rt_br && ((rt_cond == `TRW_BR_ALWAYS) || ((rt_cond == `TRW_BR_RZ) && rz)
                                                         || ((rt_cond == `TRW_BR_NRZ) && !rz));
    wire dj_go   = rt_djnz && !alu_r;
    wire [AW-1:0] br_off = {{(AW-9){rt_boff[8]}}, rt_boff};
    wire [AW-1:0] dj_off = rt_joff[AW-1:0];              // 10-bit signed, taken modulo 2^AW
    wire [AW-1:0] m_addr = regs[16*rt_mra +: AW] + {{(AW-8){1'b0}}, rt_moff};   // R3, modulo the size

    assign out_load[0] = (ex_d_out && (ex_dst[0] == 1'b0)) || (rt_out && !rt_port);
    assign out_load[1] = (ex_d_out && (ex_dst[0] == 1'b1)) || (rt_out &&  rt_port);

    // ---------------------------------------------------------------- SRAM (R1-R3)
    // A step "waits to execute" while it is in EXEC; a fetch then could read a stale RPC (R2).
    wire   mem_go = my_slot && eval_en;
    wire   do_acc = mem_go && acc_v;                                   // R3: data access first
    wire   do_fet = mem_go && !acc_v && rb && !st_v && !ex_rt;         // R2
    assign mem_en    = do_acc || do_fet;
    assign mem_we    = do_acc && (acc_kind == 2'd2);
    assign mem_addr  = do_acc ? acc_addr : rpc;
    assign mem_wdata = acc_wd;

    // ---------------------------------------------------------------- registers
    always @(posedge clk) begin
        if (!rst_n) begin
            regs      <= 64'd0;
            state     <= 4'd0;
            f         <= 3'd0;
            rb        <= 1'b0;
            pend      <= 3'd0;
            resv      <= 2'd0;
            rz        <= 1'b0;
            rpc       <= {AW{1'b0}};
            rir_v     <= 1'b0;
            rir_ld    <= 1'b0;
            rir       <= 16'd0;
            acc_v     <= 1'b0;
            acc_kind  <= 2'd0;
            acc_addr  <= {AW{1'b0}};
            acc_wd    <= 16'd0;
            ld_rd     <= 2'd0;
            ret       <= 2'd0;
            ex_slot   <= 1'b0;
            ex_rt     <= 1'b0;
            ex_ld     <= 1'b0;
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
            t_lat     <= 16'd0;
            out_valid <= 2'd0;
            out_seq   <= 2'd0;
            out_tok   <= 36'd0;
        end else begin
            // ---- SRAM returns (R1): fetch -> RIR (unless taken now), entry -> RPC, LD data -> RIR
            ret <= !mem_en ? 2'd0 : do_fet ? 2'd1 : (acc_kind == 2'd0) ? 2'd2
                 : (acc_kind == 2'd1) ? 2'd3 : 2'd0;
            if (do_acc)
                acc_v <= 1'b0;
            if (do_fet)
                rpc <= rpc + {{(AW-1){1'b0}}, 1'b1};
            if (ret == 2'd2)
                rpc <= mem_rdata[AW-1:0];
            if (!rir_v && ((ret == 2'd1) || (ret == 2'd3)) && !rt_take) begin
                rir_v  <= 1'b1;
                rir_ld <= (ret == 2'd3);
                rir    <= mem_rdata;
            end else if (rt_take) begin
                rir_v  <= 1'b0;
            end

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
            if (ex_ld)                                              // R3: the LD result step
                regs[16*ld_rd +: 16] <= a_lat;
            if (rt_alu) begin
                regs[16*rt_ard +: 16] <= alu_d;
                rz <= alu_r;
            end
            if (rt_ldi)
                regs[16*rt_crd +: 16] <= {6'd0, rt_imm};
            if (rt_ldih)
                regs[16*rt_crd +: 16] <= {rt_imm[5:0], regs[16*rt_crd +: 10]};
            if (rt_djnz)
                regs[16*rt_crd +: 16] <= alu_d;                     // R6: RZ unchanged
            if (br_go)
                rpc <= rpc + br_off;
            if (dj_go)
                rpc <= rpc + dj_off;
            if (rt_ldw || rt_stw) begin                             // R3: address and data held
                acc_v    <= 1'b1;
                acc_kind <= rt_ldw ? 2'd1 : 2'd2;
                acc_addr <= m_addr;
                acc_wd   <= regs[16*rt_crd +: 16];
                ld_rd    <= rt_crd;
            end
            if (rt_out) begin
                out_valid[rt_port]        <= 1'b1;
                out_seq[rt_port]          <= ~out_seq[rt_port];
                out_tok[18*rt_port +: 18] <= {rt_otag, regs[16*rt_ora +: 16]};
                resv[rt_port]             <= 1'b0;
            end
            if (rt_sys) begin
                case (rt_fn)                                        // L12: kinds 9-15 are NOPs
                    `TRW_SYS_RET:   rb    <= 1'b0;
                    `TRW_SYS_SETST: state <= rt_arg[3:0];
                    `TRW_SYS_SETF:  if (rt_fi != 2'd3) f[rt_fi] <= 1'b1;
                    `TRW_SYS_CLRF:  if (rt_fi != 2'd3) f[rt_fi] <= 1'b0;
                    `TRW_SYS_TSTF:  rz <= flags[rt_fi];
                    `TRW_SYS_CPYF:  if (rt_fi != 2'd3) f[rt_fi] <= rz;
                    `TRW_SYS_GETT:  regs[16*rt_fi +: 16] <= t_lat;
                    `TRW_SYS_GETK:  regs[16*rt_fi +: 16] <= k[16*rt_arg[3:2] +: 16];
                    default: ;
                endcase
            end

            // ---- EVAL static updates (L4, L6)
            ex_slot <= fire;
            ex_rt   <= rt_take;
            ex_ld   <= rt_take && st_ld;
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
                    pend[s_df] <= 1'b1;                         // L9: a new pending result wins
                if (s_is_call) begin                            // L6: RB and the entry-table read
                    rb       <= 1'b1;
                    acc_v    <= 1'b1;
                    acc_kind <= 2'd0;
                    acc_addr <= {{(AW-5){1'b0}}, s_imm[4:0]};
                end
            end else if (rt_take) begin
                a_lat <= st_w;
                t_lat <= time_now;
                if (st_out)
                    resv[st_prt] <= 1'b1;                       // R5: reserved at EVAL like a slot
            end

            // ---- host writes while halted (E2)
            if (host_we && !run) begin
                if (host_sel[2])
                    state <= host_wdata[3:0];
                else
                    regs[16*host_sel[1:0] +: 16] <= host_wdata;
            end
        end
    end

    wire _unused = &{1'b0, rt_arg[7:4], ss[`TRW_SLOT_V_LSB], ss[`TRW_SLOT_U_LSB],
                     ss[`TRW_SLOT_SE_LSB], ss[`TRW_SLOT_SV_MSB:`TRW_SLOT_SV_LSB],
                     ss[`TRW_SLOT_FV_MSB:`TRW_SLOT_FM_LSB], ss[`TRW_SLOT_TE_LSB],
                     ss[`TRW_SLOT_TAG_MSB:`TRW_SLOT_TAG_LSB], ss[`TRW_SLOT_HE_LSB],
                     ss[`TRW_SLOT_HV_LSB], ss[`TRW_SLOT_HS_LSB], mem_rdata[15:AW], rt_joff[9]};
endmodule
