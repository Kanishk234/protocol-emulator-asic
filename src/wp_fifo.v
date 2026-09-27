// Small synchronous FIFO for the host byte channels (ARCHITECTURE.md §7.3). 2**AW entries.
// A push while full or a pop while empty is ignored (the caller reports overflow).
`default_nettype none

module wp_fifo #(
    parameter integer WIDTH = 8,
    parameter integer AW = 1
) (
    input  wire             clk,
    input  wire             rst_n,
    input  wire             clear,
    input  wire             push,
    input  wire [WIDTH-1:0] din,
    input  wire             pop,
    output wire [WIDTH-1:0] dout,
    output wire             full,
    output wire             empty
);
    localparam integer DEPTH = 1 << AW;

    reg [WIDTH*DEPTH-1:0] mem;
    reg [AW:0]            wp, rp;
    integer               i;

    wire do_push = push && !full;
    wire do_pop  = pop && !empty;

    always @(posedge clk) begin
        if (!rst_n || clear) begin
            wp  <= {(AW+1){1'b0}};
            rp  <= {(AW+1){1'b0}};
            mem <= {(WIDTH*DEPTH){1'b0}};
        end else begin
            if (do_push) begin
                for (i = 0; i < DEPTH; i = i + 1)
                    if (wp[AW-1:0] == i[AW-1:0])
                        mem[i*WIDTH +: WIDTH] <= din;
                wp <= wp + 1'b1;
            end
            if (do_pop)
                rp <= rp + 1'b1;
        end
    end

    assign dout  = mem[rp[AW-1:0]*WIDTH +: WIDTH];
    assign empty = (wp == rp);
    assign full  = (wp[AW-1:0] == rp[AW-1:0]) && (wp[AW] != rp[AW]);
endmodule
