// R1 risk spike (throwaway): one fabric consumer port (ARCHITECTURE.md §4.3, §14 F1, F2, F7).
// The source multiplexer sits next to the consumer (§4.6). F5 (re-pointing) is not modelled here:
// the spike's configuration is static.
`default_nettype none

module trw_cport #(
    parameter N = 9                     // legal sources, in `sel` order
) (
    input  wire          clk,
    input  wire          rst_n,
    input  wire          en,
    input  wire [3:0]    sel,
    input  wire [3:0]    accept,        // tag mask (D-015)
    input  wire [N-1:0]  src_valid,
    input  wire [N-1:0]  src_seq,
    input  wire [2*N-1:0]  src_tag,
    input  wire [16*N-1:0] src_data,
    input  wire          take,          // the consumer takes the head this clock (only when avail)
    output wire          avail,
    output wire [17:0]   head,          // {tag, data}
    output reg           last_seq
);
    reg         s_valid, s_seq;
    reg  [1:0]  s_tag;
    reg  [15:0] s_data;
    integer n;
    always @* begin
        s_valid = 1'b0;                 // sel beyond the list: nothing available
        s_seq   = 1'b0;
        s_tag   = 2'd0;
        s_data  = 16'd0;
        for (n = 0; n < N; n = n + 1) begin
            if ({28'd0, sel} == n) begin
                s_valid = src_valid[n];
                s_seq   = src_seq[n];
                s_tag   = src_tag[2*n +: 2];
                s_data  = src_data[16*n +: 16];
            end
        end
    end

    wire present  = en && s_valid && (last_seq != s_seq);               // F1
    wire accepted = accept[s_tag];
    assign avail  = present && accepted;
    assign head   = {s_tag, s_data};

    always @(posedge clk) begin
        if (!rst_n)
            last_seq <= 1'b0;
        else if ((avail && take) || (present && !accepted))            // F2, F7
            last_seq <= s_seq;
    end
endmodule
