`default_nettype none
module trw_protected_receiver #(parameter WIDTH=1)(
 input wire [WIDTH-1:0] data, output wire [WIDTH-1:0] value);
`ifdef SYNTHESIS
 genvar bit_index;
 generate for(bit_index=0;bit_index<WIDTH;bit_index=bit_index+1) begin : g_bit
  (* keep=1 *) wire trw_receiver_node;
  (* keep=1 *) sg13cmos5l_buf_2 receiver_driver(.A(data[bit_index]),.X(trw_receiver_node));
  (* keep=1 *) sg13cmos5l_antennanp trw_receiver_diode(.A(trw_receiver_node));
  (* keep=1 *) sg13cmos5l_buf_2 trw_receiver_sink(.A(trw_receiver_node),.X(value[bit_index]));
 end endgenerate
`else
 assign value=data;
`endif
endmodule
