// WARP shell: host interface, checked loader, run control and host byte channels
// (ARCHITECTURE.md §2–5, §7.3).
//
// The host talks SPI (wp_spi_target). Each transaction's first byte is the opcode; STATUS is
// shifted out during it. Bitstream words from LOAD_DATA are forwarded to the configuration FSM
// as they arrive (cfg_word/cfg_strobe) and CRC-checked at LOAD_END; a load that fails a check
// ends in ERROR and never reaches RUNNING (F2). `running` gates everything the fabric can drive
// (the pin gate itself is in tt_um_warp).
//
// ERROR_CODE: a load error (0x10–0x13) always replaces the code; a bad command (0x01) is only
// recorded when no error is pending, so the cause of an ERROR state is not overwritten.
`default_nettype none

module wp_shell #(
    parameter [15:0] ARCH_VERSION = 16'h0001,
    parameter integer FIFO_AW = 1            // 2 entries per channel direction
) (
    input  wire        clk,
    input  wire        rst_n,
    // host pins (raw)
    input  wire        host_cs_n,
    input  wire        host_sck,
    input  wire        host_mosi,
    output wire        host_miso,
    output reg         host_irq,
    // configuration path (FABulous ConfigFSM)
    output reg  [31:0] cfg_word,
    output reg         cfg_strobe,
    output reg         cfg_restart,
    // run control
    output wire        running,
    output reg         user_reset,           // 1 = hold the user design in reset
    // host channels, fabric side (ignored unless running)
    output wire [7:0]  h_wdata,
    output wire        h_wlast,
    output wire        h_wvalid,
    input  wire        h_wready,
    input  wire [7:0]  h_rdata,
    input  wire        h_rvalid,
    output wire        h_rready,
    input  wire [7:0]  h_status,
    input  wire        h_attention
);
    // ---- constants (ARCHITECTURE.md §2.3, §2.4)
    localparam [7:0] OP_READ_ID = 8'h01, OP_READ_STATUS = 8'h02,
                     OP_LOAD_BEGIN = 8'h10, OP_LOAD_DATA = 8'h11, OP_LOAD_END = 8'h12,
                     OP_RUN = 8'h20, OP_STOP = 8'h21, OP_USER_RESET = 8'h22,
                     OP_CH_WRITE = 8'h30, OP_CH_READ = 8'h31, OP_USER_STATUS = 8'h32;
    localparam [2:0] S_UNCONFIGURED = 3'd0, S_LOADING = 3'd1, S_LOADED = 3'd2,
                     S_RUNNING = 3'd3, S_ERROR = 3'd4;
    localparam [7:0] E_NONE = 8'h00, E_BAD_COMMAND = 8'h01, E_WRONG_ARCH = 8'h10,
                     E_LENGTH = 8'h11, E_CRC = 8'h12, E_FORMAT = 8'h13;
    localparam [31:0] SYNC_WORD = 32'hFAB0_FAB1;

    // ---- host SPI
    wire cs_n_s, sck_s, mosi_s;
    wp_sync #(.WIDTH(3), .RESET_VAL(3'b100)) u_sync (
        .clk(clk), .rst_n(rst_n),
        .d({host_cs_n, host_sck, host_mosi}), .q({cs_n_s, sck_s, mosi_s})
    );

    wire       start, rx_valid;
    wire [7:0] rx_byte;
    reg  [7:0] tx_byte;
    wp_spi_target u_spi (
        .clk(clk), .rst_n(rst_n),
        .cs_n(cs_n_s), .sck(sck_s), .mosi(mosi_s),
        .tx_byte(tx_byte), .miso(host_miso),
        .start(start), .rx_valid(rx_valid), .rx_byte(rx_byte)
    );

    // ---- state
    reg [2:0]  state;
    reg [7:0]  err;
    reg        ovf;
    reg [7:0]  cmd;
    reg        cmd_ok;       // opcode accepted in this state: act on its payload
    reg [2:0]  bcnt;         // bytes completed in this transaction (saturates at 7)
    reg [23:0] pay;          // the last three payload bytes
    reg [1:0]  wbyte;        // LOAD_DATA: byte within the current word
    reg [15:0] len;
    reg [16:0] wcount;       // words received (saturates)
    reg        fmt_err;
    reg        rd_hit;       // CH_READ: a byte was waiting when the opcode arrived

    assign running = (state == S_RUNNING);

    // ---- CRC over LOAD_DATA words
    wire [31:0] word = {pay, rx_byte};
    wire        word_done = rx_valid && !start && cmd_ok && (bcnt != 3'd0) && (cmd == OP_LOAD_DATA)
                            && (wbyte == 2'd3);
    reg         crc_clear;
    wire [31:0] crc;
    wire        crc_busy;
    wp_crc32 u_crc (
        .clk(clk), .rst_n(rst_n), .clear(crc_clear),
        .word_valid(word_done), .word(word), .crc(crc), .busy(crc_busy)
    );

    // ---- host channels (cleared whenever the design is not running)
    wire       tx_full, tx_empty, rx_full, rx_empty;
    wire [8:0] tx_dout;
    wire [7:0] rx_dout;
    wire       ch_push = rx_valid && cmd_ok && (cmd == OP_CH_WRITE) && (bcnt == 3'd2);
    wire       ch_pop  = rx_valid && cmd_ok && (cmd == OP_CH_READ) && (bcnt == 3'd1) && rd_hit;

    wp_fifo #(.WIDTH(9), .AW(FIFO_AW)) u_to_design (
        .clk(clk), .rst_n(rst_n), .clear(!running),
        .push(ch_push), .din({pay[0], rx_byte}),
        .pop(h_wvalid && h_wready), .dout(tx_dout), .full(tx_full), .empty(tx_empty)
    );
    wp_fifo #(.WIDTH(8), .AW(FIFO_AW)) u_to_host (
        .clk(clk), .rst_n(rst_n), .clear(!running),
        .push(h_rvalid && h_rready), .din(h_rdata),
        .pop(ch_pop), .dout(rx_dout), .full(rx_full), .empty(rx_empty)
    );

    assign h_wdata  = tx_dout[7:0];
    assign h_wlast  = tx_dout[8];
    assign h_wvalid = running && !tx_empty;
    assign h_rready = running && !rx_full;

    wire       attention = running && h_attention;
    wire [7:0] status = {state, !rx_empty, running && !tx_full, ovf, attention, err != E_NONE};

    // ---- response byte (for the byte after `bcnt` completed bytes)
    always @(*) begin
        tx_byte = 8'h00;
        if (bcnt == 3'd0) begin
            tx_byte = status;
        end else if (cmd_ok) begin
            case (cmd)
                OP_READ_ID:
                    case (bcnt)
                        3'd1: tx_byte = 8'h57;
                        3'd2: tx_byte = 8'h50;
                        3'd3: tx_byte = ARCH_VERSION[15:8];
                        3'd4: tx_byte = ARCH_VERSION[7:0];
                        default: tx_byte = 8'h00;
                    endcase
                OP_READ_STATUS:
                    case (bcnt)
                        3'd1: tx_byte = status;
                        3'd2: tx_byte = err;
                        default: tx_byte = 8'h00;
                    endcase
                OP_CH_READ:     if (bcnt == 3'd1 && rd_hit) tx_byte = rx_dout;
                OP_USER_STATUS: if (bcnt == 3'd1 && running) tx_byte = h_status;
                default:        tx_byte = 8'h00;
            endcase
        end
    end

    // ---- opcode admission (ARCHITECTURE.md §2.3 "allowed in state")
    reg allowed;
    always @(*) begin
        case (rx_byte)
            OP_READ_ID, OP_READ_STATUS:  allowed = 1'b1;
            OP_LOAD_BEGIN:               allowed = (state != S_RUNNING);
            OP_LOAD_DATA, OP_LOAD_END:   allowed = (state == S_LOADING);
            OP_RUN:                      allowed = (state == S_LOADED);
            OP_STOP, OP_USER_RESET,
            OP_CH_WRITE, OP_CH_READ,
            OP_USER_STATUS:              allowed = (state == S_RUNNING);
            default:                     allowed = 1'b0;
        endcase
    end

    // ---- main controller
    always @(posedge clk) begin
        if (!rst_n) begin
            state       <= S_UNCONFIGURED;
            err         <= E_NONE;
            ovf         <= 1'b0;
            cmd         <= 8'h00;
            cmd_ok      <= 1'b0;
            bcnt        <= 3'd0;
            pay         <= 24'd0;
            wbyte       <= 2'd0;
            len         <= 16'd0;
            wcount      <= 17'd0;
            fmt_err     <= 1'b0;
            rd_hit      <= 1'b0;
            cfg_word    <= 32'd0;
            cfg_strobe  <= 1'b0;
            cfg_restart <= 1'b0;
            crc_clear   <= 1'b0;
            user_reset  <= 1'b1;
            host_irq    <= 1'b0;
        end else begin
            cfg_strobe  <= 1'b0;
            cfg_restart <= 1'b0;
            crc_clear   <= 1'b0;

            if (start) begin
                bcnt   <= 3'd0;
                cmd_ok <= 1'b0;
                wbyte  <= 2'd0;
            end else if (rx_valid) begin
                pay <= {pay[15:0], rx_byte};
                if (bcnt != 3'd7)
                    bcnt <= bcnt + 3'd1;

                if (bcnt == 3'd0) begin
                    // opcode
                    cmd    <= rx_byte;
                    cmd_ok <= allowed;
                    rd_hit <= !rx_empty;
                    if (!allowed) begin
                        if (err == E_NONE)
                            err <= E_BAD_COMMAND;
                    end else begin
                        case (rx_byte)
                            OP_RUN:  state <= S_RUNNING;
                            OP_STOP: state <= S_LOADED;
                            default: ;
                        endcase
                    end
                end else if (cmd_ok) begin
                    case (cmd)
                        OP_READ_STATUS:
                            if (bcnt == 3'd2) begin
                                err <= E_NONE;
                                ovf <= 1'b0;
                            end
                        OP_LOAD_BEGIN:
                            if (bcnt == 3'd4) begin
                                if (pay[23:8] == ARCH_VERSION) begin
                                    state       <= S_LOADING;
                                    len         <= {pay[7:0], rx_byte};
                                    wcount      <= 17'd0;
                                    fmt_err     <= 1'b0;
                                    crc_clear   <= 1'b1;
                                    cfg_restart <= 1'b1;
                                end else begin
                                    state <= S_ERROR;
                                    err   <= E_WRONG_ARCH;
                                end
                            end
                        OP_LOAD_DATA: begin
                            wbyte <= wbyte + 2'd1;
                            if (wbyte == 2'd3) begin
                                if (wcount != 17'h1FFFF)
                                    wcount <= wcount + 17'd1;
                                if (wcount == 17'd0 && word != SYNC_WORD)
                                    fmt_err <= 1'b1;
                                if (!fmt_err && !(wcount == 17'd0 && word != SYNC_WORD)
                                    && wcount < {1'b0, len}) begin
                                    cfg_word   <= word;
                                    cfg_strobe <= 1'b1;
                                end
                            end
                        end
                        OP_LOAD_END:
                            if (bcnt == 3'd4) begin
                                // an empty load has no sync word (BUGS #12)
                                if (fmt_err || wcount == 17'd0) begin
                                    state <= S_ERROR;
                                    err   <= E_FORMAT;
                                end else if (wcount != {1'b0, len}) begin
                                    state <= S_ERROR;
                                    err   <= E_LENGTH;
                                end else if (word != crc || crc_busy) begin
                                    state <= S_ERROR;
                                    err   <= E_CRC;
                                end else begin
                                    state <= S_LOADED;
                                end
                            end
                        OP_CH_WRITE:
                            if (bcnt == 3'd2 && tx_full)
                                ovf <= 1'b1;
                        default: ;
                    endcase
                end
            end

            // user reset: held unless running, plus one cycle on USER_RESET
            user_reset <= !running
                       || (rx_valid && !start && bcnt == 3'd0 && allowed && rx_byte == OP_USER_RESET);
            host_irq   <= !rx_empty || attention || (state == S_ERROR);
        end
    end

`ifdef FORMAL_F2
    // ---- F2 (VERIFICATION.md): a load that fails a check never reaches RUNNING.
    // Shadow loader: its own byte-wise CRC-32, word count, LENGTH and sync check, updated from
    // the decoded bytes. formal/f2_loader.sby cuts the SPI receiver so the bytes are arbitrary.
    function [31:0] f_crc_byte(input [31:0] c, input [7:0] b);
        integer k;
        reg [31:0] x;
        begin
            x = c ^ {24'd0, b};
            for (k = 0; k < 8; k = k + 1)
                x = x[0] ? ((x >> 1) ^ 32'hEDB8_8320) : (x >> 1);
            f_crc_byte = x;
        end
    endfunction

    reg        f_past_valid = 1'b0;
    reg [31:0] f_crc;
    reg [16:0] f_count;
    reg [15:0] f_len;
    reg        f_sync_ok;
    always @(posedge clk) f_past_valid <= 1'b1;
    always @(*) if (!f_past_valid) assume (!rst_n);
    // the real SPI receiver delivers a byte at most every 64 clk; the CRC needs 32 per word
    always @(*) assume (!(rx_valid && crc_busy));

    wire f_begin_ok = rx_valid && !start && cmd_ok && cmd == OP_LOAD_BEGIN && bcnt == 3'd4
                      && pay[23:8] == ARCH_VERSION;
    wire f_end_ok   = rx_valid && !start && cmd_ok && cmd == OP_LOAD_END && bcnt == 3'd4
                      && word == ~f_crc && f_count == {1'b0, f_len} && f_count != 17'd0
                      && f_sync_ok;

    always @(posedge clk) begin
        if (f_begin_ok) begin
            f_crc     <= 32'hFFFF_FFFF;
            f_count   <= 17'd0;
            f_len     <= {pay[7:0], rx_byte};
            f_sync_ok <= 1'b1;
        end else if (!start && word_done) begin
            f_crc <= f_crc_byte(f_crc_byte(f_crc_byte(f_crc_byte(f_crc,
                     word[31:24]), word[23:16]), word[15:8]), word[7:0]);
            if (f_count != 17'h1FFFF) f_count <= f_count + 17'd1;
            if (f_count == 17'd0 && word != SYNC_WORD) f_sync_ok <= 1'b0;
        end
    end

    always @(posedge clk) begin
        if (f_past_valid && $past(rst_n) && rst_n) begin
            // LOADED is entered only by STOP or by a LOAD_END that passes the shadow checks
            if (state == S_LOADED && $past(state) != S_LOADED)
                assert ($past(state) == S_RUNNING || ($past(state) == S_LOADING && $past(f_end_ok)));
            // RUNNING is entered only from LOADED
            if (state == S_RUNNING && $past(state) != S_RUNNING)
                assert ($past(state) == S_LOADED);
            // LOADING is entered only by an accepted LOAD_BEGIN
            if (state == S_LOADING && $past(state) != S_LOADING)
                assert ($past(f_begin_ok));
        end
        if (f_past_valid && !$past(rst_n))
            assert (state == S_UNCONFIGURED);
    end

    // reachability: a complete load followed by RUN
    always @(posedge clk) cover (f_past_valid && rst_n && state == S_RUNNING);
`endif
endmodule
