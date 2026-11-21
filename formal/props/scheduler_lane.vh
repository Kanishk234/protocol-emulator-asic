    reg sched_initialized = 0;
    reg [11:0] expected_pick;
    reg found;
    integer si;
    always @* begin
        expected_pick = 0;
        found = 0;
        for (si = 0; si < 12; si = si + 1)
            if (!found && ready[si] && (!rt_ok || urgent[si])) begin
                expected_pick[si] = 1;
                found = 1;
            end
    end
    always @(posedge clk) begin
        sched_initialized <= 1;
        if (!sched_initialized) assume(!rst_n);
        if (sched_initialized) begin
            assert(onehot == expected_pick);
            assert(fire == (|expected_pick));
            assert(rt_take == (rt_ok && !(|expected_pick)));
            assert(ex_slot == ($past(rst_n) && $past(fire)));
            assert(ex_rt == ($past(rst_n) && $past(rt_take)));
            assert(pend == (ex_fw ? (3'b001 << ex_df) : 3'b000));
            if ($past(rst_n) && $past(ex_fw))
                assert(f[$past(ex_df)] == $past(alu_r));
            cover(ex_fw && fire && s_fw && ex_df == s_df);

            cover(fire && rt_ok);
            cover(rt_take && (|ready));
        end
    end
    // A released token stays released until its producer changes sequence.
    always @(posedge clk) begin
        if (sched_initialized && rst_n && $past(rst_n)) begin
            assume((($past(out_all_taken) & ~(out_seq ^ $past(out_seq))) &
                    ~out_all_taken) == 2'b00);
        end
    end
