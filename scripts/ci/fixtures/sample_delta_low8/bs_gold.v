`default_nettype none
`include "trw_defs.vh"
module wrapper_gold (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        restart,
    input  wire        live,
    input  wire        active,       // TXMODE and RXMODE are bitsync (and this is a full unit)
    // configuration (static while running)
    input  wire        idle,         // the recessive level
    input  wire        order,
    input  wire        tx_lentok,
    input  wire        nrzi,
    input  wire        oe_auto,
    input  wire [1:0]  delim,        // 0 none, 1 flag, 2 se0
    input  wire [23:0] period,       // 16.8 clocks
    input  wire [23:0] sampleofs,    // 16.8 clocks after the bit start
    input  wire [23:0] sjw,          // 16.8 clocks, 0 = hard sync only
    input  wire [4:0]  idle_bits,
    input  wire        resync_both,
    input  wire [3:0]  nbits,        // NBITS - 1
    input  wire [4:0]  rx_nbits,     // 0 = NBITS
    input  wire [3:0]  stuff_n,      // 0 = no stuffing
    input  wire [1:0]  stuff_lvl,    // 0 any level, 2 only runs of 0, 3 only runs of 1
    input  wire [4:0]  crc_width,    // 0 = no CRC
    input  wire [4:0]  crc_skip,
    input  wire [15:0] crc_poly,
    input  wire [15:0] crc_init,
    input  wire [15:0] crc_res,
    input  wire [15:0] crc_xor,
    // sensed pin (S, else A), this clock and the previous one; pin B (DELIM = se0)
    input  wire        a_in,
    input  wire        a_prev,
    input  wire        b_in,
    // consumer port head
    input  wire        tx_avail,
    input  wire [1:0]  tx_tag,
    input  wire [15:0] tx_data,
    output wire        tx_take,
    output wire        late_set,
    // producer register
    input  wire        rx_free,
    output wire        rx_load,
    output wire [1:0]  rx_tag,
    output wire [15:0] rx_data,
    output wire        ovr_set,
    // pin A (and pin N during SE0, P29)
    output wire        tx_lvl,
    output wire        tx_se0,
    output wire        tx_drv,       // a bit of ours is on the line (OE_AUTO)
    // state, for debug
    output reg         bus_idle,
    output reg         in_frame,
    output wire        bnd,          // a bit boundary at this clock's edge
    output wire        smp           // a sample in this clock
);
trw_pin_bs u_bs (.clk(clk),.rst_n(rst_n),.restart(restart),.live(live),.active(active),.idle(idle),.order(order),.tx_lentok(tx_lentok),.nrzi(nrzi),.oe_auto(oe_auto),.delim(delim),.period(period),.sampleofs(sampleofs),.sjw(sjw),.idle_bits(idle_bits),.resync_both(resync_both),.nbits(nbits),.rx_nbits(rx_nbits),.stuff_n(stuff_n),.stuff_lvl(stuff_lvl),.crc_width(crc_width),.crc_skip(crc_skip),.crc_poly(crc_poly),.crc_init(crc_init),.crc_res(crc_res),.crc_xor(crc_xor),.a_in(a_in),.a_prev(a_prev),.b_in(b_in),.tx_avail(tx_avail),.tx_tag(tx_tag),.tx_data(tx_data),.tx_take(tx_take),.late_set(late_set),.rx_free(rx_free),.rx_load(rx_load),.rx_tag(rx_tag),.rx_data(rx_data),.ovr_set(ovr_set),.tx_lvl(tx_lvl),.tx_se0(tx_se0),.tx_drv(tx_drv),.bus_idle(bus_idle),.in_frame(in_frame),.bnd(bnd),.smp(smp));
endmodule
