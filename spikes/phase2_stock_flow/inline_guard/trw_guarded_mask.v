`default_nettype none
module trw_guarded_mask #(parameter WIDTH=53, FIRST=20, LAST=WIDTH-1, GROUP=6, ENABLE=1)(
 input wire mask,input wire [WIDTH-1:0] data,output wire [WIDTH-1:0] value);
`ifdef SYNTHESIS
 generate if(ENABLE) begin : g_enabled
  if(FIRST>0) begin : g_low
   assign value[FIRST-1:0]={FIRST{mask}}&data[FIRST-1:0];
  end
  if(LAST+1<WIDTH) begin : g_high
   assign value[WIDTH-1:LAST+1]={WIDTH-LAST-1{mask}}&data[WIDTH-1:LAST+1];
  end
  genvar gi,bi;
  for(gi=0;gi<(LAST-FIRST+GROUP)/GROUP;gi=gi+1) begin : g_group
   (* keep=1 *) wire trw_guard_mask_node;
   (* keep=1 *) sg13cmos5l_buf_2 mask_driver(.A(mask),.X(trw_guard_mask_node));
   (* keep=1 *) sg13cmos5l_antennanp trw_guard_mask_diode(.A(trw_guard_mask_node));
   for(bi=0;bi<GROUP;bi=bi+1) begin : g_bit
    if(FIRST+gi*GROUP+bi<=LAST) begin : g_used
     wire inverted;
     (* keep=1 *) sg13cmos5l_nand2_1 trw_guard_sink(
      .A(trw_guard_mask_node),.B(data[FIRST+gi*GROUP+bi]),.Y(inverted));
     assign value[FIRST+gi*GROUP+bi]=~inverted;
    end
   end
  end
 end else begin : g_disabled
  assign value={WIDTH{mask}}&data;
 end endgenerate
`else
 assign value={WIDTH{mask}}&data;
`endif
endmodule
