# Test-only firmware fixtures

These programs exercise the unchanged qualified two-lane/four-unit design through
the same compiler and SPI host loader as production firmware. They are not extra
synthesis sources or new hardware capabilities.

| Fixture | Loop wiring in the test environment | Lane slots | Units | SRAM image |
|---|---|---|---|---|
| `l4_uart_loop.trw` | uo0 TX to ui0 RX | L0:1, L1:3 | U0 TX, U1 RX | 32 entry words, unused |
| `l4_spi_loop.trw` | uo1 MOSI to ui0 MISO | L0:4, L1:1 | Existing U0–U3 controller pins | 32 entry words, unused |
| `l4_i2c_loop.trw` | uio0 controller SDA tied open-drain to uio2 target SDA; shared uio1 SCL | L0:11, L1:12 | U0 controller SDA, U1 SCL, U2 target SDA | 62 words: entry table and existing controller routines |

UART separates TX and framing-checked RX across lanes. SPI retains the controller
sequence, consuming its RX completion in lane0 while lane1 forwards the received
byte. I2C combines the existing controller routines with a target that caches the
last written byte in a register and returns it on the subsequent read. It is not
an EEPROM implementation. Tests deliberately disconnect each loop as negative
controls.

Baseline and idle-inserted runs use identical compiled images. Idle is inserted
between complete UART/SPI frames or STOP-completed I2C write/read groups, with
fixed seeds and without changing symbols or stretching an active frame. Each
returned sequence must match its input and independent sigrok decoding of actual
pad captures. See [the evidence](../../docs/reports/PHASE3_METAMORPHIC_LOOP_IDLE.md).
