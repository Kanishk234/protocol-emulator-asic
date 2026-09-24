// R2 risk spike (branch spike/r2-latch only; never merged): one TRIPWIRE lane with its latch slot
// array through the Tiny Tapeout cmos5l flow, driven from the pins. The lane, ALU, slot store and
// consumer port are the R1 spike's files (spikes/r1_lane/), unchanged.
//
// Around the lane, pin-driven stand-ins for the rest of the chip:
//   - a producer register feeding I0 through a real consumer port (1 source, all tags accepted);
//   - blocking subscribers for O0 and O1 that take a token on a strobe (so the §4.4 release rule
//     and the implicit output-free check are exercised);
//   - a routine instruction register (RIR) loaded from the pins and cleared when its step is taken.
//
// Pins (strobes are synchronised, 2 flops, and act on their rising edge; hold them >= 3 clocks):
//   ui[0]    REG_WR   load uio_in into register REGSEL = ui[3:1]:
//                     0 ADDR[5:0] (slot store word)   1 WDATA[7:0]   2 WDATA[15:8]
//                     3 TOK[7:0]                      4 TOK[15:8]
//                     5 CTRL: [0] RUN, [1] 1 = load RIR from WDATA (RIR valid until its step runs),
//                             [3:2] TAG of pushed tokens
//                     6 RSEL[2:0] (uo_out select)     7 unused
//   ui[4]    SLOT_WR  slot store word ADDR := WDATA (ignored while RUN)
//   ui[5]    PUSH     I0 producer := {TAG, TOK} (ignored while it still holds an untaken token)
//   ui[6]    POP0     take the token on O0 (if there is one)
//   ui[7]    POP1     take the token on O1 (if there is one)
//   uo_out by RSEL:   0/1 slot store word ADDR [7:0]/[15:8]; 2/3 O0 data [7:0]/[15:8];
//                     4/5 O1 data [7:0]/[15:8];
//                     6 {o0_avail, o0_tag[1:0], o1_avail, o1_tag[1:0], i0_full, run};
//                     7 {4'b0, rir_valid, call_req_seen, rb, rz}
//   uio      inputs only (uio_oe = 0)
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
    // ---- strobes
    reg [2:0] s_reg, s_slot, s_push, s_pop0, s_pop1;
    always @(posedge clk) begin
        if (!rst_n) begin
            s_reg  <= 3'd0;
            s_slot <= 3'd0;
            s_push <= 3'd0;
            s_pop0 <= 3'd0;
            s_pop1 <= 3'd0;
        end else begin
            s_reg  <= {s_reg[1:0],  ui_in[0]};
            s_slot <= {s_slot[1:0], ui_in[4]};
            s_push <= {s_push[1:0], ui_in[5]};
            s_pop0 <= {s_pop0[1:0], ui_in[6]};
            s_pop1 <= {s_pop1[1:0], ui_in[7]};
        end
    end
    wire reg_edge  = s_reg[1]  && !s_reg[2];
    wire slot_edge = s_slot[1] && !s_slot[2];
    wire push_edge = s_push[1] && !s_push[2];
    wire pop0_edge = s_pop0[1] && !s_pop0[2];
    wire pop1_edge = s_pop1[1] && !s_pop1[2];

    // ---- byte registers
    reg [5:0]  addr_reg;
    reg [15:0] wdata_reg, tok_reg;
    reg        run;
    reg [1:0]  push_tag;
    reg [2:0]  rsel;
    reg        rir_valid;
    reg [15:0] rir;
    wire       rt_take;
    always @(posedge clk) begin
        if (!rst_n) begin
            addr_reg  <= 6'd0;
            wdata_reg <= 16'd0;
            tok_reg   <= 16'd0;
            run       <= 1'b0;
            push_tag  <= 2'd0;
            rsel      <= 3'd0;
            rir_valid <= 1'b0;
            rir       <= 16'd0;
        end else begin
            if (rt_take)
                rir_valid <= 1'b0;
            if (reg_edge) begin
                case (ui_in[3:1])
                    3'd0: addr_reg         <= uio_in[5:0];
                    3'd1: wdata_reg[7:0]   <= uio_in;
                    3'd2: wdata_reg[15:8]  <= uio_in;
                    3'd3: tok_reg[7:0]     <= uio_in;
                    3'd4: tok_reg[15:8]    <= uio_in;
                    3'd5: begin
                        run      <= uio_in[0];
                        push_tag <= uio_in[3:2];
                        if (uio_in[1]) begin
                            rir       <= wdata_reg;
                            rir_valid <= 1'b1;
                        end
                    end
                    3'd6: rsel             <= uio_in[2:0];
                    default: ;
                endcase
            end
        end
    end

    // ---- time base
    reg [15:0] time_now;
    always @(posedge clk) begin
        if (!rst_n)
            time_now <= 16'd0;
        else
            time_now <= time_now + 16'd1;
    end

    // ---- slot store
    wire [12*`TRW_SLOT_BITS-1:0] slots;
    wire [63:0] k;
    wire [15:0] slot_rd;
    trw_slots u_slots (
        .clk (clk), .rst_n (rst_n), .we (slot_edge && !run), .waddr (addr_reg), .wdata (wdata_reg),
        .slots (slots), .k (k), .raddr (addr_reg), .rdata (slot_rd)
    );

    // ---- I0: producer register + consumer port
    reg        p_valid, p_seq;
    reg [17:0] p_tok;
    wire       i0_last;
    wire [1:0] in_take;
    wire       i0_avail;
    wire [17:0] i0_head;
    wire       p_free = !p_valid || (i0_last == p_seq);
    always @(posedge clk) begin
        if (!rst_n) begin
            p_valid <= 1'b0;
            p_seq   <= 1'b0;
            p_tok   <= 18'd0;
        end else if (push_edge && p_free) begin
            p_valid <= 1'b1;
            p_seq   <= !p_seq;
            p_tok   <= {push_tag, tok_reg};
        end
    end
    trw_cport #(.N(1)) u_i0 (
        .clk (clk), .rst_n (rst_n), .en (1'b1), .sel (4'd0), .accept (4'b1111),
        .src_valid (p_valid), .src_seq (p_seq), .src_tag (p_tok[17:16]), .src_data (p_tok[15:0]),
        .take (in_take[0]), .avail (i0_avail), .head (i0_head), .last_seq (i0_last)
    );

    // ---- lane
    wire [1:0]  out_valid, out_seq;
    wire [35:0] out_tok;
    reg  [1:0]  sub_last;
    wire        rt_nz, rz, call_req, rb;
    wire [4:0]  call_idx;
    trw_lane u_lane (
        .clk (clk), .rst_n (rst_n), .run (run), .slots (slots), .k (k), .time_now (time_now),
        .in_avail ({1'b0, i0_avail}), .in_head ({18'd0, i0_head}), .in_take (in_take),
        .out_all_taken (~(sub_last ^ out_seq)), .out_valid (out_valid), .out_seq (out_seq),
        .out_tok (out_tok),
        .rir_valid (rir_valid), .rir (rir), .rt_take (rt_take), .rt_nz (rt_nz), .rz (rz),
        .call_req (call_req), .call_idx (call_idx), .rb_o (rb)
    );

    // ---- subscribers of O0 / O1 (blocking; take on a strobe)
    wire [1:0] o_avail = out_valid & (sub_last ^ out_seq);
    reg        call_seen;
    always @(posedge clk) begin
        if (!rst_n) begin
            sub_last  <= 2'd0;
            call_seen <= 1'b0;
        end else begin
            if (pop0_edge && o_avail[0])
                sub_last[0] <= out_seq[0];
            if (pop1_edge && o_avail[1])
                sub_last[1] <= out_seq[1];
            if (call_req)
                call_seen <= 1'b1;
        end
    end

    // ---- pins
    reg [7:0] uo_mux;
    always @* begin
        case (rsel)
            3'd0:    uo_mux = slot_rd[7:0];
            3'd1:    uo_mux = slot_rd[15:8];
            3'd2:    uo_mux = out_tok[7:0];
            3'd3:    uo_mux = out_tok[15:8];
            3'd4:    uo_mux = out_tok[25:18];
            3'd5:    uo_mux = out_tok[33:26];
            3'd6:    uo_mux = {o_avail[0], out_tok[17:16], o_avail[1], out_tok[35:34], !p_free, run};
            default: uo_mux = {4'd0, rir_valid, call_seen, rb, rz};
        endcase
    end
    assign uo_out  = uo_mux;
    assign uio_out = 8'h00;
    assign uio_oe  = 8'h00;

    wire _unused = &{1'b0, ena, in_take[1], rt_nz, call_idx};
endmodule
