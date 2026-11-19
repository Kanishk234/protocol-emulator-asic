// Native BITSYNC producer arbitration, including its buffered status semantics.
always @(posedge clk) begin
    assert(!rx_load || rx_free);
    if (fr_want && !rx_free) assert(ovr_set);
    if (st_hold && st_keep) assert(ovr_set);
    if (fr_want && rx_free) begin
        assert(rx_load);
        assert(rx_tag == fr_tag);
        assert(rx_data == fr_data);
    end
    if (!fr_want && !st_v && st_new && rx_free) begin
        assert(rx_load);
        assert(rx_tag == `TRW_TAG_EVENT);
        assert(rx_data == st_nd);
    end
    if (!fr_want && st_v && rx_free) begin
        assert(rx_load);
        assert(rx_tag == `TRW_TAG_EVENT);
        assert(rx_data == st_d);
    end
end
reg formal_bs_past = 0;
always @(posedge clk) begin
    formal_bs_past <= 1;
    if (formal_bs_past) begin
        if ($past(!rst_n || restart || !active)) assert(!st_v);
        else if ($past(st_hold && !st_keep)) begin
            assert(st_v);
            assert(st_d == $past(st_nd));
        end else if ($past(ld_sth)) assert(!st_v);
        else begin
            assert(st_v == $past(st_v));
            assert(st_d == $past(st_d));
        end
    end
end
