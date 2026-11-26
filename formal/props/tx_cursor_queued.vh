    // Queue a LEVEL action, then offer a second action while it is pending.
    (* anyconst *) reg test_prescale, test_long_first, test_same_pad;
    (* anyconst *) reg [1:0] test_second_delay;
    reg [3:0] test_phase = 0;
    wire [1:0] test_first_delay = {1'b1, test_long_first};
    wire [3:0] test_first_due = test_prescale ? {1'b0, test_first_delay, 1'b0}
                                              : {2'b0, test_first_delay};
    wire [3:0] test_second_clocks = test_prescale ? {1'b0, test_second_delay, 1'b0}
                                                  : {2'b0, test_second_delay};
    wire [3:0] test_second_due = test_first_due + test_second_clocks;
    always @(posedge clk) begin
        if (test_phase != 15) test_phase <= test_phase + 1'b1;
    end
    always @* begin
        assume(test_second_delay <= 2);
        assume(rst_n == (test_phase != 0));
        assume(!restart && live && !idle && !idle_next && !carrier_active);
        assume(txmode == `TRW_PCE_TXMODE_LEVEL);
        assume(presc == {7'b0, test_prescale});
        assume(tx_avail == (test_phase != 0 && test_phase <= test_first_due));
        assume(tx_tag == `TRW_TAG_CTRL);
        assume(tx_data == (test_phase == 1
                           ? {`TRW_CMD_LEVEL, 1'b1, 9'b0, test_first_delay}
                           : {test_same_pad ? `TRW_CMD_LEVEL : `TRW_CMD_OE,
                              1'b0, 9'b0, test_second_delay}));
        if (test_phase != 0) begin
            assert(tx_take == (test_phase == 1 || test_phase == test_first_due));
            assert(!late_set);
            assert(lvl == (test_phase >= test_first_due + 2 &&
                           (!test_same_pad || test_phase < test_second_due + 2)));
            assert(oe == (test_same_pad || test_phase < test_second_due + 2));
        end
    end
