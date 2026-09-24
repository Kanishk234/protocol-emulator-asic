// R3 risk spike (branch spike/r3-sram only; never merged): the IHP 512x16 SRAM macro through the
// Tiny Tapeout cmos5l flow, tested from the pins.
//
// Two ways in, both through trw_sram:
//   - Direct word access: byte registers loaded from uio_in, then a write or read strobe.
//   - BIST: 18 passes, each writes all 512 words and reads them back and compares.
//       passes 0-15: word a holds 1 << ((a + pass) mod 16), so every word sees every
//                    single-bit value (walking ones) and neighbours differ;
//       pass 16:     {a[6:0], a}: every word unique, catches address aliasing;
//       pass 17:     the complement of pass 16 (every bit toggles; left in the memory).
//
// Pins (strobes are synchronised, 2 flops, and act on their rising edge; hold them >= 3 clocks):
//   ui[0] START      begin the BIST (ignored while busy)
//   ui[2] REG_WR     load uio_in into the byte register REGSEL = ui[4:3]:
//                    0 ADDR[7:0], 1 ADDR[8], 2 WDATA[7:0], 3 WDATA[15:8]
//   ui[5] MEM_WR     SRAM[ADDR] := WDATA          (ignored while the BIST is busy)
//   ui[6] MEM_RD     RDATA := SRAM[ADDR]          (ignored while the BIST is busy)
//   {ui[7], ui[1]}   uo_out select: 0 STATUS {busy, done, fail, pass[4:0]}, 1 ERRCNT (saturating),
//                    2 RDATA[7:0], 3 RDATA[15:8]
//   uio              inputs only (uio_oe = 0)
`default_nettype none

module tt_um_tripwire (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);
    localparam [4:0] LAST_PASS = 5'd17;

    // ---- strobes: synchroniser + rising-edge detect
    reg [2:0] s_start, s_regwr, s_memwr, s_memrd;
    always @(posedge clk) begin
        if (!rst_n) begin
            s_start <= 3'd0;
            s_regwr <= 3'd0;
            s_memwr <= 3'd0;
            s_memrd <= 3'd0;
        end else begin
            s_start <= {s_start[1:0], ui_in[0]};
            s_regwr <= {s_regwr[1:0], ui_in[2]};
            s_memwr <= {s_memwr[1:0], ui_in[5]};
            s_memrd <= {s_memrd[1:0], ui_in[6]};
        end
    end
    wire start_edge = s_start[1] && !s_start[2];
    wire regwr_edge = s_regwr[1] && !s_regwr[2];
    wire memwr_edge = s_memwr[1] && !s_memwr[2];
    wire memrd_edge = s_memrd[1] && !s_memrd[2];

    // ---- byte registers
    reg [8:0]  addr_reg;
    reg [15:0] wdata_reg;
    always @(posedge clk) begin
        if (!rst_n) begin
            addr_reg  <= 9'd0;
            wdata_reg <= 16'd0;
        end else if (regwr_edge) begin
            case (ui_in[4:3])
                2'd0:    addr_reg[7:0]    <= uio_in;
                2'd1:    addr_reg[8]      <= uio_in[0];
                2'd2:    wdata_reg[7:0]   <= uio_in;
                default: wdata_reg[15:8]  <= uio_in;
            endcase
        end
    end

    // ---- BIST patterns
    function [15:0] pattern;
        input [4:0] p;
        input [8:0] a;
        begin
            if (!p[4])
                pattern = 16'h0001 << (a[3:0] + p[3:0]);    // 4-bit sum: mod 16
            else if (!p[0])
                pattern = {a[6:0], a};
            else
                pattern = ~{a[6:0], a};
        end
    endfunction

    // ---- BIST sequencer: phase 0 writes a = 0..511, phase 1 reads them, phase 2 drains the last
    // compare. A read issued in clock n is compared in clock n+1 (the macro's registered output).
    localparam [1:0] PH_WRITE = 2'd0, PH_READ = 2'd1, PH_DRAIN = 2'd2;
    reg        busy, done, fail;
    reg [1:0]  phase;
    reg [4:0]  pass;
    reg [8:0]  a;
    reg        cmp_v;
    reg [4:0]  cmp_pass;
    reg [8:0]  cmp_a;
    reg [7:0]  errcnt;
    reg        rd_pending;
    reg [15:0] rdata_reg;

    wire [15:0] sram_rdata;
    wire        b_access = busy && (phase != PH_DRAIN);
    wire        sram_en    = b_access || (!busy && (memwr_edge || memrd_edge));
    wire        sram_we    = busy ? (phase == PH_WRITE) : memwr_edge;
    wire [8:0]  sram_addr  = busy ? a : addr_reg;
    wire [15:0] sram_wdata = busy ? pattern(pass, a) : wdata_reg;

    trw_sram u_sram (
        .clk (clk), .rst_n (rst_n), .en (sram_en), .we (sram_we),
        .addr (sram_addr), .wdata (sram_wdata), .rdata (sram_rdata)
    );

    wire mismatch = cmp_v && (sram_rdata != pattern(cmp_pass, cmp_a));

    always @(posedge clk) begin
        if (!rst_n) begin
            busy       <= 1'b0;
            done       <= 1'b0;
            fail       <= 1'b0;
            phase      <= PH_WRITE;
            pass       <= 5'd0;
            a          <= 9'd0;
            cmp_v      <= 1'b0;
            cmp_pass   <= 5'd0;
            cmp_a      <= 9'd0;
            errcnt     <= 8'd0;
            rd_pending <= 1'b0;
            rdata_reg  <= 16'd0;
        end else begin
            // compare stage
            cmp_v    <= busy && (phase == PH_READ);
            cmp_pass <= pass;
            cmp_a    <= a;
            if (mismatch) begin
                fail <= 1'b1;
                if (errcnt != 8'hFF)
                    errcnt <= errcnt + 8'd1;
            end

            // sequencer
            if (!busy) begin
                if (start_edge) begin
                    busy   <= 1'b1;
                    done   <= 1'b0;
                    fail   <= 1'b0;
                    errcnt <= 8'd0;
                    phase  <= PH_WRITE;
                    pass   <= 5'd0;
                    a      <= 9'd0;
                end
            end else begin
                case (phase)
                    PH_WRITE: begin
                        a <= a + 9'd1;
                        if (a == 9'd511)
                            phase <= PH_READ;
                    end
                    PH_READ: begin
                        a <= a + 9'd1;
                        if (a == 9'd511) begin
                            if (pass == LAST_PASS) begin
                                phase <= PH_DRAIN;
                            end else begin
                                pass  <= pass + 5'd1;
                                phase <= PH_WRITE;
                            end
                        end
                    end
                    default: begin                      // PH_DRAIN: the last compare is this clock
                        busy  <= 1'b0;
                        done  <= 1'b1;
                        phase <= PH_WRITE;
                    end
                endcase
            end

            // direct read: capture one clock after the access
            rd_pending <= !busy && memrd_edge && !memwr_edge;
            if (rd_pending)
                rdata_reg <= sram_rdata;
        end
    end

    // ---- pins
    reg [7:0] uo_mux;
    always @* begin
        case ({ui_in[7], ui_in[1]})
            2'd0:    uo_mux = {busy, done, fail, pass};
            2'd1:    uo_mux = errcnt;
            2'd2:    uo_mux = rdata_reg[7:0];
            default: uo_mux = rdata_reg[15:8];
        endcase
    end
    assign uo_out  = uo_mux;
    assign uio_out = 8'h00;
    assign uio_oe  = 8'h00;

    wire _unused = &{1'b0, ena};
endmodule
