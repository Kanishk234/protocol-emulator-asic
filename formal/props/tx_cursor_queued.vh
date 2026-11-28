    // Queue a LEVEL action, then offer a second action while it is pending.
    (* anyconst *) reg test_long_first, test_same_pad;
    (* anyconst *) reg [1:0] test_prescale;
    (* anyconst *) reg [1:0] test_second_delay;
    reg [4:0] test_phase = 0;
    wire [1:0] test_first_delay = {1'b1, test_long_first};
    wire [2:0] test_clocks_per_tick = {1'b0, test_prescale} + 3'd1;
    wire [4:0] test_first_due = test_first_delay * test_clocks_per_tick;
    wire [4:0] test_second_clocks = test_second_delay * test_clocks_per_tick;
    wire [4:0] test_second_due = test_first_due + test_second_clocks;
    always @(posedge clk) begin
        if (test_phase != 31) test_phase <= test_phase + 1'b1;
    end
    always @* begin
        assume(rst_n == (test_phase != 0));
        assume(!restart && live && !idle && !idle_next && !carrier_active);
        assume(txmode == `TRW_PCE_TXMODE_LEVEL);
        assume(presc == {6'b0, test_prescale});
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
