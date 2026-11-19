// Independent list oracle for status retention, output priority and exact loss.
// Inputs are intent boundaries in the seam proof; actual engine wires in the
// integration proof. No oracle value drives the implementation.
reg queue_past = 0;
reg ref_valid;
reg [15:0] ref_data;
reg [15:0] ref_items [0:3];
integer ref_count, ref_offset, qi;
reg ref_load, ref_loss;
reg [1:0] ref_tag;
reg [15:0] ref_output;
wire [15:0] ref_readback = 16'h8000 | ({15'd0,a_in} << 14)
                        | ((tmode != 1) ? 16'h2000 : 16'd0)
                        | ((tmode == 3) ? 16'h1000 : 16'd0)
                        | ({5'd0,lcnt} << 1);
always @* begin
    for(qi=0;qi<4;qi=qi+1) ref_items[qi]=0;
    ref_count=0;
    if(ref_valid) begin ref_items[ref_count]=ref_data; ref_count=ref_count+1; end
    if(live && rb_ev) begin ref_items[ref_count]=ref_readback;ref_count=ref_count+1;end
    if(live && sync_ev) begin ref_items[ref_count]=16'h9001;ref_count=ref_count+1;end
    if(live && ref_ev) begin ref_items[ref_count]=16'hc001;ref_count=ref_count+1;end
    ref_offset=0;ref_load=0;ref_tag=0;ref_output=0;
    if(fr_want && rx_free) begin ref_load=1;ref_tag=fr_tag;ref_output=fr_data;end
    else if(!fr_want && rx_free && ref_count!=0) begin
        ref_load=1;ref_tag=2'd2;ref_output=ref_items[0];ref_offset=1;
    end
    ref_loss=(fr_want && !rx_free) || (ref_count-ref_offset>1);
end
reg saw_pair;
always @(posedge clk) begin
    queue_past <= 1;
    if(!rst_n || restart || !active) begin ref_valid<=0;ref_data<=0;saw_pair<=0;end
    else begin
        ref_valid <= ref_count>ref_offset;
        ref_data <= ref_items[ref_offset];
        if(live && rb_ev && sync_ev && rx_free && !fr_want && !ref_valid) saw_pair<=1;
    end
    if(queue_past && rst_n) begin
        assert(st_v==ref_valid);
        if(ref_valid) assert(st_d==ref_data);
        assert(rx_load==ref_load);
        if(ref_load) begin assert(rx_tag==ref_tag);assert(rx_data==ref_output);end
        assert(ovr_set==ref_loss);
        cover(live && rb_ev && sync_ev && rx_free && !fr_want && !ref_valid && !ovr_set);
`ifdef STATUS_QUEUE_SEAM
        cover(live && rb_ev && sync_ev && ref_ev && ovr_set);
`else
        // The abstract boundary accepts three intents; the actual engine cannot
        // generate this combination. Prove that fact instead of assuming it.
        assert(!(rb_ev && sync_ev && ref_ev));
`endif
        cover(saw_pair && ref_valid && rx_free && !fr_want && rx_load);
        cover(fr_want && rx_free && ref_valid && rx_load);
    end
end
