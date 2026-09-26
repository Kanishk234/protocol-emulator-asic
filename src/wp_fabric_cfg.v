// Configuration path for the tiny fabric (phase 1 spike, ARCHITECTURE.md §3 to follow).
// FABulous's bit-bang receiver + frame-based configuration FSM (src/fabric_gen, unmodified),
// with one frame-data register per fabric row and one frame-select decoder per column, the way
// FABulous's generated eFPGA_top wires them. All ROWS rows of the macro are written (the edge
// rows have configuration bits too).
//
// Bit-bang protocol (FABulous bitbang.v): a data bit is taken on each rising edge of cfg_clk and
// a control bit on each falling edge; when the last 16 control bits are 0xFAB1 the last 32 data
// bits form a word, and 0xFAB0 ends the session. `active` is high during a session.
`default_nettype none

module wp_fabric_cfg #(
    parameter integer ROWS = 4,
    parameter integer COLS = 3,
    parameter integer FRAME_BITS = 32,
    parameter integer MAX_FRAMES = 20
) (
    input  wire                         clk,
    input  wire                         rst_n,
    input  wire                         cfg_clk,
    input  wire                         cfg_data,
    output wire                         active,
    output wire [FRAME_BITS*ROWS-1:0]   frame_data,
    output wire [MAX_FRAMES*COLS-1:0]   frame_strobe
);
    localparam integer ROW_SEL_W   = 5;
    localparam integer FRAME_SEL_W = 5;

    wire [31:0]             word;
    wire                    word_strobe;
    wire [FRAME_BITS-1:0]   frame_address;
    wire                    long_frame_strobe;
    wire [ROW_SEL_W-1:0]    row_select;

    bitbang u_bitbang (
        .s_clk   (cfg_clk),
        .s_data  (cfg_data),
        .strobe  (word_strobe),
        .data    (word),
        .active  (active),
        .clk     (clk),
        .reset_n (rst_n)
    );

    ConfigFSM #(
        .NumberOfRows   (ROWS),
        .RowSelectWidth (ROW_SEL_W),
        .FrameBitsPerRow(FRAME_BITS),
        .desync_flag    (20)
    ) u_fsm (
        .CLK                    (clk),
        .reset_n                (rst_n),
        .write_data             (word),
        .write_strobe           (word_strobe),
        .fsm_reset              (active),
        .frame_address_register (frame_address),
        .long_frame_strobe      (long_frame_strobe),
        .row_select             (row_select)
    );

    // frame_address bits between the frame strobes and the column select are not used
    wire _unused = &{frame_address[FRAME_BITS-FRAME_SEL_W-1:MAX_FRAMES], 1'b0};

    genvar r, c;
    generate
        for (r = 0; r < ROWS; r = r + 1) begin : g_row
            Frame_Data_Reg #(
                .FrameBitsPerRow(FRAME_BITS),
                .RowSelectWidth (ROW_SEL_W),
                .Row            (r + 1)
            ) u_row (
                .CLK         (clk),
                .FrameData_I (word),
                .FrameData_O (frame_data[r*FRAME_BITS +: FRAME_BITS]),
                .RowSelect   (row_select)
            );
        end
        for (c = 0; c < COLS; c = c + 1) begin : g_col
            Frame_Select #(
                .MaxFramesPerCol (MAX_FRAMES),
                .FrameSelectWidth(FRAME_SEL_W),
                .Col             (c)
            ) u_col (
                .FrameStrobe_I (frame_address[MAX_FRAMES-1:0]),
                .FrameStrobe_O (frame_strobe[c*MAX_FRAMES +: MAX_FRAMES]),
                .FrameSelect   (frame_address[FRAME_BITS-1 -: FRAME_SEL_W]),
                .FrameStrobe   (long_frame_strobe)
            );
        end
    endgenerate
endmodule
