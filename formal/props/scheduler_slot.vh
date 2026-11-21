            wire eligible_except_pending = eval_en && v &&
                (!se || (state == sv)) && (((flags ^ fv) & fm) == 4'd0) &&
                in_ok && out_ok && call_ok;
            wire executing_dependency = ex_fw && (ex_df < 3) && fm[ex_df];
            always @(posedge clk) if (sched_initialized) begin
                assert(ready[i] == (eligible_except_pending && !executing_dependency));
            end
