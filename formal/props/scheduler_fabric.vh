    reg started = 1'b0;
    always @(posedge clk) begin
        started <= 1'b1;
        if (!started)
            assume(!rst_n);
        if (started && rst_n && $past(rst_n)) begin
            assert((($past(all_taken) & ~(p_seq ^ $past(p_seq))) &
                    ~all_taken) == 9'b0);
            cover($past(cfg_we[8]) && en[8] && !tap[8] &&
                  sel[35:32] == 4'd0 && p_valid[4] && all_taken[4]);
        end
    end
