// Basys 3 block RAM implementation of the ASIC SRAM wrapper interface.
// Reset suppresses access. Writes and disabled cycles retain the last read value.
`default_nettype none
module trw_sram (
    input wire clk, rst_n, en, we,
    input wire [8:0] addr,
    input wire [15:0] wdata,
    output reg [15:0] rdata
);
    reg [15:0] memory [0:511];
    always @(posedge clk) begin
        if (rst_n && en) begin
            if (we)
                memory[addr] <= wdata;
            else
                rdata <= memory[addr];
        end
    end
endmodule
