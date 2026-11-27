    // Bounded one-command check, with an independent clock-count oracle.
    (* anyconst *) reg [1:0] test_issue, test_delay;
    (* anyconst *) reg [2:0] test_prescale;
    (* anyconst *) reg test_oe;
    reg [4:0] test_phase = 0;
    wire [3:0] test_clocks_per_tick = {1'b0, test_prescale} + 4'd1;
    wire [4:0] test_requested = test_delay * test_clocks_per_tick;
    wire [4:0] test_decision = test_requested > {3'b0, test_issue}
                               ? test_requested : {3'b0, test_issue};
    always @(posedge clk) begin
        if (test_phase != 31) test_phase <= test_phase + 1'b1;
    end
    always @* begin
        assume(test_issue != 0);
        assume(rst_n == (test_phase != 0));
        assume(!restart && live && !idle && !idle_next && !carrier_active);
        assume(txmode == `TRW_PCE_TXMODE_LEVEL);
        assume(presc == {5'b0, test_prescale});
        assume(tx_avail == (test_phase == test_issue));
        assume(tx_tag == `TRW_TAG_CTRL);
        assume(tx_data == {test_oe ? `TRW_CMD_OE : `TRW_CMD_LEVEL,
                           !test_oe, 9'b0, test_delay});
        if (test_phase == test_issue) begin
            assert(tx_take);
            assert(late_set == (test_delay != 0 && {3'b0, test_issue} > test_requested));
        end
        if (test_phase != 0) begin
            assert(lvl == (!test_oe && test_phase >= test_decision + 2));
            assert(oe == !(test_oe && test_phase >= test_decision + 2));
        end
    end
