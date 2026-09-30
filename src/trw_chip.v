// TRIPWIRE, the whole chip (ARCHITECTURE.md §3), with Tiny Tapeout's pins. tt_um_tripwire.v will wrap it
// once the area budget is settled (phase 2 task 2.4); until then it is exercised by test_internal/chip.
//
// Blocks: `TRW_LANES lanes (trw_lane + trw_slots), the channel fabric (trw_fabric, generated) with the
// producer registers of the pin units and HOST_IN (trw_chan_prod), `TRW_UNITS pin units (trw_pin_cfg +
// trw_pin_unit; U0-U1 full, D-040), the pad owners (trw_pins), the host (trw_host + trw_spi), the SRAM
// (trw_sram) on the fixed rotation, the 2-FF input synchronisers (trw_sync) and the global time.
// Lane and unit counts come from spec/tripwire.yaml (`fabric`), so a different count is a spec change
// that regenerates the fabric, the host map and this chip together.
//
// Timing contract:
//   - One clock; synchronous active-low reset. Pad inputs reach every block through trw_sync (§14 P1);
//     pin units see uo pads directly (P7).
//   - Time is 0 at reset and counts every clock. The SRAM rotation slot is time mod 4: 0..2 lane k (if
//     that lane exists), 3 the host (§14 R1).
//   - Pads (§10, spec `pads.host`): ui4 CS_n, ui5 SCK, ui6 MOSI, uo3 MISO, uo6 IRQ; the other 19 pads
//     belong to the pin units through the owner registers. `ena` is not used.
// Numbering (tools/gen fabric_numbering): producers U0..U(NU-1).rx, then L0.O0, L0.O1, L1.O0, ..., then
// HOST_IN; consumers L0.I0, L0.I1, ..., then U0..U(NU-1).tx, then HOST_OUT.
`default_nettype none
`include "trw_defs.vh"

module trw_chip (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);
    localparam NL  = `TRW_LANES;
    localparam NU  = `TRW_UNITS;
    localparam NP  = `TRW_NPROD;
    localparam NC  = `TRW_NCONS;
    localparam LDW = 180;                          // lane debug bus (trw_host.v)
    localparam P_L = NU;                           // first lane producer
    localparam P_H = NU + 2 * NL;                  // HOST_IN
    localparam C_U = 2 * NL;                       // first unit consumer
    localparam C_H = 2 * NL + NU;                  // HOST_OUT

    // ---------------------------------------------------------------- pads in, time
    wire [15:0] s;
    trw_sync #(.W (16)) u_sync (.clk (clk), .d ({uio_in, ui_in}), .q (s));
    wire [7:0]  ui_s  = s[7:0];
    wire [7:0]  uio_s = s[15:8];
    wire [23:0] pads  = {uio_s, uo_out, ui_s};      // pads 0..23 (§14 P1, P7)

    reg [15:0] tnow;
    always @(posedge clk) begin
        if (!rst_n) tnow <= 16'd0;
        else        tnow <= tnow + 16'd1;
    end
    wire [1:0] slot = tnow[1:0];

    // ---------------------------------------------------------------- fabric
    wire [NP-1:0]    p_valid, p_seq, p_load, all_taken;
    wire [18*NP-1:0] p_tok;
    wire [NC-1:0]    take, avail;
    wire [18*NC-1:0] head;
    wire [NC-1:0]    port_we, clr_dropped;
    wire [10*NC-1:0] port_state;
    wire [8*NC-1:0]  dropped;
    wire [15:0]      hwd;                           // host write data
    trw_fabric u_fab (
        .clk (clk), .rst_n (rst_n),
        .p_valid (p_valid), .p_seq (p_seq), .p_load (p_load), .p_tok (p_tok), .all_taken (all_taken),
        .take (take), .avail (avail), .head (head),
        .cfg_we (port_we), .cfg_en (hwd[0]), .cfg_tap (hwd[1]), .cfg_sel (hwd[5:2]), .cfg_accept (hwd[9:6]),
        .clr_dropped (clr_dropped), .port_state (port_state), .dropped (dropped)
    );

    // ---------------------------------------------------------------- host
    wire [NL-1:0]     run, step, slot_we, lane_hwe;
    wire              live, irq, miso;
    wire [5:0]        slot_waddr;
    wire [2:0]        lane_hsel;
    wire [NL*LDW-1:0] lane_dbg;
    wire [NU-1:0]     pcfg_we, clr_overrun, clr_late, overrun, late;
    wire [4:0]        pcfg_waddr;
    wire              own_we;
    wire [3:0]        own_waddr, own_raddr;
    wire [2:0]        own_q;
    wire              hin_req;
    wire [17:0]       hin_tok;
    wire              h_en, h_we;
    wire [8:0]        h_addr;
    wire [15:0]       h_wd, s_rdata;
    trw_host #(.NL (NL), .NU (NU), .NC (NC), .LDW (LDW)) u_host (
        .clk (clk), .rst_n (rst_n), .csn (ui_s[4]), .sck (ui_s[5]), .mosi (ui_s[6]), .miso (miso), .irq (irq),
        .run (run), .step (step), .live (live), .time_now (tnow),
        .slot_we (slot_we), .slot_waddr (slot_waddr), .lane_hwe (lane_hwe), .lane_hsel (lane_hsel),
        .wdata (hwd), .lane_dbg (lane_dbg),
        .port_we (port_we), .clr_dropped (clr_dropped), .port_state (port_state), .dropped (dropped),
        .pcfg_we (pcfg_we), .pcfg_waddr (pcfg_waddr), .clr_overrun (clr_overrun), .clr_late (clr_late),
        .overrun (overrun), .late (late),
        .own_we (own_we), .own_waddr (own_waddr), .own_raddr (own_raddr), .own_q (own_q),
        .hin_load_req (hin_req), .hin_tok (hin_tok), .hin_free (hin_free),
        .hout_avail (avail[C_H]), .hout_head (head[18*C_H +: 18]), .hout_take (take[C_H]),
        .host_slot (slot == 2'd3), .mem_en (h_en), .mem_we (h_we), .mem_addr (h_addr), .mem_wdata (h_wd),
        .mem_rdata (s_rdata)
    );

    // HOST_IN producer
    wire hin_free;
    trw_chan_prod u_hin (
        .clk (clk), .rst_n (rst_n), .load_req (hin_req), .tok_in (hin_tok), .all_taken (all_taken[P_H]),
        .free (hin_free), .load (p_load[P_H]), .valid (p_valid[P_H]), .seq (p_seq[P_H]),
        .tok (p_tok[18*P_H +: 18])
    );

    // ---------------------------------------------------------------- lanes
    wire [NL-1:0]    l_en, l_we;
    wire [9*NL-1:0]  l_addr;
    wire [16*NL-1:0] l_wd;
    genvar k;
    generate
        for (k = 0; k < NL; k = k + 1) begin : g_lane
            wire [12*`TRW_SLOT_BITS-1:0] slots;
            wire [63:0] kk;
            trw_slots u_slots (
                .clk (clk), .rst_n (rst_n), .we (slot_we[k]), .waddr (slot_waddr), .wdata (hwd),
                .slots (slots), .k (kk)
            );
            wire [63:0] regs;
            wire [3:0]  state, flags;
            wire [2:0]  pend;
            wire [8:0]  rpc;
            wire        rir_v, rz;
            wire [15:0] rir;
            wire [1:0]  ov, os;
            wire [35:0] ot;
            trw_lane u_lane (
                .clk (clk), .rst_n (rst_n), .run (run[k]), .step (step[k]), .slots (slots), .k (kk),
                .time_now (tnow),
                .in_avail (avail[2*k +: 2]), .in_head (head[36*k +: 36]), .in_take (take[2*k +: 2]),
                .out_all_taken (all_taken[P_L+2*k +: 2]), .out_valid (ov), .out_seq (os), .out_tok (ot),
                .out_load (p_load[P_L+2*k +: 2]),
                .my_slot (slot == k), .mem_rdata (s_rdata), .mem_en (l_en[k]), .mem_we (l_we[k]),
                .mem_addr (l_addr[9*k +: 9]), .mem_wdata (l_wd[16*k +: 16]),
                .host_we (lane_hwe[k]), .host_sel (lane_hsel), .host_wdata (hwd),
                .dbg_regs (regs), .dbg_state (state), .dbg_flags (flags), .dbg_pend (pend), .dbg_rpc (rpc),
                .dbg_rir_valid (rir_v), .dbg_rir (rir), .dbg_rz (rz)
            );
            assign p_valid[P_L+2*k +: 2]       = ov;
            assign p_seq[P_L+2*k +: 2]         = os;
            assign p_tok[18*(P_L+2*k) +: 36]   = ot;
            assign lane_dbg[LDW*k +: LDW] = {head[36*k +: 36], avail[2*k +: 2], ot, os, ov, rz, rir, rir_v,
                                             rpc, pend, flags, state, regs};
        end
    endgenerate

    // ---------------------------------------------------------------- SRAM on the rotation (§14 R1)
    reg        s_en, s_we;
    reg [8:0]  s_addr;
    reg [15:0] s_wd;
    integer j;
    always @* begin
        s_en = h_en;  s_we = h_we;  s_addr = h_addr;  s_wd = h_wd;          // slot 3 (the host)
        for (j = 0; j < NL; j = j + 1)
            if ({30'd0, slot} == j) begin
                s_en = l_en[j];  s_we = l_we[j];  s_addr = l_addr[9*j +: 9];  s_wd = l_wd[16*j +: 16];
            end
    end
    trw_sram u_sram (
        .clk (clk), .rst_n (rst_n), .en (s_en), .we (s_we), .addr (s_addr), .wdata (s_wd), .rdata (s_rdata)
    );

    // ---------------------------------------------------------------- pin units
    wire [NU-1:0]   a_out, a_oe, n_out, n_oe;
    wire [5*NU-1:0] pin_a, pin_n;
    genvar u;
    generate
        for (u = 0; u < NU; u = u + 1) begin : g_unit
            localparam FULL = (`TRW_PC_UNITS_PULSE >> u) & 1;               // D-040: U0-U1 full
            wire [`TRW_PC_BITS-1:0] cfg;
            wire        carrier_active;
            wire        restart, rx_load, rx_free;
            wire [1:0]  rx_tag;
            wire [15:0] rx_data;
            trw_pin_cfg #(.FULL (FULL)) u_cfg (
                .clk (clk), .rst_n (rst_n), .we (pcfg_we[u]), .waddr (pcfg_waddr), .wdata (hwd),
                .cfg (cfg), .carrier_active (carrier_active), .restart (restart)
            );
            trw_pin_unit #(.FULL (FULL)) u_unit (
                .clk (clk), .rst_n (rst_n), .restart (restart), .live (live), .cfg (cfg),
                .carrier_active (carrier_active), .pads (pads),
                .tx_avail (avail[C_U+u]), .tx_tag (head[18*(C_U+u)+16 +: 2]), .tx_data (head[18*(C_U+u) +: 16]),
                .tx_take (take[C_U+u]),
                .rx_free (rx_free), .rx_load (rx_load), .rx_tag (rx_tag), .rx_data (rx_data),
                .a_out (a_out[u]), .a_oe (a_oe[u]), .n_out (n_out[u]), .n_oe (n_oe[u]),
                .late (late[u]), .overrun (overrun[u]), .clr_late (clr_late[u]), .clr_overrun (clr_overrun[u])
            );
            trw_chan_prod u_prod (
                .clk (clk), .rst_n (rst_n), .load_req (rx_load), .tok_in ({rx_tag, rx_data}),
                .all_taken (all_taken[u]), .free (rx_free), .load (p_load[u]), .valid (p_valid[u]),
                .seq (p_seq[u]), .tok (p_tok[18*u +: 18])
            );
            assign pin_a[5*u +: 5] = cfg[`TRW_PC_PIN_A_MSB:`TRW_PC_PIN_A_LSB];
            assign pin_n[5*u +: 5] = cfg[`TRW_PC_PIN_N_MSB:`TRW_PC_PIN_N_LSB];
        end
    endgenerate

    // ---------------------------------------------------------------- pads out (§7.1, §10)
    wire [15:0] pad_out, pad_oe;
    trw_pins #(.NU (NU)) u_pins (
        .clk (clk), .rst_n (rst_n), .own_we (own_we), .own_waddr (own_waddr), .own_wdata (hwd[2:0]),
        .own_raddr (own_raddr), .own_q (own_q),
        .a_out (a_out), .a_oe (a_oe), .n_out (n_out), .n_oe (n_oe), .pin_a (pin_a), .pin_n (pin_n),
        .pad_out (pad_out), .pad_oe (pad_oe)
    );
    assign uo_out  = {pad_out[7], irq, pad_out[5:4], miso, pad_out[2:0]};
    assign uio_out = pad_out[15:8];
    assign uio_oe  = pad_oe[15:8];

    wire _unused = &{1'b0, ena, pad_oe[7:0], pad_out[6], pad_out[3]};
endmodule
