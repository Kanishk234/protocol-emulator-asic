    // SYNC re-anchors the cursor, then GAP advances it before a LEVEL command.
    (* anyconst *) reg test_prescale;
    (* anyconst *) reg [1:0] test_gap, test_delay;
    reg [4:0] test_phase = 0;
    wire [2:0] test_ticks = {1'b0, test_gap} + {1'b0, test_delay};
    wire [4:0] test_requested = 5'd1 + (test_prescale ? {1'b0, test_ticks, 1'b0}
                                                     : {2'b0, test_ticks});
    wire [4:0] test_decision = test_requested > 5'd3 ? test_requested : 5'd3;
    always @(posedge clk) begin
        if (test_phase != 31) test_phase <= test_phase + 1'b1;
    end
    always @* begin
        assume(rst_n == (test_phase != 0));
        assume(!restart && live && !idle && !idle_next && !carrier_active);
        assume(txmode == `TRW_PCE_TXMODE_LEVEL);
        assume(presc == {7'b0, test_prescale});
        assume(tx_avail == (test_phase >= 1 && test_phase <= 3));
        assume(tx_tag == `TRW_TAG_CTRL);
        case (test_phase)
            1: assume(tx_data == {`TRW_CMD_SYNC, 12'b0});
            2: assume(tx_data == {`TRW_CMD_GAP, 10'b0, test_gap});
            default: assume(tx_data == {`TRW_CMD_LEVEL, 1'b1, 9'b0, test_delay});
        endcase
        if (test_phase != 0) begin
            assert(tx_take == (test_phase <= 3));
            assert(late_set == (test_phase == 3 && test_delay != 0 && test_requested < 3));
            assert(lvl == (test_phase >= test_decision + 2));
            assert(oe);
        end
    end
