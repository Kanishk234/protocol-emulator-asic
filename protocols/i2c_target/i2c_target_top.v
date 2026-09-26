// I2C target user design (provisional user-design interface, DECISIONS D-014).
//
// Bus:   open drain. sda_oe = 1 pulls SDA low (ACK, data 0); SCL is only read (no stretching).
//        Inputs two-flop synchronized; SCL low and high phases must each last >= 4 clocks.
// Map:   NREGS (power of two, <= 16) 8-bit registers.
//        Bus write:  [ADDR+W] [pointer] [data ...]  -> registers from the pointer, auto-increment
//                    (wrapping); the pointer is taken modulo NREGS. Every byte is ACKed.
//        Bus read:   [ADDR+R] -> registers from the pointer, auto-increment, until the
//                    controller NACKs. A repeated START keeps the pointer.
//        Other addresses are not ACKed and the transaction is ignored.
// Host:  command bytes on h_w* (h_wlast ignored):
//          8'b0000_iiii, then a data byte  write register i (host and bus writes in the same
//                                           clock: the bus write wins)
//          8'b1000_iiii                    read register i; reply on h_r*; clears dirty[i]
//        h_status = {dirty[3:0] (registers 0..3 written by the bus since the host last read
//                    them), overrun, cmd_err, 1'b0, addressed}.
`default_nettype none

module i2c_target_top #(
    parameter [6:0] ADDR  = 7'h42,
    parameter       NREGS = 4
) (
    input  wire       clk,
    input  wire       rst_n,
    // pins
    input  wire       sda_i,
    input  wire       scl_i,
    output reg        sda_oe,
    output wire       sda_o,        // always 0 (open drain)
    // host -> design
    input  wire [7:0] h_wdata,
    input  wire       h_wlast,
    input  wire       h_wvalid,
    output wire       h_wready,
    // design -> host
    output reg  [7:0] h_rdata,
    output reg        h_rvalid,
    input  wire       h_rready,
    output wire [7:0] h_status
);
    localparam IW = (NREGS > 1) ? $clog2(NREGS) : 1;

    localparam [2:0] T_IDLE   = 3'd0,  // not addressed: wait for START
                     T_ADDR   = 3'd1,  // receiving the address byte
                     T_ACK    = 3'd2,  // driving ACK for one SCL clock
                     T_WR     = 3'd3,  // receiving a write byte
                     T_RD     = 3'd4,  // sending a read byte
                     T_RD_ACK = 3'd5;  // reading the controller's ACK/NACK

    reg [7:0]    regs [0:NREGS-1];
    reg [NREGS-1:0] dirty;

    reg [2:0]    sda_s, scl_s;
    reg [2:0]    state;
    reg [3:0]    nbit;
    reg [7:0]    shift;
    reg [IW-1:0] ptr;
    reg          rw, first, nack;
    reg          overrun_q, cmd_err_q;
    reg          h_pend;               // a host write command is waiting for its data byte
    reg [IW-1:0] h_idx;

    wire sda = sda_s[1];
    wire scl = scl_s[1];
    wire scl_rise = scl && !scl_s[2];
    wire scl_fall = !scl && scl_s[2];
    wire start    = scl && scl_s[2] && !sda && sda_s[2];
    wire stop     = scl && scl_s[2] && sda && !sda_s[2];

    assign sda_o    = 1'b0;
    assign h_wready = 1'b1;            // commands are handled in one clock

    integer k;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (k = 0; k < NREGS; k = k + 1) regs[k] <= 8'h00;
            dirty     <= {NREGS{1'b0}};
            sda_s     <= 3'b111;
            scl_s     <= 3'b111;
            state     <= T_IDLE;
            nbit      <= 4'd0;
            shift     <= 8'h00;
            ptr       <= {IW{1'b0}};
            rw        <= 1'b0;
            first     <= 1'b0;
            nack      <= 1'b0;
            sda_oe    <= 1'b0;
            overrun_q <= 1'b0;
            cmd_err_q <= 1'b0;
            h_pend    <= 1'b0;
            h_idx     <= {IW{1'b0}};
            h_rdata   <= 8'h00;
            h_rvalid  <= 1'b0;
        end else begin
            sda_s <= {sda_s[1:0], sda_i};
            scl_s <= {scl_s[1:0], scl_i};
            if (h_rvalid && h_rready) h_rvalid <= 1'b0;

            // ---- host commands (a bus write below, in the same clock, takes precedence)
            if (h_wvalid) begin
                if (h_pend) begin
                    regs[h_idx] <= h_wdata;
                    h_pend      <= 1'b0;
                end else if (h_wdata[6:4] != 3'b000 || h_wdata[3:0] >= NREGS) begin
                    cmd_err_q <= 1'b1;
                end else if (h_wdata[7]) begin
                    if (h_rvalid && !h_rready) overrun_q <= 1'b1;
                    else begin
                        h_rdata  <= regs[h_wdata[IW-1:0]];
                        h_rvalid <= 1'b1;
                    end
                    dirty[h_wdata[IW-1:0]] <= 1'b0;
                end else begin
                    h_pend <= 1'b1;
                    h_idx  <= h_wdata[IW-1:0];
                end
            end

            // ---- I2C bus
            if (start) begin
                state  <= T_ADDR;
                nbit   <= 4'd0;
                sda_oe <= 1'b0;
            end else if (stop) begin
                state  <= T_IDLE;
                sda_oe <= 1'b0;
            end else begin
                case (state)
                    T_ADDR, T_WR: begin
                        if (scl_rise) begin
                            shift <= {shift[6:0], sda};
                            nbit  <= nbit + 1'b1;
                        end else if (scl_fall && nbit == 4'd8) begin
                            nbit <= 4'd0;
                            if (state == T_ADDR) begin
                                if (shift[7:1] == ADDR) begin
                                    rw     <= shift[0];
                                    first  <= !shift[0];
                                    sda_oe <= 1'b1;               // ACK
                                    state  <= T_ACK;
                                end else begin
                                    state <= T_IDLE;              // not us
                                end
                            end else begin
                                if (first) begin
                                    ptr   <= shift[IW-1:0];
                                    first <= 1'b0;
                                end else begin
                                    regs[ptr]  <= shift;
                                    dirty[ptr] <= 1'b1;
                                    ptr        <= ptr + 1'b1;
                                end
                                sda_oe <= 1'b1;                   // ACK
                                state  <= T_ACK;
                            end
                        end
                    end

                    T_ACK: if (scl_fall) begin                    // end of the ACK clock
                        if (rw) begin
                            shift  <= regs[ptr];
                            ptr    <= ptr + 1'b1;
                            sda_oe <= !regs[ptr][7];
                            nbit   <= 4'd1;
                            state  <= T_RD;
                        end else begin
                            sda_oe <= 1'b0;
                            state  <= T_WR;
                        end
                    end

                    T_RD: if (scl_fall) begin
                        if (nbit == 4'd8) begin
                            sda_oe <= 1'b0;                       // release for the controller's ACK
                            state  <= T_RD_ACK;
                        end else begin
                            sda_oe <= !shift[3'd7 - nbit[2:0]];
                            nbit   <= nbit + 1'b1;
                        end
                    end

                    T_RD_ACK: begin
                        if (scl_rise) nack <= sda;
                        else if (scl_fall) begin
                            if (nack) state <= T_IDLE;            // controller is done
                            else begin
                                shift  <= regs[ptr];
                                ptr    <= ptr + 1'b1;
                                sda_oe <= !regs[ptr][7];
                                nbit   <= 4'd1;
                                state  <= T_RD;
                            end
                        end
                    end

                    default: ;                                    // T_IDLE: wait for START
                endcase
            end
        end
    end

    wire [3:0] dirty4;
    generate
        if (NREGS >= 4) begin : g_d4
            assign dirty4 = dirty[3:0];
        end else begin : g_dn
            assign dirty4 = {{(4 - NREGS){1'b0}}, dirty};
        end
    endgenerate

    wire _unused = &{h_wlast, 1'b0};
    assign h_status = {dirty4, overrun_q, cmd_err_q, 1'b0, (state != T_IDLE)};
endmodule
