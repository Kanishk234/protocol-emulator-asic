// I2C target user design (provisional user-design interface, DECISIONS D-014).
//
// Bus:   open drain. sda_oe = 1 pulls SDA low (ACK, data 0); SCL is only read (no stretching).
//        sda_i / scl_i are used as they arrive: the shell synchronizes every input (ARCHITECTURE
//        §6; simulated alone, drive them synchronously). SCL low and high phases must each last
//        >= 4 clocks.
// Map:   NREGS (power of two, <= 16) 8-bit registers.
//        Bus write:  [ADDR+W] [pointer] [data ...]  -> registers from the pointer, auto-increment
//                    (wrapping); the pointer is taken modulo NREGS. Every byte is ACKed.
//        Bus read:   [ADDR+R] -> registers from the pointer, auto-increment, until the
//                    controller NACKs. A repeated START keeps the pointer.
//        Other addresses are not ACKed and the transaction is ignored.
// Host:  command bytes on h_w* (h_wlast ignored):
//          8'b0000_iiii, then a data byte  write register i
//          8'b1000_iiii                    read register i; reply on h_r*; clears dirty[i]
//        The registers have one write port and one read port, shared: in a clock where the bus
//        writes a register or loads a byte to send, h_wready is 0 and the host byte waits.
//        h_status = {dirty[3:0] (registers 0..3 written by the bus since the host last read
//                    them), overrun, cmd_err, 1'b0, addressed}.
// PRIMS: 1: the bus byte (in and out) and its bit count in a WARP hard shift register
//        (ARCHITECTURE §8, D-026); 0: the same register in plain logic. Same behaviour.
`default_nettype none

module i2c_target_top #(
    parameter [6:0] ADDR  = 7'h42,
    parameter       NREGS = 4,
    parameter       PRIMS = 0
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

    localparam [1:0] T_IDLE = 2'd0,  // not addressed: wait for START
                     T_RX   = 2'd1,  // receiving a byte (address first, then write data)
                     T_ACK  = 2'd2,  // driving ACK for one SCL clock
                     T_TX   = 2'd3;  // sending a read byte, then reading the controller's ACK

    reg [8*NREGS-1:0] regs;            // register i is regs[8*i +: 8] (flip-flops, not a memory)
    reg [NREGS-1:0] dirty;

    reg          sda_q, scl_q;         // previous values, for edges and START/STOP
    reg [1:0]    state;
    reg [IW-1:0] ptr;
    reg          addr_ph;              // T_RX: the byte is the address
    reg          rw, first, nack;
    reg          overrun_q, cmd_err_q;
    reg          h_pend;               // a host write command is waiting for its data byte
    reg [IW-1:0] h_idx;

    wire scl_rise = scl_i && !scl_q;
    wire scl_fall = !scl_i && scl_q;
    wire start    = scl_i && scl_q && !sda_i && sda_q;
    wire stop     = scl_i && scl_q && sda_i && !sda_q;
    wire bus_ev   = !start && !stop;

    // Byte register: T_RX shifts SDA in on SCL rising edges, MSB first; T_TX shifts the byte
    // out (SDA takes q[6] at each falling edge; ones fill in, so the 8th edge releases SDA).
    // done = 8 steps since the last load.
    wire       sr_done;
    wire [7:0] sr_q;
    wire       sr_load;
    wire       sr_step;
    wire [7:0] rd_data;                // the shared read port

    // Register access (bus side), in this clock
    wire rx_byte = bus_ev && state == T_RX && scl_fall && sr_done;
    wire addr_ok = sr_q[7:1] == ADDR;
    wire bus_we  = rx_byte && !addr_ph && !first;                        // data byte written
    wire tx_ld   = bus_ev && scl_fall && ((state == T_ACK && rw) ||      // first read byte
                                          (state == T_TX && sr_done && !nack));  // next one

    assign sr_load = start || tx_ld || (bus_ev && state == T_ACK && scl_fall && !rw);
    assign sr_step = bus_ev && ((state == T_RX && scl_rise) || (state == T_TX && scl_fall && !sr_done));

    generate
        if (PRIMS != 0) begin : g_prims
            wire sout_unused;
            WP_SHIFT #(.LEN(4'd8), .MSB_FIRST(1'b1)) u_shift (
                .clk(clk), .rst(!rst_n), .load(sr_load), .step(sr_step),
                .sin(state == T_TX ? 1'b1 : sda_i), .d(rd_data),
                .sout(sout_unused), .done(sr_done), .q(sr_q));
            wire _unused_p = &{sout_unused, 1'b0};
        end else begin : g_logic
            reg [7:0] sr;
            reg [3:0] n;
            always @(posedge clk) begin
                if (!rst_n) begin
                    sr <= 8'h00;
                    n  <= 4'd0;
                end else if (sr_load) begin
                    sr <= rd_data;
                    n  <= 4'd0;
                end else if (sr_step) begin
                    sr <= {sr[6:0], state == T_TX ? 1'b1 : sda_i};
                    if (n != 4'd8) n <= n + 1'b1;
                end
            end
            assign sr_q    = sr;
            assign sr_done = (n == 4'd8);
        end
    endgenerate

    assign sda_o = 1'b0;

    // Host side: stalled in clocks where the bus uses the write or the read port
    assign h_wready = !(bus_we || tx_ld);
    wire h_take  = h_wvalid && h_wready;
    wire h_bad   = h_wdata[6:4] != 3'b000 || h_wdata[3:0] >= NREGS;
    wire h_write = h_take && h_pend;

    // One read port (bus load or host read) and one write port (bus or host)
    wire [IW-1:0] r_idx = tx_ld ? ptr : h_wdata[IW-1:0];
    assign rd_data = regs[8 * r_idx +: 8];
    wire [IW-1:0] w_idx  = bus_we ? ptr : h_idx;
    wire [7:0]    w_data = bus_we ? sr_q : h_wdata;

    genvar gi;
    generate
        for (gi = 0; gi < NREGS; gi = gi + 1) begin : g_reg
            always @(posedge clk) begin
                if (!rst_n)                                       regs[8*gi +: 8] <= 8'h00;
                else if ((bus_we || h_write) && w_idx == gi)      regs[8*gi +: 8] <= w_data;
            end
        end
    endgenerate

    always @(posedge clk) begin
        if (!rst_n) begin
            dirty     <= {NREGS{1'b0}};
            sda_q     <= 1'b1;
            scl_q     <= 1'b1;
            state     <= T_IDLE;
            ptr       <= {IW{1'b0}};
            addr_ph   <= 1'b0;
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
            sda_q <= sda_i;
            scl_q <= scl_i;
            if (h_rvalid && h_rready) h_rvalid <= 1'b0;

            // ---- host commands
            if (h_take) begin
                if (h_pend) h_pend <= 1'b0;                       // data byte written above
                else if (h_bad) cmd_err_q <= 1'b1;
                else if (h_wdata[7]) begin
                    if (h_rvalid && !h_rready) overrun_q <= 1'b1;
                    else begin
                        h_rdata  <= rd_data;
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
                state   <= T_RX;
                addr_ph <= 1'b1;
                sda_oe  <= 1'b0;
            end else if (stop) begin
                state  <= T_IDLE;
                sda_oe <= 1'b0;
            end else begin
                case (state)
                    T_RX: if (rx_byte) begin
                        if (addr_ph) begin
                            addr_ph <= 1'b0;
                            if (addr_ok) begin
                                rw     <= sr_q[0];
                                first  <= !sr_q[0];
                                sda_oe <= 1'b1;                   // ACK
                                state  <= T_ACK;
                            end else begin
                                state <= T_IDLE;                  // not us
                            end
                        end else begin
                            if (first) begin
                                ptr   <= sr_q[IW-1:0];
                                first <= 1'b0;
                            end else begin
                                dirty[ptr] <= 1'b1;               // written above (bus_we)
                                ptr        <= ptr + 1'b1;
                            end
                            sda_oe <= 1'b1;                       // ACK
                            state  <= T_ACK;
                        end
                    end

                    T_ACK: if (scl_fall) begin                    // end of the ACK clock
                        if (rw) begin                             // byte loaded (tx_ld)
                            ptr    <= ptr + 1'b1;
                            sda_oe <= !rd_data[7];
                            nack   <= 1'b0;
                            state  <= T_TX;
                        end else begin
                            sda_oe <= 1'b0;
                            state  <= T_RX;
                        end
                    end

                    T_TX: begin
                        if (scl_rise && sr_done) nack <= sda_i;   // the controller's ACK bit
                        else if (scl_fall) begin
                            if (!sr_done) sda_oe <= !sr_q[6];     // next bit; the 8th edge releases
                            else if (nack) state <= T_IDLE;       // controller is done
                            else begin                            // next byte loaded (tx_ld)
                                ptr    <= ptr + 1'b1;
                                sda_oe <= !rd_data[7];
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
