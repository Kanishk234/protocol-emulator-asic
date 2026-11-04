// Experimental masked-word OR reduction: protect shared mask gate inputs.
// Data inputs and final reduction gates are not claimed to be protected.
`default_nettype none
module trw_guarded_reduce #(parameter WIDTH=33, ROWS=12, GROUP=6)(
 input wire [ROWS-1:0] mask,
 input wire [ROWS*WIDTH-1:0] words,
 output wire [WIDTH-1:0] value
);
`ifdef SYNTHESIS
 localparam PAIRS=(ROWS+1)/2;
 wire [PAIRS*WIDTH-1:0] inverted_terms;
 genvar pair_index, group_index, bit_index;
 generate for (pair_index=0; pair_index<PAIRS; pair_index=pair_index+1) begin : g_pair
  for (group_index=0; group_index<(WIDTH+GROUP-1)/GROUP; group_index=group_index+1) begin : g_group
   (* keep = 1 *) wire trw_guard_mask0_node;
   (* keep = 1 *) wire trw_guard_mask1_node;
   (* keep = 1 *) sg13cmos5l_buf_2 mask0_driver (.A(mask[2*pair_index]), .X(trw_guard_mask0_node));
   (* keep = 1 *) sg13cmos5l_antennanp trw_guard_mask0_diode (.A(trw_guard_mask0_node));
   if (2*pair_index+1<ROWS) begin : g_second
    (* keep = 1 *) sg13cmos5l_buf_2 mask1_driver (.A(mask[2*pair_index+1]), .X(trw_guard_mask1_node));
    (* keep = 1 *) sg13cmos5l_antennanp trw_guard_mask1_diode (.A(trw_guard_mask1_node));
   end else begin : g_last
    assign trw_guard_mask1_node=1'b0;
   end
   for (bit_index=0; bit_index<GROUP; bit_index=bit_index+1) begin : g_bit
    if (group_index*GROUP+bit_index<WIDTH) begin : g_used
     localparam COL=group_index*GROUP+bit_index;
     wire second_word;
     if (2*pair_index+1<ROWS) begin : g_second_word
      assign second_word=words[(2*pair_index+1)*WIDTH+COL];
     end else begin : g_zero_word
      assign second_word=1'b0;
     end
     (* keep = 1 *) sg13cmos5l_a22oi_1 trw_guard_sink (
      .A1(trw_guard_mask0_node), .A2(words[2*pair_index*WIDTH+COL]),
      .B1(trw_guard_mask1_node), .B2(second_word), .Y(inverted_terms[pair_index*WIDTH+COL]));
    end
   end
  end
 end endgenerate
 reg [WIDTH-1:0] reduced;
 integer rr;
 always @* begin
  reduced={WIDTH{1'b1}};
  for (rr=0; rr<PAIRS; rr=rr+1) reduced=reduced & inverted_terms[rr*WIDTH +: WIDTH];
 end
 assign value=~reduced;
`else
 reg [WIDTH-1:0] reduced;
 integer rr;
 always @* begin
  reduced={WIDTH{1'b0}};
  for (rr=0; rr<ROWS; rr=rr+1)
   reduced=reduced | ({WIDTH{mask[rr]}} & words[rr*WIDTH +: WIDTH]);
 end
 assign value=reduced;
`endif
endmodule
