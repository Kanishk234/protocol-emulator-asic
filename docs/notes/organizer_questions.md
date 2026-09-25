# Draft organizer questions — not sent

To: asic-competition@janestreet.com

Subject: Protocol emulator competition: eFPGA architecture and macro integration

We are developing an open-source protocol emulator for the January 2027
competition. We are evaluating a small embedded FPGA, with a fixed loader
and host data interface, instead of a CPU executing a protocol ISA. Users
would compile synthesizable Verilog into bitstreams and load new protocols
after fabrication. UART, SPI and I2C would be user designs, not fixed
protocol controllers.

1. Does an implementation with no on-chip CPU meet the competition's
   intended scope?
2. May a FABulous fabric be hardened separately on the same CMOS5L PDK and
   integrated as a macro, provided the complete submission passes the
   Tiny Tapeout template's checks?
3. We are budgeting 6x4, as currently stated in the announcement. Has an
   8x4 allocation been approved for this competition?

Repository: https://github.com/Kanishk234/protocol-emulator-asic

No answer has been recorded. The existence of an 8x4 template or another
project's macro does not establish organizer approval. The [competition
announcement](https://blog.janestreet.com/protocol-emulator-asic-competition/)
was checked on 2026-09-25 and still states 6x4 with a possible increase.
