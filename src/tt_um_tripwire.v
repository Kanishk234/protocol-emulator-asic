// R4 spike (branch spike/r4-floorplan only; never merged, DECISIONS D-043): an area- and wiring-
// representative TRIPWIRE on 6x4, to learn at what utilisation the full chip routes.
//
// On the chip:
//   - 3 lanes: the R1 lane with its latch slot array and K (spikes/r1_lane), no slot read-back (D-039),
//     each with a routine sequencer stub (r4_seq) on the SRAM rotation;
//   - 6 lean pin units (src/trw_pin_unit.v, FULL = 0) with their configuration latch blocks
//     (src/trw_pin_cfg.v) and producer registers; output owners per pad (reset: none);
//   - the fabric: 13 producers, 13 consumer ports with the spec's legal-source multiplexers
//     (r4_fabric.v, generated from spec/tripwire.yaml) and the release terms;
//   - the IHP 512x16 SRAM macro (trw_sram, R3 recipe) with the fixed 4-way rotation (§14 R1);
//   - a host SPI stub (r4_host) that writes every slot, K, fabric port, configuration word, owner and
//     SRAM word, pushes HOST_IN and pops HOST_OUT, and reads back lane registers, producer heads, pin
//     outputs, sticky flags, drop counters and SRAM.
// Everything is controlled and observed from the pins, so synthesis keeps it all.
//
// Pins (ARCHITECTURE.md §9, §10): ui[4] CS_n, ui[5] SCK, ui[6] MOSI, uo[3] MISO, uo[6] IRQ; the other
// 19 pads belong to the pin units through the owner registers.
//
// Host address map (a stub of §9):
//   W 0x0000            RUN[2:0] (per lane); any RUN = 1 makes the pin units live (P-G16)
//   W 0x0002            clear sticky flags: [5:0] LATE of U0-U5, [13:8] OVERRUN
//   W 0x1000-0x13FF     slots and K: lane [9:8], slot [7:4] (12 = K), word [1:0]
//   W 0x2000-0x200C     consumer port c: {accept[3:0], sel[3:0], tap, en}  (c as in r4_fabric.v)
//   W 0x3000-0x30BF     pin unit u word w at 0x3000 + 32u + w
//   RW 0x30C0-0x30CF    output owner of pad 8 + i ([2:0], 7 = none; host pads ignore writes)
//   W 0x6000-0x6003     HOST_IN push, tag = addr[1:0]
//   RW 0x8000-0x81FF    SRAM (host rotation slot)
//   R 0x0000 {live, RUN}; 0x0001 time; 0x0002 sticky {OVERRUN[13:8], LATE[5:0]}
//   R 0x2040 + c        DROPPED of port c
//   R 0x5000 + 32k + j  lane k: j = 0-3 r0-r3, 4 STATE, 5 {PEND[6:4], FLAGS[3:0]}
//   R 0x6004 / 0x6005   HOST_OUT {avail, tag[1:0]} / data (reading 0x6005 pops)
//   R 0x7000 + 2p (+1)  producer p {valid, seq, tag} (data)
//   R 0x7100 / 0x7101   pins A {a_oe[13:8], a_out[5:0]} / pins N {n_oe, n_out}
`default_nettype none
`include "trw_defs.vh"

module tt_um_tripwire (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);
    localparam SB = `TRW_SLOT_BITS;
    localparam PB = `TRW_PC_BITS;

    // ---------------------------------------------------------------- pads in, time, host
    reg [7:0] ui_s1, ui_s2, uio_s1, uio_s2;
    always @(posedge clk) begin
        ui_s1 <= ui_in;   ui_s2 <= ui_s1;
        uio_s1 <= uio_in; uio_s2 <= uio_s1;
    end

    reg [15:0] tnow;
    always @(posedge clk) begin
        if (!rst_n) tnow <= 16'd0;
        else        tnow <= tnow + 16'd1;
    end

    wire        miso, hwr, rd_req, rd_ack;
    wire [15:0] wa, wd, rd_addr;
    reg  [15:0] rd_data;
    r4_host u_host (
        .clk (clk), .rst_n (rst_n), .csn (ui_s2[4]), .sck (ui_s2[5]), .mosi (ui_s2[6]), .miso (miso),
        .wr (hwr), .wr_addr (wa), .wr_data (wd),
        .rd_req (rd_req), .rd_addr (rd_addr), .rd_data (rd_data), .rd_ack (rd_ack)
    );

    wire w_ctl  = hwr && (wa == 16'h0000);
    wire w_clr  = hwr && (wa == 16'h0002);
    wire w_slot = hwr && (wa[15:10] == 6'b000100);
    wire w_port = hwr && (wa[15:4] == 12'h200) && (wa[3:0] < 4'd13);
    wire w_pcfg = hwr && (wa[15:8] == 8'h30) && (wa[7:5] < 3'd6);
    wire w_own  = hwr && (wa[15:4] == 12'h30c) && (wa[3:0] != 4'd3) && (wa[3:0] != 4'd6);
    wire w_hin  = hwr && (wa[15:2] == 14'h1800);
    wire w_sram = hwr && (wa[15:9] == 7'b1000000);

    reg [2:0] run;
    reg       live;
    always @(posedge clk) begin
        if (!rst_n) begin
            run  <= 3'd0;
            live <= 1'b0;
        end else if (w_ctl) begin
            run  <= wd[2:0];
            live <= live || (wd[2:0] != 3'd0);
        end
    end

    // ---------------------------------------------------------------- fabric
    wire [12:0]  p_valid, p_seq, p_load, all_taken, avail, take;
    wire [233:0] p_tok, head;
    wire [103:0] dropped;
    reg  [129:0] port_cfg;
    reg  [12:0]  port_wr;
    integer c;
    always @(posedge clk) begin
        if (!rst_n) begin
            port_cfg <= 130'd0;
            port_wr  <= 13'd0;
        end else begin
            port_wr <= 13'd0;               // F5 acts the clock after the new sel is visible
            if (w_port) begin
                for (c = 0; c < 13; c = c + 1)
                    if ({28'd0, wa[3:0]} == c) port_cfg[10*c +: 10] <= wd[9:0];
                port_wr <= 13'd1 << wa[3:0];
            end
        end
    end
    r4_fabric u_fab (
        .clk (clk), .rst_n (rst_n), .p_valid (p_valid), .p_seq (p_seq), .p_load (p_load), .p_tok (p_tok),
        .port_cfg (port_cfg), .port_wr (port_wr), .take (take), .avail (avail), .head (head),
        .all_taken (all_taken), .dropped (dropped)
    );

    // HOST_IN (producer 12) and HOST_OUT (consumer 12)
    reg        hin_v, hin_s;
    reg [17:0] hin_t;
    wire hin_ld = w_hin && (!hin_v || all_taken[12]);
    always @(posedge clk) begin
        if (!rst_n) begin
            hin_v <= 1'b0;  hin_s <= 1'b0;  hin_t <= 18'd0;
        end else if (hin_ld) begin
            hin_v <= 1'b1;  hin_s <= !hin_s;  hin_t <= {wa[1:0], wd};
        end
    end
    assign p_valid[12] = hin_v;
    assign p_seq[12]   = hin_s;
    assign p_load[12]  = hin_ld;
    assign p_tok[233:216] = hin_t;
    assign take[12] = rd_ack && (rd_addr == 16'h6005) && avail[12];

    // ---------------------------------------------------------------- SRAM and its rotation (§14 R1)
    wire [1:0]  slot = tnow[1:0];
    wire [2:0]  q_en;
    wire [26:0] q_addr;
    reg         hp_v, hp_we, h_await;
    reg  [8:0]  hp_addr;
    reg  [15:0] hp_wd, h_rq;
    wire        s_en    = (slot == 2'd3) ? hp_v : q_en[slot];
    wire        s_we    = (slot == 2'd3) && hp_we;
    wire [8:0]  s_addr  = (slot == 2'd3) ? hp_addr : q_addr[9*slot +: 9];
    wire [15:0] s_rdata;
    trw_sram u_sram (
        .clk (clk), .rst_n (rst_n), .en (s_en), .we (s_we), .addr (s_addr), .wdata (hp_wd), .rdata (s_rdata)
    );
    wire h_rd = rd_req && (rd_addr[15:9] == 7'b1000000);
    always @(posedge clk) begin
        if (!rst_n) begin
            hp_v <= 1'b0;  hp_we <= 1'b0;  hp_addr <= 9'd0;  hp_wd <= 16'd0;  h_await <= 1'b0;  h_rq <= 16'd0;
        end else begin
            h_await <= (slot == 2'd3) && hp_v && !hp_we;
            if (h_await)
                h_rq <= s_rdata;
            if (w_sram || h_rd) begin
                hp_v <= 1'b1;  hp_we <= w_sram;
                hp_addr <= w_sram ? wa[8:0] : rd_addr[8:0];
                hp_wd <= wd;
            end else if (slot == 2'd3) begin
                hp_v <= 1'b0;
            end
        end
    end

    // ---------------------------------------------------------------- lanes
    wire [224:0] lane_dbg;
    genvar k;
    generate
        for (k = 0; k < 3; k = k + 1) begin : g_lane
            wire [12*SB-1:0] slots;
            wire [63:0]      kk;
            wire [15:0]      slot_rd;
            trw_slots u_slots (
                .clk (clk), .rst_n (rst_n), .we (w_slot && (wa[9:8] == k)),
                .waddr ({wa[7:4], wa[1:0]}), .wdata (wd), .slots (slots), .k (kk),
                .raddr (6'd0), .rdata (slot_rd)                  // no slot read-back (D-039)
            );
            wire [1:0]  ov, os;
            wire [35:0] ot;
            wire        rt_take, rt_nz, rz, call_req, rb, rir_valid;
            wire [4:0]  call_idx;
            wire [15:0] rir;
            trw_lane u_lane (
                .clk (clk), .rst_n (rst_n), .run (run[k]), .slots (slots), .k (kk), .time_now (tnow),
                .in_avail (avail[2*k +: 2]), .in_head (head[36*k +: 36]), .in_take (take[2*k +: 2]),
                .out_all_taken (all_taken[6+2*k +: 2]), .out_valid (ov), .out_seq (os), .out_tok (ot),
                .rir_valid (rir_valid), .rir (rir), .rt_take (rt_take), .rt_nz (rt_nz), .rz (rz),
                .call_req (call_req), .call_idx (call_idx), .rb_o (rb), .dbg (lane_dbg[75*k +: 75])
            );
            r4_seq u_seq (
                .clk (clk), .rst_n (rst_n), .run (run[k]), .my_slot (slot == k), .rb (rb),
                .call_req (call_req), .call_idx (call_idx), .rt_take (rt_take), .rdata (s_rdata),
                .req_en (q_en[k]), .req_addr (q_addr[9*k +: 9]), .rir_valid (rir_valid), .rir (rir)
            );
            // producers L<k>.O0 / O1 are the lane's own registers; a load shows as a seq change
            reg [1:0] os_q;
            always @(posedge clk) os_q <= os;
            assign p_valid[6+2*k +: 2] = ov;
            assign p_seq[6+2*k +: 2]   = os;
            assign p_load[6+2*k +: 2]  = os ^ os_q;   // one clock late: tap drops only (stub)
            assign p_tok[18*(6+2*k) +: 36] = ot;
            wire _unused_l = &{1'b0, slot_rd, rt_nz, rz};
        end
    endgenerate

    // ---------------------------------------------------------------- pin units
    reg  [5:0] clr_late, clr_ovr;
    always @(posedge clk) begin
        clr_late <= w_clr ? wd[5:0] : 6'd0;
        clr_ovr  <= w_clr ? wd[13:8] : 6'd0;
    end
    wire [23:0] pads = {uio_s2, uo_out, ui_s2};              // P1, P7
    wire [5:0]  a_out, a_oe, n_out, n_oe, late, ovr;
    wire [29:0] pin_a, pin_n;
    genvar u;
    generate
        for (u = 0; u < 6; u = u + 1) begin : g_unit
            wire [PB-1:0] cfg;
            wire          restart, rx_load;
            wire [1:0]    rx_tag;
            wire [15:0]   rx_data;
            trw_pin_cfg #(.FULL (0)) u_cfg (
                .clk (clk), .rst_n (rst_n), .we (w_pcfg && (wa[7:5] == u)), .waddr (wa[4:0]), .wdata (wd),
                .cfg (cfg), .restart (restart)
            );
            reg        pv, ps;
            reg [17:0] pt;
            wire free = !pv || all_taken[u];
            trw_pin_unit #(.FULL (0)) u_unit (
                .clk (clk), .rst_n (rst_n), .restart (restart), .live (live), .cfg (cfg), .pads (pads),
                .tx_avail (avail[6+u]), .tx_tag (head[18*(6+u)+16 +: 2]), .tx_data (head[18*(6+u) +: 16]),
                .tx_take (take[6+u]),
                .rx_free (free), .rx_load (rx_load), .rx_tag (rx_tag), .rx_data (rx_data),
                .a_out (a_out[u]), .a_oe (a_oe[u]), .n_out (n_out[u]), .n_oe (n_oe[u]),
                .late (late[u]), .overrun (ovr[u]), .clr_late (clr_late[u]), .clr_overrun (clr_ovr[u])
            );
            always @(posedge clk) begin
                if (!rst_n) begin
                    pv <= 1'b0;  ps <= 1'b0;  pt <= 18'd0;
                end else if (rx_load) begin
                    pv <= 1'b1;  ps <= !ps;  pt <= {rx_tag, rx_data};
                end
            end
            assign p_valid[u] = pv;
            assign p_seq[u]   = ps;
            assign p_load[u]  = rx_load;
            assign p_tok[18*u +: 18] = pt;
            assign pin_a[5*u +: 5] = cfg[`TRW_PC_PIN_A_MSB:`TRW_PC_PIN_A_LSB];
            assign pin_n[5*u +: 5] = cfg[`TRW_PC_PIN_N_MSB:`TRW_PC_PIN_N_LSB];
        end
    endgenerate

    // ---------------------------------------------------------------- pads out: owners (§7.1)
    reg  [47:0] own;                // pad 8 + i: own[3i +: 3]
    integer oi, i, j;
    always @(posedge clk) begin
        if (!rst_n)
            own <= {16{3'd7}};
        else if (w_own)
            for (oi = 0; oi < 16; oi = oi + 1)
                if ({28'd0, wa[3:0]} == oi) own[3*oi +: 3] <= wd[2:0];
    end
    reg [15:0] pv_o, pe_o;           // value / output enable for pads 8..23
    always @* begin
        pv_o = 16'd0;
        pe_o = 16'd0;
        for (i = 0; i < 16; i = i + 1)
            for (j = 0; j < 6; j = j + 1)
                if ({29'd0, own[3*i +: 3]} == j) begin
                    if ({27'd0, pin_a[5*j +: 5]} == i + 8) begin
                        pv_o[i] = a_out[j];  pe_o[i] = a_oe[j];
                    end else if ({27'd0, pin_n[5*j +: 5]} == i + 8) begin
                        pv_o[i] = n_out[j];  pe_o[i] = n_oe[j];
                    end
                end
    end
    wire irq = |{late, ovr};
    assign uo_out  = {pv_o[7], irq, pv_o[5:4], miso, pv_o[2:0]};
    assign uio_out = pv_o[15:8];
    assign uio_oe  = pe_o[15:8];

    // ---------------------------------------------------------------- host reads
    always @* begin
        rd_data = 16'd0;
        casez (rd_addr)
            16'h0000: rd_data = {live, 12'd0, run};
            16'h0001: rd_data = tnow;
            16'h0002: rd_data = {2'd0, ovr, 2'd0, late};
            16'h6004: rd_data = {avail[12], 13'd0, head[233:232]};
            16'h6005: rd_data = head[231:216];
            16'h7100: rd_data = {2'd0, a_oe, 2'd0, a_out};
            16'h7101: rd_data = {2'd0, n_oe, 2'd0, n_out};
            16'b1000_000?_????_????: rd_data = h_rq;
            default: begin
                if (rd_addr[15:4] == 12'h204 && rd_addr[3:0] < 4'd13)
                    rd_data = {8'd0, dropped[8*rd_addr[3:0] +: 8]};
                else if (rd_addr[15:4] == 12'h30c)
                    rd_data = {13'd0, own[3*rd_addr[3:0] +: 3]};
                else if (rd_addr[15:7] == 9'b0101_0000_0 && rd_addr[6:5] != 2'd3 && rd_addr[4:3] == 2'd0)
                    // lane k = addr[6:5]; j = addr[2:0]: 0-3 r0-r3, 4 STATE, 5 {PEND, FLAGS}
                    case (rd_addr[2:0])
                        3'd0, 3'd1, 3'd2, 3'd3:
                                rd_data = lane_dbg[75*rd_addr[6:5] + 16*rd_addr[1:0] +: 16];
                        3'd4:   rd_data = {12'd0, lane_dbg[75*rd_addr[6:5] + 64 +: 4]};
                        3'd5:   rd_data = {9'd0, lane_dbg[75*rd_addr[6:5] + 68 +: 7]};
                        default: rd_data = 16'd0;
                    endcase
                else if (rd_addr[15:5] == 11'b0111_0000_000 && rd_addr[4:1] < 4'd13)
                    rd_data = rd_addr[0] ? p_tok[18*rd_addr[4:1] +: 16]
                                         : {p_valid[rd_addr[4:1]], p_seq[rd_addr[4:1]], 12'd0,
                                            p_tok[18*rd_addr[4:1] + 16 +: 2]};
            end
        endcase
    end

    wire _unused = &{1'b0, ena, rd_req, pv_o[6], pv_o[3], pe_o[7:0]};
endmodule
