module status_queue_harness(input wire clk);
    (* anyseq *) reg rst_n, restart, active, live, rx_free;
    (* anyseq *) reg fr_want, rb_ev, sync_ev, ref_ev, a_in;
    (* anyseq *) reg [1:0] fr_tag,tmode;
    (* anyseq *) reg [15:0] fr_data;
    (* anyseq *) reg [10:0] lcnt;
    reg past_valid=0;
    always @(posedge clk) begin
        past_valid<=1;
        if(!past_valid) assume(!rst_n);else assume(rst_n);
    end
    status_queue_native queue (
        .clk(clk),.rst_n(rst_n),.restart(restart),.active(active),.live(live),.rx_free(rx_free),
        .fr_want(fr_want),.rb_ev(rb_ev),.sync_ev(sync_ev),.ref_ev(ref_ev),.a_in(a_in),
        .fr_tag(fr_tag),.tmode(tmode),.fr_data(fr_data),.lcnt(lcnt)
    );
endmodule
