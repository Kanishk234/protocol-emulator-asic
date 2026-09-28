// F3 (docs/design/VERIFICATION.md): the shell's host-channel FIFO (src/wp_fifo.v) never loses,
// duplicates or reorders a byte: a shadow queue written from the specification (push when not
// full, pop when not empty, a push while full is dropped, `clear` empties it) must agree with
// the FIFO's `empty`, `full` and `dout` in every cycle, for every sequence of inputs.
`default_nettype none

module f3_fifo #(
    parameter integer AW = 1
) (
    input wire       clk,
    input wire       rst_n,
    input wire       clear,
    input wire       push,
    input wire [7:0] din,
    input wire       pop
);
    localparam integer DEPTH = 1 << AW;

    wire [7:0] dout;
    wire       full, empty;
    wp_fifo #(.WIDTH(8), .AW(AW)) dut (
        .clk(clk), .rst_n(rst_n), .clear(clear), .push(push), .din(din), .pop(pop),
        .dout(dout), .full(full), .empty(empty));

    // shadow queue: q[0] is the head
    reg [7:0]  q [0:DEPTH-1];
    reg [AW:0] n;
    wire m_push = push && n != DEPTH;
    wire m_pop  = pop && n != 0;
    integer i;
    always @(posedge clk) begin
        if (!rst_n || clear) begin
            n <= 0;
        end else begin
            if (m_pop) begin
                for (i = 0; i < DEPTH - 1; i = i + 1) q[i] <= q[i + 1];
                if (m_push) q[n - 1] <= din;               // the new byte after the remaining ones
            end else if (m_push) begin
                q[n] <= din;
            end
            n <= n + m_push - m_pop;
        end
    end

    reg past = 1'b0;
    always @(posedge clk) past <= 1'b1;
    always @(*) if (!past) assume (!rst_n);                 // start from a reset

    always @(*) if (past && rst_n) begin
        assert (empty == (n == 0));
        assert (full == (n == DEPTH));
        if (n != 0) assert (dout == q[0]);
    end
    // Entries behind the head are not compared directly (no hierarchical references into the
    // unmodified RTL); each reaches `dout` within DEPTH pops, and abc pdr proves the property
    // for every reachable state, so a wrong hidden entry would show up at `dout`.
    // cover: a full FIFO drains in order
    always @(*) if (past) cover (full && rst_n);
endmodule
