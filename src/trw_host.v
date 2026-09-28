// Host controller (ARCHITECTURE.md §9, DECISIONS D-046 with D-042 and D-044): the SPI slave (trw_spi) and
// the register map generated into trw_defs.vh (`TRW_HA_*`, `TRW_HL_*`, `TRW_IRQ_*`). It owns RUN, STEP,
// the pin units' `live` bit (D-041 B: set by the first RUN or STEP), the IRQ enable and the host's SRAM rotation slot; every other
// register belongs to its block, which this module writes through strobes and reads through the buses
// below.
//
// Timing contract:
//   - Write strobes (`*_we`, `clr_*`, `hin_load_req`, `step`) are one-clock pulses in the clock after the
//     SPI word completes; address and data outputs are valid with them. `run` changes at that edge.
//   - Slot writes to a running lane are dropped (§9: written while halted); lane register writes carry
//     the same rule inside trw_lane (E2). STEP reaches only halted lanes.
//   - Reads: the read multiplexer is combinational from `rd_addr` (held by trw_spi) and the blocks'
//     state; trw_spi samples it at `rd_ack`. A read of `host_out` takes the HOST_OUT token only when that
//     word has been shifted out completely (`rd_done`), not when it is prefetched (BUGS #47); after a
//     host_status word in the same burst, only if that status showed a token (BUGS #48).
//   - SRAM: a host access waits for the host rotation slot (`host_slot`, time mod 4 = 3, §14 R1); read
//     data is captured the clock after (the macro's registered output), well inside trw_spi's 60 clocks.
//   - `irq` is registered: OR of (status & enable), status live (D-046).
// Lane debug bus, per lane (LDW bits, packed by the top from trw_lane's outputs and the lane's ports):
//   [63:0] r3..r0, [67:64] STATE, [71:68] FLAGS {RB, f2..f0}, [74:72] PEND, [83:75] RPC, [84] RIR valid,
//   [100:85] RIR, [101] RZ, [103:102] O valid {O1, O0}, [105:104] O seq, [141:106] O tokens {O1, O0},
//   [143:142] I avail {I1, I0}, [179:144] I heads {I1, I0}.
`default_nettype none
`include "trw_defs.vh"

module trw_host #(
    parameter NL = 3,                       // lanes
    parameter NU = 6,                       // pin units
    parameter NC = 13,                      // fabric consumer ports
    parameter LDW = 180                     // lane debug bus width, per lane
) (
    input  wire              clk,
    input  wire              rst_n,
    // SPI pins (synchronised) and IRQ
    input  wire              csn,
    input  wire              sck,
    input  wire              mosi,
    output wire              miso,
    output reg               irq,
    // control
    output reg  [NL-1:0]     run,
    output reg  [NL-1:0]     step,
    output reg               live,
    input  wire [15:0]       time_now,
    // lanes: slot store writes, register writes, debug
    output wire [NL-1:0]     slot_we,
    output wire [5:0]        slot_waddr,
    output wire [NL-1:0]     lane_hwe,
    output wire [2:0]        lane_hsel,
    output wire [15:0]       wdata,           // write data for every strobe below
    input  wire [NL*LDW-1:0] lane_dbg,
    // fabric ports
    output wire [NC-1:0]     port_we,          // fields from wdata: [0] en, [1] tap, [5:2] sel, [9:6] accept
    output wire [NC-1:0]     clr_dropped,
    input  wire [10*NC-1:0]  port_state,
    input  wire [8*NC-1:0]   dropped,
    // pin units: configuration blocks, flags, owners
    output wire [NU-1:0]     pcfg_we,
    output wire [4:0]        pcfg_waddr,
    output wire [NU-1:0]     clr_overrun,
    output wire [NU-1:0]     clr_late,
    input  wire [NU-1:0]     overrun,
    input  wire [NU-1:0]     late,
    output wire              own_we,
    output wire [3:0]        own_waddr,
    output wire [3:0]        own_raddr,
    input  wire [2:0]        own_q,
    // HOST_IN producer (trw_chan_prod) and HOST_OUT consumer port
    output wire              hin_load_req,
    output wire [17:0]       hin_tok,
    input  wire              hin_free,
    input  wire              hout_avail,
    input  wire [17:0]       hout_head,
    output wire              hout_take,
    // SRAM, host rotation slot
    input  wire              host_slot,
    output wire              mem_en,
    output wire              mem_we,
    output wire [8:0]        mem_addr,
    output wire [15:0]       mem_wdata,
    input  wire [15:0]       mem_rdata
);
    // ---------------------------------------------------------------- SPI
    wire        wr, rd_req, rd_ack, rd_done;
    wire [15:0] wa, wd, ra;
    reg  [15:0] rd_data;
    trw_spi u_spi (
        .clk (clk), .rst_n (rst_n), .csn (csn), .sck (sck), .mosi (mosi), .miso (miso),
        .wr (wr), .wr_addr (wa), .wr_data (wd), .rd_req (rd_req), .rd_addr (ra), .rd_data (rd_data),
        .rd_ack (rd_ack), .rd_done (rd_done)
    );
    assign wdata = wd;

    // ---------------------------------------------------------------- write decode
    wire [15:0] o_uf  = wa - `TRW_HA_UNIT_FLAGS;
    wire [15:0] o_sl  = wa - `TRW_HA_SLOTS;
    wire [15:0] o_pt  = wa - `TRW_HA_PORTS;
    wire [15:0] o_dr  = wa - `TRW_HA_DROPPED;
    wire [15:0] o_pc  = wa - `TRW_HA_PIN_CFG;
    wire [15:0] o_ow  = wa - `TRW_HA_OWNERS;
    wire [15:0] o_ln  = wa - `TRW_HA_LANES;
    wire [15:0] o_hi  = wa - `TRW_HA_HOST_IN;
    wire [15:0] o_sr  = wa - `TRW_HA_SRAM;

    wire w_run  = wr && (wa == `TRW_HA_RUN);
    wire w_step = wr && (wa == `TRW_HA_STEP);
    wire w_irqe = wr && (wa == `TRW_HA_IRQ_EN);
    wire w_uf   = wr && (o_uf < NU);
    wire w_sl   = wr && (o_sl < `TRW_HA_SLOTS_N) && (o_sl[3:2] == 2'd0);
    wire w_pt   = wr && (o_pt < NC);
    wire w_dr   = wr && (o_dr < NC);
    wire w_pc   = wr && (o_pc < `TRW_HA_PIN_CFG_N) && (o_pc[7:5] < NU);
    wire w_ow   = wr && (o_ow < `TRW_HA_OWNERS_N);
    wire w_ln   = wr && (o_ln < NL * `TRW_HA_LANE_STRIDE) && (o_ln[4:0] <= `TRW_HL_STATE);
    wire w_hi   = wr && (o_hi < `TRW_HA_HOST_IN_N);
    wire w_sr   = wr && (o_sr < `TRW_HA_SRAM_N);

    genvar g;
    generate
        for (g = 0; g < NL; g = g + 1) begin : g_lw
            assign slot_we[g]  = w_sl && (o_sl[9:8] == g) && !run[g];
            assign lane_hwe[g] = w_ln && (o_ln[6:5] == g);
        end
        for (g = 0; g < NC; g = g + 1) begin : g_cw
            assign port_we[g]     = w_pt && (o_pt[3:0] == g);
            assign clr_dropped[g] = w_dr && (o_dr[3:0] == g);
        end
        for (g = 0; g < NU; g = g + 1) begin : g_uw
            assign pcfg_we[g]     = w_pc && (o_pc[7:5] == g);
            assign clr_overrun[g] = w_uf && (o_uf[2:0] == g) && wd[0];
            assign clr_late[g]    = w_uf && (o_uf[2:0] == g) && wd[1];
        end
    endgenerate
    assign slot_waddr   = {o_sl[7:4], o_sl[1:0]};
    assign lane_hsel    = o_ln[2:0];
    assign pcfg_waddr   = o_pc[4:0];
    assign own_we       = w_ow;
    assign own_waddr    = o_ow[3:0];
    assign hin_load_req = w_hi;
    assign hin_tok      = {o_hi[1:0], wd};

    // ---------------------------------------------------------------- control registers, IRQ
    reg  [10:0] irq_en;
    wire        any_drop = |dropped;
    wire [10:0] irq_st;
    generate                                   // [5:0]: unit u's OVERRUN or LATE (0 for units the chip lacks)
        for (g = 0; g < 6; g = g + 1) begin : g_irq
            if (g < NU) begin : g_u
                assign irq_st[g] = overrun[g] | late[g];
            end else begin : g_n
                assign irq_st[g] = 1'b0;
            end
        end
    endgenerate
    assign irq_st[7:6] = 2'd0;
    assign irq_st[8]   = hout_avail;
    assign irq_st[9]   = hin_free;
    assign irq_st[10]  = any_drop;
    always @(posedge clk) begin
        if (!rst_n) begin
            run    <= {NL{1'b0}};
            step   <= {NL{1'b0}};
            live   <= 1'b0;
            irq_en <= 11'd0;
            irq    <= 1'b0;
        end else begin
            step <= w_step ? (wd[NL-1:0] & ~run) : {NL{1'b0}};
            if (w_run) begin
                run  <= wd[NL-1:0];
                live <= live || (wd[NL-1:0] != {NL{1'b0}});
            end
            if (w_step && ((wd[NL-1:0] & ~run) != {NL{1'b0}}))
                live <= 1'b1;                           // D-041 B: the first RUN or STEP (BUGS #49)
            if (w_irqe)
                irq_en <= wd[10:0];
            irq <= |(irq_st & irq_en);
        end
    end

    // ---------------------------------------------------------------- SRAM (host rotation slot)
    wire [15:0] r_sr = ra - `TRW_HA_SRAM;
    wire        h_rd = rd_req && (r_sr < `TRW_HA_SRAM_N);
    reg         hp_v, hp_we, h_await;
    reg  [8:0]  hp_addr;
    reg  [15:0] hp_wd, h_rq;
    assign mem_en    = host_slot && hp_v;
    assign mem_we    = hp_we;
    assign mem_addr  = hp_addr;
    assign mem_wdata = hp_wd;
    always @(posedge clk) begin
        if (!rst_n) begin
            hp_v <= 1'b0;  hp_we <= 1'b0;  hp_addr <= 9'd0;  hp_wd <= 16'd0;  h_await <= 1'b0;  h_rq <= 16'd0;
        end else begin
            h_await <= mem_en && !hp_we;
            if (h_await)
                h_rq <= mem_rdata;
            if (w_sr || h_rd) begin
                hp_v    <= 1'b1;
                hp_we   <= w_sr;
                hp_addr <= w_sr ? o_sr[8:0] : r_sr[8:0];
                hp_wd   <= wd;
            end else if (mem_en) begin
                hp_v <= 1'b0;
            end
        end
    end

    // ---------------------------------------------------------------- read multiplexer
    wire [15:0] r_uf = ra - `TRW_HA_UNIT_FLAGS;
    wire [15:0] r_pt = ra - `TRW_HA_PORTS;
    wire [15:0] r_dr = ra - `TRW_HA_DROPPED;
    wire [15:0] r_ow = ra - `TRW_HA_OWNERS;
    wire [15:0] r_ln = ra - `TRW_HA_LANES;
    assign own_raddr = r_ow[3:0];
    // The word being shifted out was loaded from host_out while a token was there: take it when done.
    // Read right after host_status in the same burst, it is taken only if that status showed the token
    // (a token arriving between the two loads would otherwise be taken but ignored, BUGS #48).
    reg out_pend, st_seen, st_av;
    always @(posedge clk) begin
        if (!rst_n || csn) begin
            out_pend <= 1'b0;
            st_seen  <= 1'b0;
            st_av    <= 1'b0;
        end else if (rd_ack) begin
            out_pend <= (ra == `TRW_HA_HOST_OUT) && hout_avail && (!st_seen || st_av);
            st_seen  <= (ra == `TRW_HA_HOST_STATUS);
            st_av    <= hout_avail;
        end
    end
    assign hout_take = rd_done && out_pend;

    // the addressed lane's debug fields
    wire [1:0]     lk  = r_ln[6:5];
    wire [LDW-1:0] ld  = lane_dbg[LDW*lk +: LDW];
    reg  [15:0]    lane_word;
    always @* begin
        case (r_ln[4:0])
            `TRW_HL_R0, `TRW_HL_R1, `TRW_HL_R2, `TRW_HL_R3:
                                  lane_word = ld[16*r_ln[1:0] +: 16];
            `TRW_HL_STATE:        lane_word = {12'd0, ld[67:64]};
            `TRW_HL_FLAGS:        lane_word = {9'd0, ld[74:72], ld[71:68]};
            `TRW_HL_RPC:          lane_word = {7'd0, ld[83:75]};
            `TRW_HL_RIR_STATUS:   lane_word = {ld[84], ld[101], 14'd0};
            `TRW_HL_RIR:          lane_word = ld[100:85];
            `TRW_HL_CHANNELS:     lane_word = {10'd0, ld[103], ld[105], ld[102], ld[104], ld[143:142]};
            `TRW_HL_I0_TAG:       lane_word = {14'd0, ld[161:160]};
            `TRW_HL_I0_DATA:      lane_word = ld[159:144];
            `TRW_HL_I1_TAG:       lane_word = {14'd0, ld[179:178]};
            `TRW_HL_I1_DATA:      lane_word = ld[177:162];
            `TRW_HL_O0_TAG:       lane_word = {14'd0, ld[123:122]};
            `TRW_HL_O0_DATA:      lane_word = ld[121:106];
            `TRW_HL_O1_TAG:       lane_word = {14'd0, ld[141:140]};
            `TRW_HL_O1_DATA:      lane_word = ld[139:124];
            default:              lane_word = 16'd0;
        endcase
    end

    reg     uf_late, uf_ovr;                   // unit_flags word r_uf (any unit count)
    integer ku;
    always @* begin
        uf_late = 1'b0;
        uf_ovr  = 1'b0;
        for (ku = 0; ku < NU; ku = ku + 1)
            if (r_uf[2:0] == ku[2:0]) begin
                uf_late = late[ku];
                uf_ovr  = overrun[ku];
            end
    end
    always @* begin
        rd_data = 16'd0;
        if (ra == `TRW_HA_RUN)                      rd_data = {live, {(15-NL){1'b0}}, run};
        else if (ra == `TRW_HA_TIME)                rd_data = time_now;
        else if (ra == `TRW_HA_IRQ_EN)              rd_data = {5'd0, irq_en};
        else if (ra == `TRW_HA_IRQ_STATUS)          rd_data = {5'd0, irq_st};
        else if (r_uf < NU)                         rd_data = {14'd0, uf_late, uf_ovr};
        else if (ra == `TRW_HA_VERSION)             rd_data = `TRW_SPEC_VERSION;
        else if (ra == `TRW_HA_ID)                  rd_data = `TRW_HOST_ID;
        else if (r_pt < NC)                         rd_data = {6'd0, port_state[10*r_pt[3:0] +: 10]};
        else if (r_dr < NC)                         rd_data = {8'd0, dropped[8*r_dr[3:0] +: 8]};
        else if (r_ow < `TRW_HA_OWNERS_N)           rd_data = {13'd0, own_q};
        else if (r_ln < NL * `TRW_HA_LANE_STRIDE)   rd_data = lane_word;
        else if (ra == `TRW_HA_HOST_STATUS)         rd_data = {hout_avail, hin_free, 12'd0, hout_head[17:16]};
        else if (ra == `TRW_HA_HOST_OUT)            rd_data = hout_head[15:0];
        else if (r_sr < `TRW_HA_SRAM_N)             rd_data = h_rq;
    end
endmodule
