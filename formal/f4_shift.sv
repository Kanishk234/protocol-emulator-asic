// F4 (docs/design/VERIFICATION.md): wp_shift equals the cycle-exact spec of ARCHITECTURE §8.2,
// for every configuration (held constant) and every input sequence. Spec model from the document.
`default_nettype none

module f4_shift (
    input wire       clk,
    input wire       rst, load, step, sin,
    input wire [7:0] d,
    input wire [4:0] cfg
);
    wire       sout, done;
    wire [7:0] q;
    wire [3:0] d_n;
    wp_shift dut (.CLK(clk), .rst(rst), .load(load), .step(step), .sin(sin), .d(d),
                  .sout(sout), .done(done), .q(q), .f_n(d_n), .ConfigBits(cfg));

    reg past = 1'b0;
    always @(posedge clk) past <= 1'b1;
    always @(posedge clk) if (past) assume ($stable(cfg));

    reg [7:0] m_sr;
    reg [3:0] m_n;
    wire [3:0] len = cfg[3:0];
    wire       msb = cfg[4];
    always @(posedge clk) begin
        if (rst)       begin m_sr <= 8'd0; m_n <= 4'd0; end
        else if (load) begin m_sr <= d;    m_n <= 4'd0; end
        else if (step) begin
            m_sr <= msb ? {m_sr[6:0], sin} : {sin, m_sr[7:1]};
            if (m_n != len) m_n <= m_n + 1'b1;
        end
    end

    always @(*) if (!past) assume (rst);
    always @(*) if (past) begin
        assert (d_n == m_n);
        assert (q == m_sr);
        assert (sout == (msb ? m_sr[7] : m_sr[0]));
        assert (done == (m_n == len));
    end
endmodule
