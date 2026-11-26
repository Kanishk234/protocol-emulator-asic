    // Signed widened intermediates avoid circular reliance on the RTL sign tests.
    wire signed [17:0] wide_base = (w_fire || (use_pe && pe_m1)) ? -18'sd1 :
                                    use_pe ? 18'sd0 : $signed({{2{eq[15]}}, eq});
    wire signed [17:0] wide_delta = wide_base - $signed({6'b0, h_d});
    wire reset_cursor = tk && !h_ext && (c_sync || tk_late);
    wire apply_delay = tk && !h_ext && !reset_cursor && (c_gap || tk_timed);
    wire signed [17:0] selected_quotient = reset_cursor ? -18'sd1 :
                                          apply_delay ? wide_delta : wide_base;
    wire [8:0] prescale_span = {1'b0, presc} + 9'd1;
    wire [8:0] next_remainder = reset_cursor ? prescale_span : {1'b0, r_b} + 9'd1;
    wire crosses_tick = next_remainder == prescale_span;
    wire signed [17:0] expected_quotient =
        (crosses_tick && selected_quotient < 18'sd32767)
        ? selected_quotient + 18'sd1 : selected_quotient;

    always @* begin
        assume(r_b <= presc);
        // The upstream admission guard rejects a delayed cursor underflow.
        assume(!apply_delay || wide_delta >= -18'sd32768);
        assert($signed(q_b) == wide_base);
        assert($signed(q_sub) == wide_delta);
        assert(q_uf == (wide_delta < -18'sd32768));
        assert(late == (wide_delta >= 18'sd0));
        assert(at_m1 == (wide_delta == -18'sd1 && {1'b0, r_b} + 9'd1 == prescale_span));
        assert($signed(q_inc) == expected_quotient);
        assert({1'b0, r_inc} == (crosses_tick ? 9'd0 : next_remainder));
        assert(r_inc <= presc);
    end
