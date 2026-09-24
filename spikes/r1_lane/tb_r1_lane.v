// R1 risk spike: functional sanity check of the spike lane (not a verification suite).
// Runs ISA.md §7.1 (forward r0 bytes from I0 to O0, then an EVENT on O1) and checks the data, the
// tags and the "3 clocks per byte" cost that ISA.md states for it.
`default_nettype none
`timescale 1ns / 1ps
`include "trw_defs.vh"

module tb_r1_lane;
    localparam N = 4;                                   // bytes to forward
    localparam [3:0] INIT = 4'd0, SEND = 4'd1, DEC = 4'd2, IDLE = 4'd3, CALLED = 4'd4;

    reg clk = 1'b0;
    always #10 clk = ~clk;
    reg rst_n = 1'b0;
    reg run = 1'b0;

    // host write port
    reg        we = 1'b0;
    reg [5:0]  waddr = 6'd0;
    reg [15:0] wdata = 16'd0;

    // I0 producer (the test drives it)
    reg        p_valid = 1'b0, p_seq = 1'b0;
    reg [15:0] p_data = 16'd0;
    wire       i0_last;

    // subscribers of O0 / O1 (the test takes every token at once)
    reg  [1:0] sub_last = 2'b00;
    wire [1:0] out_valid, out_seq;
    wire [35:0] out_tok;

    wire [12*`TRW_SLOT_BITS-1:0] slots;
    wire [63:0] k;
    wire [1:0]  in_avail, in_take;
    wire [35:0] in_head;
    wire        rt_take, rt_nz, rz, call_req, rb;
    wire [4:0]  call_idx;

    trw_slots u_slots (.clk (clk), .rst_n (rst_n), .we (we), .waddr (waddr), .wdata (wdata),
                       .slots (slots), .k (k), .raddr (6'd0), .rdata ());
    trw_cport #(.N(1)) u_i0 (
        .clk (clk), .rst_n (rst_n), .en (1'b1), .sel (4'd0), .accept (4'b1111),
        .src_valid (p_valid), .src_seq (p_seq), .src_tag (`TRW_TAG_DATA), .src_data (p_data),
        .take (in_take[0]), .avail (in_avail[0]), .head (in_head[17:0]), .last_seq (i0_last)
    );
    assign in_avail[1] = 1'b0;
    assign in_head[35:18] = 18'd0;

    trw_lane u_lane (
        .clk (clk), .rst_n (rst_n), .run (run), .slots (slots), .k (k), .time_now (16'd0),
        .in_avail (in_avail), .in_head (in_head), .in_take (in_take),
        .out_all_taken (~(sub_last ^ out_seq)), .out_valid (out_valid), .out_seq (out_seq),
        .out_tok (out_tok),
        .rir_valid (1'b0), .rir (16'd0), .rt_take (rt_take), .rt_nz (rt_nz), .rz (rz),
        .call_req (call_req), .call_idx (call_idx), .rb_o (rb)
    );

    // ---- slot images
    function [52:0] fld;
        input [52:0] val;
        input integer lsb;
        begin
            fld = val << lsb;
        end
    endfunction

    function [52:0] slot_word;
        input integer idx;
        begin
            case (idx)
                // slot 0: when STATE=SEND, f0=0 do MOV O0 := I0 ; deq ; STATE:=DEC
                0: slot_word = fld(1, `TRW_SLOT_V_LSB) | fld(1, `TRW_SLOT_SE_LSB) | fld(SEND, `TRW_SLOT_SV_LSB)
                             | fld(4'b0001, `TRW_SLOT_FM_LSB) | fld(0, `TRW_SLOT_FV_LSB)
                             | fld(`TRW_OP_MOV, `TRW_SLOT_OP_LSB) | fld(`TRW_DST_O0, `TRW_SLOT_DST_LSB)
                             | fld(`TRW_ASRC_I0, `TRW_SLOT_ASRC_LSB) | fld(1, `TRW_SLOT_DQ_LSB)
                             | fld(1, `TRW_SLOT_NSE_LSB) | fld(DEC, `TRW_SLOT_NS_LSB)
                             | fld(`TRW_TAG_ERR, `TRW_SLOT_OT_LSB) | fld(1, `TRW_SLOT_KT_LSB)
                             | fld(3, `TRW_SLOT_DF_LSB);
                //         (KT with A = I0: the head's DATA tag is kept, OT = ERR is not used; §14 L8)
                // slot 1: when STATE=DEC do SUB r0 := r0, #1 -> f0 ; STATE:=SEND
                1: slot_word = fld(1, `TRW_SLOT_V_LSB) | fld(1, `TRW_SLOT_SE_LSB) | fld(DEC, `TRW_SLOT_SV_LSB)
                             | fld(`TRW_OP_SUB, `TRW_SLOT_OP_LSB) | fld(`TRW_DST_R0, `TRW_SLOT_DST_LSB)
                             | fld(`TRW_ASRC_R0, `TRW_SLOT_ASRC_LSB) | fld(`TRW_BSEL_IMM, `TRW_SLOT_BSEL_LSB)
                             | fld(1, `TRW_SLOT_IMM_LSB) | fld(1, `TRW_SLOT_DFE_LSB) | fld(0, `TRW_SLOT_DF_LSB)
                             | fld(1, `TRW_SLOT_NSE_LSB) | fld(SEND, `TRW_SLOT_NS_LSB);
                // slot 2: when STATE=SEND, f0=1 do MOV O1 := zero, tag EVENT ; STATE:=IDLE
                //         KT is set too: with A = zero it must be ignored (§14 L8), so the tag stays EVENT
                2: slot_word = fld(1, `TRW_SLOT_V_LSB) | fld(1, `TRW_SLOT_SE_LSB) | fld(SEND, `TRW_SLOT_SV_LSB)
                             | fld(4'b0001, `TRW_SLOT_FM_LSB) | fld(4'b0001, `TRW_SLOT_FV_LSB)
                             | fld(`TRW_OP_MOV, `TRW_SLOT_OP_LSB) | fld(`TRW_DST_O1, `TRW_SLOT_DST_LSB)
                             | fld(`TRW_ASRC_ZERO, `TRW_SLOT_ASRC_LSB) | fld(`TRW_TAG_EVENT, `TRW_SLOT_OT_LSB)
                             | fld(1, `TRW_SLOT_KT_LSB)
                             | fld(1, `TRW_SLOT_NSE_LSB) | fld(IDLE, `TRW_SLOT_NS_LSB) | fld(3, `TRW_SLOT_DF_LSB);
                // slot 3 (setup): when STATE=INIT do MOVB r0 := #N ; STATE:=SEND
                3: slot_word = fld(1, `TRW_SLOT_V_LSB) | fld(1, `TRW_SLOT_SE_LSB) | fld(INIT, `TRW_SLOT_SV_LSB)
                             | fld(`TRW_OP_MOVB, `TRW_SLOT_OP_LSB) | fld(`TRW_DST_R0, `TRW_SLOT_DST_LSB)
                             | fld(`TRW_BSEL_IMM, `TRW_SLOT_BSEL_LSB) | fld(N, `TRW_SLOT_IMM_LSB)
                             | fld(1, `TRW_SLOT_NSE_LSB) | fld(SEND, `TRW_SLOT_NS_LSB) | fld(3, `TRW_SLOT_DF_LSB);
                // slot 4: when STATE=IDLE do CALL 5 ; STATE:=CALLED, with DST = O0 and DFE on f0.
                //         O0 still holds the last, untaken byte, and f0 = 1. Under §14 L10 (CALL
                //         ignores DST and DFE) it must fire anyway: no wait for O0, no reservation,
                //         no load, no PEND, and f0 stays 1 (a flag write would store R = 0).
                4: slot_word = fld(1, `TRW_SLOT_V_LSB) | fld(1, `TRW_SLOT_SE_LSB) | fld(IDLE, `TRW_SLOT_SV_LSB)
                             | fld(`TRW_OP_CALL, `TRW_SLOT_OP_LSB) | fld(`TRW_DST_O0, `TRW_SLOT_DST_LSB)
                             | fld(`TRW_ASRC_ZERO, `TRW_SLOT_ASRC_LSB) | fld(5, `TRW_SLOT_IMM_LSB)
                             | fld(1, `TRW_SLOT_DFE_LSB) | fld(0, `TRW_SLOT_DF_LSB)
                             | fld(1, `TRW_SLOT_NSE_LSB) | fld(CALLED, `TRW_SLOT_NS_LSB);
                default: slot_word = 53'd0;
            endcase
        end
    endfunction

    task host_write;
        input [5:0]  a;
        input [15:0] d;
        begin
            @(negedge clk);
            we = 1'b1; waddr = a; wdata = d;
            @(negedge clk);
            we = 1'b0;
        end
    endtask

    // ---- I0 producer: loads the next byte when free (§14 F3), bytes 0xA1, 0xA2, ...
    integer sent = 0;
    always @(posedge clk) begin
        if (run && sent < N + 2 && (!p_valid || i0_last == p_seq)) begin
            p_valid <= 1'b1;
            p_seq   <= ~p_seq;
            p_data  <= 16'h00A1 + sent;
            sent    <= sent + 1;
        end
    end

    // ---- subscribers: take and check. O0 takes the first N-1 bytes only, so the last byte stays in
    // O0 and the output is full when the CALL (slot 4) is evaluated.
    integer cycle = 0, got0 = 0, got1 = 0, last_t = -1, errors = 0;
    always @(posedge clk) cycle <= cycle + 1;
    always @(posedge clk) begin
        if (out_valid[0] && sub_last[0] != out_seq[0] && got0 < N - 1) begin
            sub_last[0] <= out_seq[0];
            if (out_tok[15:0] !== 16'h00A1 + got0 || out_tok[17:16] !== `TRW_TAG_DATA) begin
                $display("FAIL: O0 token %0d = %h tag %0d", got0, out_tok[15:0], out_tok[17:16]);
                errors = errors + 1;
            end
            if (last_t >= 0 && cycle - last_t != 3) begin
                $display("FAIL: O0 token %0d came %0d clocks after the previous one (expected 3)",
                         got0, cycle - last_t);
                errors = errors + 1;
            end
            last_t = cycle;
            got0 = got0 + 1;
        end
        if (out_valid[1] && sub_last[1] != out_seq[1]) begin
            sub_last[1] <= out_seq[1];
            if (out_tok[35:34] !== `TRW_TAG_EVENT)      // slot 2: KT with A = zero -> OT (§14 L8)
                begin
                $display("FAIL: O1 token tag %0d (expected EVENT: KT ignored when A is not an input)",
                         out_tok[35:34]);
                errors = errors + 1;
            end
            got1 = got1 + 1;
        end
    end

    // §14 L10, checked in the CALL's own EXEC clock: its EVAL edge must not have reserved O0 or set
    // PEND (the old behaviour set both and cleared them again at EXEC, invisible at the end).
    always @(posedge clk) begin
        if (u_lane.ex_slot && u_lane.ex_op == `TRW_OP_CALL && (u_lane.resv !== 2'b00 || u_lane.pend !== 3'b000)) begin
            $display("FAIL: CALL in EXEC with resv %b pend %b", u_lane.resv, u_lane.pend);
            errors = errors + 1;
        end
    end

    // §14 H1: halted after reset; nothing fires, is taken or loaded before RUN, while the slots are
    // still being written (unwritten latches are X in simulation).
    always @(posedge clk) begin
        if (rst_n && !run && (u_lane.ex_slot !== 1'b0 || u_lane.ex_rt !== 1'b0 || in_take !== 2'b00
                              || out_valid !== 2'b00 || u_lane.state !== INIT)) begin
            $display("FAIL: activity while halted: ex_slot %b ex_rt %b take %b out_valid %b STATE %0d",
                     u_lane.ex_slot, u_lane.ex_rt, in_take, out_valid, u_lane.state);
            errors = errors + 1;
        end
    end

    integer s, w;
    reg [63:0] img;
    initial begin
        if ($test$plusargs("vcd")) begin
            $dumpfile("tb_r1_lane.vcd");
            $dumpvars(0, tb_r1_lane);
        end
        repeat (3) @(posedge clk);
        rst_n = 1'b1;
        for (s = 0; s < 12; s = s + 1) begin
            img = {11'd0, slot_word(s)};
            for (w = 0; w < 4; w = w + 1)
                host_write(4*s + w, img[16*w +: 16]);
        end
        for (w = 0; w < 4; w = w + 1)
            host_write(48 + w, 16'd0);
        @(negedge clk);
        run = 1'b1;
        repeat (60) @(posedge clk);
        // O0: N loads in all (seq back to N mod 2); the last byte is still there, untaken, unchanged.
        if (got0 != N - 1 || got1 != 1 || !out_valid[0] || sub_last[0] == out_seq[0]
            || out_seq[0] !== N[0] || out_tok[15:0] !== 16'h00A1 + N - 1 || out_tok[17:16] !== `TRW_TAG_DATA) begin
            $display("FAIL: taken %0d + %0d; O0 valid %b seq %b data %h tag %0d", got0, got1,
                     out_valid[0], out_seq[0], out_tok[15:0], out_tok[17:16]);
            errors = errors + 1;
        end
        // §14 L10: the CALL fired although O0 was full; no reservation, no PEND, f0 not written.
        if (u_lane.state !== CALLED || !rb || call_idx !== 5'd5 || u_lane.resv !== 2'b00
            || u_lane.pend !== 3'b000 || u_lane.f[0] !== 1'b1) begin
            $display("FAIL: CALL: STATE %0d rb %b idx %0d resv %b pend %b f %b", u_lane.state, rb,
                     call_idx, u_lane.resv, u_lane.pend, u_lane.f);
            errors = errors + 1;
        end
        if (errors == 0)
            $display("tb_r1_lane: PASS (%0d bytes at 3 clocks each, EVENT; KT per L8, CALL per L10, H1)", N);
        else
            $display("tb_r1_lane: FAIL (%0d errors)", errors);
        $finish;
    end
endmodule
