// Configuration path (ARCHITECTURE.md §3): FABulous's frame-based configuration FSM and frame-data
// registers (src/fabric_gen, unmodified), one register per fabric row, as FABulous's generated
// eFPGA_top wires them; all ROWS rows of the macro are written (the edge rows have configuration
// bits too). Frame strobes: the one-hot frame bits of the frame header are encoded to a frame
// number here and each column decodes it itself (wp_frame_select, D-025), so the wires shared by
// all columns are 11 instead of MAX_FRAMES + 6.
//
// Words come from the shell's checked loader (wp_shell): `word` is valid with a one-cycle
// `word_strobe`; a one-cycle `restart` at LOAD_BEGIN returns the FSM to waiting for the sync word.
`default_nettype none

module wp_fabric_cfg #(
    parameter integer ROWS = 4,
    parameter integer COLS = 3,
    parameter integer FRAME_BITS = 32,
    parameter integer MAX_FRAMES = 20
) (
    input  wire                         clk,
    input  wire                         rst_n,
    input  wire [31:0]                  word,
    input  wire                         word_strobe,
    input  wire                         restart,
    output wire [FRAME_BITS*ROWS-1:0]   frame_data,
    output wire [MAX_FRAMES*COLS-1:0]   frame_strobe
);
    localparam integer ROW_SEL_W   = 5;
    localparam integer FRAME_SEL_W = 5;

    wire [FRAME_BITS-1:0]   frame_address;
    wire                    long_frame_strobe;
    wire [ROW_SEL_W-1:0]    row_select;

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
        .fsm_reset              (restart),
        .frame_address_register (frame_address),
        .long_frame_strobe      (long_frame_strobe),
        .row_select             (row_select)
    );

    // frame_address bits between the frame strobes and the column select are not used
    wire _unused = &{frame_address[FRAME_BITS-FRAME_SEL_W-1:MAX_FRAMES], 1'b0};

    // one-hot frame bits -> frame number (the lowest set bit; the compile flow sets exactly one)
    reg [FRAME_SEL_W-1:0] frame_idx;
    integer i;
    always @(*) begin
        frame_idx = {FRAME_SEL_W{1'b0}};
        for (i = MAX_FRAMES - 1; i >= 0; i = i - 1)
            if (frame_address[i])
                frame_idx = i[FRAME_SEL_W-1:0];
    end

    genvar r, c;
    generate
        for (r = 0; r < ROWS; r = r + 1) begin : g_row
            // the row number sized to the parameter's width (a bare genvar expression is 32 bits)
            localparam integer         ROW_I = r + 1;
            localparam [ROW_SEL_W-1:0] ROW   = ROW_I[ROW_SEL_W-1:0];
            Frame_Data_Reg #(
                .FrameBitsPerRow(FRAME_BITS),
                .RowSelectWidth (ROW_SEL_W),
                .Row            (ROW)
            ) u_row (
                .CLK         (clk),
                .FrameData_I (word),
                .FrameData_O (frame_data[r*FRAME_BITS +: FRAME_BITS]),
                .RowSelect   (row_select)
            );
        end
        for (c = 0; c < COLS; c = c + 1) begin : g_col
            wp_frame_select #(
                .MAX_FRAMES(MAX_FRAMES),
                .IDX_W     (FRAME_SEL_W),
                .COL_W     (FRAME_SEL_W),
                .COL       (c)
            ) u_col (
                .frame_idx    (frame_idx),
                .col          (frame_address[FRAME_BITS-1 -: FRAME_SEL_W]),
                .strobe       (long_frame_strobe),
                .frame_strobe (frame_strobe[c*MAX_FRAMES +: MAX_FRAMES])
            );
        end
    endgenerate
endmodule
