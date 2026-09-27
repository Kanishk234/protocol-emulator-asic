// Host channel test design (ARCHITECTURE §7.3): takes each byte the host writes and returns it
// plus one; h_status counts the bytes taken; h_attention is raised by a byte marked last and stays
// up until a user reset. One-byte buffer: the next host byte is taken once the returned one has
// been handed to the shell.
`default_nettype none

module hostecho (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [7:0] h_wdata,
    input  wire       h_wlast,
    input  wire       h_wvalid,
    output wire       h_wready,
    output reg  [7:0] h_rdata,
    output reg        h_rvalid,
    input  wire       h_rready,
    output wire [7:0] h_status,
    output wire       h_attention
);
    reg [7:0] count;
    reg       last_seen;

    assign h_wready    = !h_rvalid;
    assign h_status    = count;
    assign h_attention = last_seen;

    always @(posedge clk) begin
        if (!rst_n) begin
            h_rdata   <= 8'd0;
            h_rvalid  <= 1'b0;
            count     <= 8'd0;
            last_seen <= 1'b0;
        end else begin
            if (h_rvalid && h_rready)
                h_rvalid <= 1'b0;
            if (h_wvalid && !h_rvalid) begin
                h_rdata  <= h_wdata + 8'd1;
                h_rvalid <= 1'b1;
                count    <= count + 8'd1;
                if (h_wlast)
                    last_seen <= 1'b1;
            end
        end
    end
endmodule
