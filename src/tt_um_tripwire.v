// R4 run 6 (branch spike/r4-floorplan only; never merged, DECISIONS D-043, D-049): the real chip
// (src/trw_chip.v from main) at the protocol floor's counts, to measure whether that size routes on 6x4.
//
// The counts come from this branch's spec/tripwire.yaml: 2 lanes, 4 pin units, only U0 full (D-049: every
// protocol still has what it needs, one at a time), 12 slots per lane, the 512-word SRAM. The fabric, the
// host map and trw_defs.vh are regenerated from it (tools/gen/gen.py). Everything else is main's RTL as is.
//
// Pins (ARCHITECTURE.md §9, §10): ui[4] CS_n, ui[5] SCK, ui[6] MOSI, uo[3] MISO, uo[6] IRQ; the other
// 19 pads belong to the pin units through the owner registers.
`default_nettype none

module tt_um_tripwire (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);
    trw_chip u_chip (
        .ui_in (ui_in), .uo_out (uo_out), .uio_in (uio_in), .uio_out (uio_out), .uio_oe (uio_oe),
        .ena (ena), .clk (clk), .rst_n (rst_n)
    );
endmodule
