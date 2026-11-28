    // Check the pending record across arbitrary command histories.
    wire check_enqueue = tk_timed && !tk_now;
    wire check_cancel = !rst_n || restart;
    reg check_started = 1'b0;
    reg check_hold, check_empty;
    reg [7:0] check_payload;
    reg [3:0] check_dispatch;
    reg [4:0] check_rx_pin;
    reg check_level, check_oe;
    reg check_started_burst, check_cancelled;
    reg check_pad_oe, check_pad_level;
    reg check_pad_level_valid;
    reg check_idle_after_edge;
    always @(posedge clk) begin
        check_started <= 1'b1;
        check_hold <= !check_cancel && pend_v && !pend_go;
        check_empty <= check_cancel || (pend_go && !check_enqueue);
        check_payload <= {pend_k, pend_a};
        check_started_burst <= !check_cancel && ((pend_go && pend_k == K_START) ||
                               (tk_now && (h_shift || h_clk)));
        check_cancelled <= check_cancel;
        check_pad_oe <= check_cancel || (due_oe_v ? due_oe : oe);
        check_pad_level_valid <= !check_cancel && due_lvl_v && !d_hi;
        check_pad_level <= due_lvl ^ idle;
        check_idle_after_edge <= idle_next;
        check_dispatch <= 4'b0000;
        if (!check_cancel) begin
            if (pend_go) begin
                case (pend_k)
                    K_LVL: begin check_dispatch[3] <= 1'b1; check_level <= pend_a[0]; end
                    K_OE: begin check_dispatch[2] <= 1'b1; check_oe <= pend_a[0]; end
                    K_RXS: begin check_dispatch[1] <= 1'b1; check_rx_pin <= pend_a; end
                    K_SMP: check_dispatch[0] <= 1'b1;
                    default: begin end
                endcase
            end
            // A same-edge immediate command of the same type wins.
            if (tk_now) begin
                if (h_lvl) begin check_dispatch[3] <= 1'b1; check_level <= h_v; end
                if (c_oe) begin check_dispatch[2] <= 1'b1; check_oe <= h_v; end
                if (h_rxs) begin check_dispatch[1] <= 1'b1; check_rx_pin <= arg[4:0]; end
                if (c_smp) check_dispatch[0] <= 1'b1;
            end
        end
    end

    always @* begin
        if (!check_started)
            assume(!rst_n);
        if (check_started) begin
            if (USE_LEVEL_CACHE != 0)
                assert(lvl == ((lvx && !(car_out_on && cph)) ^ check_idle_after_edge));
            else
                assert(lvl == ((lvx && !(car_out_on && cph)) ^ idle));
            assert(oe == check_pad_oe);
            if (check_pad_level_valid) begin
                assert(lvx == check_pad_level);
                assert(!echo);
            end
            if (check_started_burst) assert(p_act);
            if (check_cancelled) assert(!p_act);
            if (pend_v && pend_k == K_START && pend_go)
                assert(!check_enqueue);
            assert({due_lvl_v, due_oe_v, rxset, smp} == check_dispatch);
            if (due_lvl_v) assert(due_lvl == check_level);
            if (due_oe_v) assert(due_oe == check_oe);
            if (rxset) assert(rxset_n == check_rx_pin);
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
