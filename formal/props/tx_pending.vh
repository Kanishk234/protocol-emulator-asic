    // Check the pending record across arbitrary command histories.
    wire check_enqueue = tk_timed && !tk_now;
    wire check_cancel = !rst_n || restart;
    reg check_started = 1'b0;
    reg check_hold, check_empty;
    reg [7:0] check_payload;
    always @(posedge clk) begin
        check_started <= 1'b1;
        check_hold <= !check_cancel && pend_v && !pend_go;
        check_empty <= check_cancel || (pend_go && !check_enqueue);
        check_payload <= {pend_k, pend_a};
    end

    always @* begin
        if (!check_started)
            assume(!rst_n);
        if (check_started) begin
            if (pend_v && !pend_go)
                assert(!tk_timed);
            if (check_hold) begin
                assert(pend_v);
                assert({pend_k, pend_a} == check_payload);
            end
            if (check_empty) begin
                assert(!pend_v);
                assert(!pend_go);
            end
        end
    end
