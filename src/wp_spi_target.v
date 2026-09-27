// SPI target, mode 0, MSB first, oversampled on clk (ARCHITECTURE.md §2.1). Inputs must already
// be synchronized to clk (wp_sync).
//
// Receive: MOSI is sampled on each detected SCK rising edge; after 8 bits `rx_valid` pulses with
// `rx_byte`. Transmit: the byte to send is taken from `tx_byte` two cycles after a transaction
// starts (`start`) or a byte completes (`rx_valid`), so the controller can present a `tx_byte`
// that depends on the byte just received. MISO shifts on the detected SCK rising edge, right
// after the host has sampled it, which leaves most of an SCK period of setup for the next bit.
//
// Host timing (from the two-flop synchronizers and the 2-cycle load): SCK <= clk/8, CS_N falling
// to the first SCK rising edge >= 8 clk, CS_N high between transactions >= 4 clk.
`default_nettype none

module wp_spi_target (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       cs_n,       // synchronized
    input  wire       sck,        // synchronized
    input  wire       mosi,       // synchronized
    input  wire [7:0] tx_byte,
    output wire       miso,
    output reg        start,      // one cycle: CS_N fell
    output reg        rx_valid,   // one cycle: rx_byte complete
    output reg  [7:0] rx_byte
);
    reg       cs_n_q, sck_q, load;
    reg [2:0] bit_cnt;
    reg [6:0] rx_sr;
    reg [7:0] tx_sr;

    always @(posedge clk) begin
        if (!rst_n) begin
            cs_n_q   <= 1'b1;
            sck_q    <= 1'b0;
            load     <= 1'b0;
            bit_cnt  <= 3'd0;
            rx_sr    <= 7'd0;
            tx_sr    <= 8'd0;
            start    <= 1'b0;
            rx_valid <= 1'b0;
            rx_byte  <= 8'd0;
        end else begin
            cs_n_q   <= cs_n;
            sck_q    <= sck;
            start    <= 1'b0;
            rx_valid <= 1'b0;
            load     <= start | rx_valid;
            if (load)
                tx_sr <= tx_byte;
            if (cs_n) begin
                bit_cnt <= 3'd0;
            end else if (cs_n_q) begin
                start   <= 1'b1;
                bit_cnt <= 3'd0;
            end else if (sck && !sck_q) begin
                rx_sr   <= {rx_sr[5:0], mosi};
                bit_cnt <= bit_cnt + 3'd1;
                if (bit_cnt == 3'd7) begin
                    rx_valid <= 1'b1;
                    rx_byte  <= {rx_sr, mosi};
                end else begin
                    tx_sr <= {tx_sr[6:0], 1'b0};
                end
            end
        end
    end

    assign miso = !cs_n && tx_sr[7];
endmodule
