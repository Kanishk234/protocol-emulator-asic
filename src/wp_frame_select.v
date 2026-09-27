// Frame-strobe decoder for one fabric column (replaces FABulous's Frame_Select, D-025).
// FABulous's version takes the ConfigFSM's one-hot frame bits and gates them per column, so the
// shell has to route all MAX_FRAMES one-hot bits to every column: on the 6x4 chip those wires run
// the whole width of the fabric on the only horizontal routing layer (Metal3). Here the column
// gets the frame *number* and decodes it locally: the shared wires are frame_idx, col and strobe
// (11 instead of 26), and the per-column gates sit under their column.
// Same function for every bitstream the compile flow writes (one frame per header).
`default_nettype none

module wp_frame_select #(
    parameter integer MAX_FRAMES = 20,
    parameter integer IDX_W      = 5,
    parameter integer COL_W      = 5,
    parameter integer COL        = 0
) (
    input  wire [IDX_W-1:0]      frame_idx,
    input  wire [COL_W-1:0]      col,
    input  wire                  strobe,
    output wire [MAX_FRAMES-1:0] frame_strobe
);
    wire here = strobe && (col == COL[COL_W-1:0]);
    genvar i;
    generate
        for (i = 0; i < MAX_FRAMES; i = i + 1) begin : g_frame
            assign frame_strobe[i] = here && (frame_idx == i[IDX_W-1:0]);
        end
    endgenerate
endmodule
