// Verification-only composition of the actual native producer and full fabric.
// HOST_IN (source8) legally reaches four lane inputs and four unit TX ports.
module channel_native_box #(
    parameter EXTRA_TAPS = 0,
    parameter BLOCK_TX = 0
) (
    input wire clk, rst_n,
    input wire [3:0] stage,
    input wire request,
    input wire [17:0] input_token,
    input wire [3:0] blocking_take, tap_take, tap_accept, tap_clear,
    input wire [15:0] blocking_accept,
    output wire producer_free, producer_load, producer_valid, producer_seq,
    output wire [17:0] producer_token,
    output wire [3:0] blocking_avail,
    output wire [71:0] blocking_head,
    output wire [31:0] tap_dropped
);
    wire [8:0] all_taken, avail;
    wire [161:0] head;
    wire [89:0] state;
    wire [71:0] dropped;
    wire [3:0] config_index = BLOCK_TX ? stage ^ 4'd4 : stage;
    wire [8:0] config_we = rst_n && stage < 8 ? (9'd1 << config_index) : 9'd0;
    wire [7:0] consumer_take = BLOCK_TX ? {blocking_take,tap_take} : {tap_take,blocking_take};
    trw_chan_prod producer (
        .clk(clk), .rst_n(rst_n), .load_req(stage == 9 && request),
        .tok_in(input_token), .all_taken(all_taken[8]),
        .free(producer_free), .load(producer_load), .valid(producer_valid),
        .seq(producer_seq), .tok(producer_token)
    );
    trw_fabric fabric (
        .clk(clk), .rst_n(rst_n),
        .p_valid({producer_valid,8'd0}), .p_seq({producer_seq,8'd0}),
        .p_load({producer_load,8'd0}), .p_tok({producer_token,144'd0}),
        .all_taken(all_taken), .take({1'b0,consumer_take}),
        .avail(avail), .head(head), .cfg_we(config_we),
        .cfg_en(stage < 4 || EXTRA_TAPS != 0), .cfg_tap(stage >= 4),
        .cfg_sel(4'd4), .cfg_accept(stage < 4 ? blocking_accept[4*stage[1:0] +: 4] : tap_accept),
        .clr_dropped({1'b0,tap_clear,4'd0}), .port_state(state), .dropped(dropped)
    );
    assign blocking_avail = BLOCK_TX ? avail[7:4] : avail[3:0];
    assign blocking_head = BLOCK_TX ? head[143:72] : head[71:0];
    assign tap_dropped = dropped[63:32];
endmodule

module channel_blocking #(
    parameter ALWAYS_READY = 0,
    parameter BLOCK_TX = 0
) (input wire clk);
    (* anyseq *) reg rst_n, request;
    (* anyseq *) reg [17:0] input_token;
    (* anyseq *) reg [3:0] arbitrary_take;
    wire [3:0] take = ALWAYS_READY ? 4'hf : arbitrary_take;
    reg past_valid = 0;
    reg [3:0] stage;
    always @(posedge clk) begin
        past_valid <= 1;
        if (!past_valid) assume(!rst_n); else assume(rst_n);
        if (!rst_n) stage <= 0;
        else if (stage < 9) stage <= stage + 1'b1;
    end
    wire free, load, valid, seq;
    wire [17:0] token;
    wire [3:0] avail;
    wire [71:0] head;
    wire [31:0] unused_drops;
    channel_native_box #(.BLOCK_TX(BLOCK_TX)) box (
        .clk(clk),.rst_n(rst_n),.stage(stage),.request(request),.input_token(input_token),
        .blocking_take(take),.tap_take(4'd0),.tap_accept(4'hf),.tap_clear(4'd0),
        .blocking_accept(16'hffff),
        .producer_free(free),.producer_load(load),.producer_valid(valid),
        .producer_seq(seq),.producer_token(token),.blocking_avail(avail),
        .blocking_head(head),.tap_dropped(unused_drops)
    );
    // Ghost ledger is an oracle only: never feeds any native control input.
    reg [3:0] pending;
    reg issued_valid;
    reg [17:0] issued_token;
    reg [1:0] generations;
    reg saw_stall;
    wire [3:0] fire = avail & take;
    integer i;
    always @(posedge clk) begin
        if (!rst_n) begin
            pending <= 0;
            issued_valid <= 0;
            issued_token <= 0;
            generations <= 0;
            saw_stall <= 0;
        end else begin
            if (load) begin
                pending <= 4'hf;
                issued_valid <= 1;
                issued_token <= input_token;
                if (generations != 3) generations <= generations + 1'b1;
            end else pending <= pending & ~fire;
            if (stage == 9 && pending != 0 && request && !free && take == 0) saw_stall <= 1;
            if (stage == 9) begin
                assert(valid == issued_valid);
                if (valid) assert(token == issued_token);
                assert(avail == pending);
                assert(!load || pending == 0);
                assert((fire & ~pending) == 0);
                assert(!(load && |fire)); // same-edge takes do not free a producer
                for (i=0;i<4;i=i+1)
                    if (avail[i]) assert(head[18*i +:18] == issued_token);
                if (ALWAYS_READY && past_valid && $past(stage == 9 && load))
                    assert(fire == 4'hf);
                cover(generations >= 2 && pending == 0);
                if (!ALWAYS_READY) cover(generations >= 2 && pending == 0 && saw_stall);
            end
        end
    end
    genvar port_index;
    generate for (port_index=0;port_index<4;port_index=port_index+1) begin: held_head
        always @(posedge clk)
            if (past_valid && $past(rst_n && stage == 9 && avail[port_index] && !take[port_index])) begin
                assert(avail[port_index]);
                assert(head[18*port_index +:18] == $past(head[18*port_index +:18]));
            end
    end endgenerate
endmodule

module channel_filtered_tx(input wire clk);
    (* anyseq *) reg rst_n, request;
    (* anyseq *) reg [17:0] input_token;
    (* anyseq *) reg [3:0] take;
    (* anyconst *) reg [15:0] accept;
    reg past_valid = 0;
    reg [3:0] stage;
    always @(posedge clk) begin
        past_valid <= 1;
        if (!past_valid) assume(!rst_n); else assume(rst_n);
        if (!rst_n) stage <= 0;
        else if (stage < 9) stage <= stage + 1'b1;
    end
    wire [3:0] avail;
    wire [71:0] head;
    channel_native_box #(.BLOCK_TX(1)) box (
        .clk(clk),.rst_n(rst_n),.stage(stage),.request(request),.input_token(input_token),
        .blocking_take(take),.tap_take(4'd0),.tap_accept(4'd0),.tap_clear(4'd0),
        .blocking_accept(accept),.blocking_avail(avail),.blocking_head(head)
    );
    genvar port_index;
    generate for (port_index=0;port_index<4;port_index=port_index+1) begin: filtered_head
        wire [17:0] token = head[18*port_index +:18];
        wire [3:0] mask = accept[4*port_index +:4];
        always @(posedge clk) begin
            if (past_valid && $past(rst_n && stage == 9 && avail[port_index] && !take[port_index])) begin
                assert(avail[port_index]);
                assert(token == $past(token));
            end
            cover(rst_n && stage == 9 && mask != 4'hf && avail[port_index] && !take[port_index]);
        end
    end endgenerate
endmodule

module channel_taps(input wire clk);
    (* anyseq *) reg rst_n, request;
    (* anyseq *) reg [17:0] input_token;
    (* anyseq *) reg [3:0] take, tap_take, tap_accept, tap_clear;
    reg past_valid = 0;
    reg [3:0] stage;
    always @(posedge clk) begin
        past_valid <= 1;
        if (!past_valid) assume(!rst_n); else assume(rst_n);
        if (!rst_n) stage <= 0;
        else if (stage < 9) stage <= stage + 1'b1;
    end
    wire [1:0] free,load,valid,seq;
    wire [35:0] token;
    wire [7:0] avail;
    wire [143:0] head;
    wire [63:0] dropped;
    genvar g;
    generate for(g=0;g<2;g=g+1) begin: copies
        channel_native_box #(.EXTRA_TAPS(g)) box (
            .clk(clk),.rst_n(rst_n),.stage(stage),.request(request),.input_token(input_token),
            .blocking_take(take),.tap_take(tap_take),.tap_accept(tap_accept),.tap_clear(tap_clear),
            .blocking_accept(16'hffff),
            .producer_free(free[g]),.producer_load(load[g]),.producer_valid(valid[g]),
            .producer_seq(seq[g]),.producer_token(token[18*g +:18]),
            .blocking_avail(avail[4*g +:4]),.blocking_head(head[72*g +:72]),
            .tap_dropped(dropped[32*g +:32])
        );
    end endgenerate
    always @(posedge clk) if(rst_n && stage==9) begin
        assert(free[0]==free[1]);
        assert(load[0]==load[1]);
        assert(valid[0]==valid[1]);
        assert(seq[0]==seq[1]);
        assert(token[17:0]==token[35:18]);
        assert(avail[3:0]==avail[7:4]);
        assert(head[71:0]==head[143:72]);
        cover(dropped[39:32]!=0 && valid[0] && |avail[3:0]);
    end
endmodule
