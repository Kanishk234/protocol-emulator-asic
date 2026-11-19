// Inserted only into an ignored verification copy of the actual pin unit.
reg formal_past = 0;
always @(posedge clk) begin
    formal_past <= 1;
    if (!formal_past) assume(!rst_n); else assume(rst_n);
    if (formal_past) begin
        assume(cfg == $past(cfg));
        assume(period >= 24'd256);
        if (FULL != 0) begin
            assume(sampleofs < period);
            assume(idle_bits != 0);
            if (stuff_n != 0)
                assume({1'b0,idle_bits} >= {2'b0,stuff_n} + (delim == 1 ? 6'd2 : 6'd1));
        end
        if (USE_SAMPLE_DELTA) assume(sample_delta == {1'b0,sampleofs} - {1'b0,period});
        if (USE_BITSYNC_ACTIVE) assume(bitsync_active == ((FULL != 0) && txmode == `TRW_PCE_TXMODE_BITSYNC && rxmode == `TRW_PCE_RXMODE_BITSYNC));
        if (USE_LEVEL_CACHE) begin
            assume(idle_next == idle);
            assume(carrier_active == ((FULL != 0) && |carrier[23:9]));
        end
        if ($past(live)) assume(live);
        if ($past(tx_avail && !tx_take)) begin
            assume(tx_avail);
            assume(tx_tag == $past(tx_tag));
            assume(tx_data == $past(tx_data));
        end
        if ($past(!rst_n || restart)) begin
            assert(!overrun);
            assert(!late);
        end else begin
            assert(overrun == $past(ovr_h || ovr_b || (overrun && !clr_overrun)));
            assert(late == $past(late_t || late_b || (late && !clr_late)));
        end
        assert(!rx_load || rx_free);
        assert(!(load_h && load_b));
        if (load_h) begin
            assert(rx_load);
            assert(rx_tag == tag_h);
            assert(rx_data == data_h);
        end else if (load_b) begin
            assert(rx_load);
            assert(rx_tag == tag_b);
            assert(rx_data == data_b);
        end
        cover($past(rst_n && !restart && clr_overrun && ovr_set) && overrun);
        cover($past(rst_n && !restart && clr_overrun && !ovr_set && overrun) && !overrun);
        if (FULL != 0) cover(load_h && ovr_b && bs_on);
    end
end
