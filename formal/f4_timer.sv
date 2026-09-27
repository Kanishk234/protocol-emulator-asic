// F4 (docs/design/VERIFICATION.md): wp_timer equals the cycle-exact spec of ARCHITECTURE §8.1,
// for every configuration (held constant, as the configuration latches are while running) and
// every input sequence. The spec model below is written from the document, not from the RTL.
`default_nettype none

module f4_timer (
    input wire        clk,
    input wire        rst, load, half, en,
    input wire [16:0] cfg
);
    wire tc;
    wire [15:0] d_count;
    wire        d_armed;
    wp_timer dut (.CLK(clk), .rst(rst), .load(load), .half(half), .en(en), .tc(tc),
                  .f_count(d_count), .f_armed(d_armed), .ConfigBits(cfg));

    // configuration does not change while the design runs
    reg past = 1'b0;
    always @(posedge clk) past <= 1'b1;
    always @(posedge clk) if (past) assume ($stable(cfg));

    // spec model
    reg [15:0] m_count;
    reg        m_armed;
    wire [15:0] reload = cfg[15:0];
    wire        oneshot = cfg[16];
    always @(posedge clk) begin
        if (rst)                  begin m_count <= reload; m_armed <= 1'b1; end
        else if (load)            begin m_count <= half ? reload >> 1 : reload; m_armed <= 1'b1; end
        else if (en && m_armed) begin
            if (m_count == 0)     begin m_count <= reload; m_armed <= !oneshot; end
            else                  m_count <= m_count - 1'b1;
        end
    end

    // both start from a reset (the design is held in reset before RUN, ARCHITECTURE §5)
    always @(*) if (!past) assume (rst);
    always @(*) if (past) begin
        assert (d_count == m_count && d_armed == m_armed);
        assert (tc == (en && m_armed && m_count == 0));
    end
endmodule
