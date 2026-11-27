module fabric_isolation(input wire clk, rst_n);
    (* anyseq *) reg [8:0] valid, seq, load, take, cfg_we, clear;
    (* anyseq *) reg [161:0] token;
    (* anyseq *) reg [1:0] peer_valid, peer_seq, peer_load;
    (* anyseq *) reg [35:0] peer_token;
    (* anyseq *) reg cfg_en, cfg_tap;
    (* anyseq *) reg [3:0] cfg_sel, cfg_accept;
    wire [8:0] a_avail, b_avail;
    wire [161:0] a_head, b_head;
    wire [89:0] a_state, b_state;
    wire [71:0] a_drop, b_drop;
    trw_fabric a (
        .clk(clk), .rst_n(rst_n), .p_valid(valid), .p_seq(seq),
        .p_load(load), .p_tok(token), .take(take), .avail(a_avail),
        .head(a_head), .cfg_we(cfg_we), .cfg_en(cfg_en), .cfg_tap(cfg_tap),
        .cfg_sel(cfg_sel), .cfg_accept(cfg_accept), .clr_dropped(clear),
        .port_state(a_state), .dropped(a_drop)
    );
    trw_fabric b (
        .clk(clk), .rst_n(rst_n),
        .p_valid({valid[8], peer_valid, valid[5:0]}),
        .p_seq({seq[8], peer_seq, seq[5:0]}),
        .p_load({load[8], peer_load, load[5:0]}),
        .p_tok({token[161:144], peer_token, token[107:0]}),
        .take(take), .avail(b_avail), .head(b_head),
        .cfg_we(cfg_we), .cfg_en(cfg_en), .cfg_tap(cfg_tap), .cfg_sel(cfg_sel),
        .cfg_accept(cfg_accept), .clr_dropped(clear),
        .port_state(b_state), .dropped(b_drop)
    );
    reg initialized = 0;
    always @(posedge clk) begin
        initialized <= 1;
        if (!initialized) assume(!rst_n);
`ifndef ISO_ALLOW_PEER
        // Select codes 0–4 name pin units or HOST_IN on both L0 ports.
        if (|cfg_we[1:0]) assume(cfg_sel <= 4);
`endif
        if (initialized) begin
            assert({a_avail[1:0], a_head[35:0], a_state[19:0], a_drop[15:0]} ==
                   {b_avail[1:0], b_head[35:0], b_state[19:0], b_drop[15:0]});
            cover(a_avail[0] && peer_token != token[143:108]);
        end
    end
endmodule
