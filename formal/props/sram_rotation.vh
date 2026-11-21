    reg rotation_check_started = 0;
    always @(posedge clk) begin
        rotation_check_started <= 1;
        if (!rotation_check_started) assume(!rst_n);
        if (rotation_check_started) begin
            if ($past(rst_n)) assert(slot == $past(slot) + 2'd1);
            else assert(slot == 2'd0);
            assert(slot == 0 || !l_en[0]);
            assert(slot == 1 || !l_en[1]);
            assert(slot == 3 || !h_en);
            case (slot)
                2'd0: assert({s_en,s_we,s_addr,s_wd} == {l_en[0],l_we[0],l_addr[8:0],l_wd[15:0]});
                2'd1: assert({s_en,s_we,s_addr,s_wd} == {l_en[1],l_we[1],l_addr[17:9],l_wd[31:16]});
                2'd2: assert(!s_en);
                2'd3: assert({s_en,s_we,s_addr,s_wd} == {h_en,h_we,h_addr,h_wd});
            endcase
            cover(slot == 0 && rst_n);
            cover(slot == 1 && rst_n);
            cover(slot == 2 && rst_n);
            cover(slot == 3 && rst_n);
        end
    end
