"""Working examples for the Tiny Tapeout demo board (D-032): drive the design-set protocols,
loaded as WARP bitstreams, from the RP2040 through the host byte channel. Each function takes a
`warp.Warp` whose design is running. MicroPython and CPython (tests run these same functions
against the chip's simulation, test/test_bitstream.py::test_board_examples_*).

Pins (docs/EXAMPLES.md): FAB_OUT0..5 = uo_out[2..7], FAB_IN0..4 = ui_in[3..7],
FAB_IO0..7 = uio[0..7].
"""

# ---- UART (protocols/uart, pins: rx_i = FAB_IN0, tx_o = FAB_OUT0) -----------------------------

def uart_send(w, data):
    """Send bytes out of tx_o (8N1 at the bitstream's baud rate)."""
    for b in data:
        w.ch_write(b)


def uart_recv(w, n, tries=1000):
    """Up to n received bytes (fewer if none arrive)."""
    out = []
    for _ in range(n):
        b = w.ch_read(tries)
        if b is None:
            break
        out.append(b)
    return out


def uart_errors(w):
    """(overrun, framing_error, tx_busy) from the design's status (sticky until USER_RESET)."""
    s = w.user_status()
    return bool(s & 4), bool(s & 2), bool(s & 1)


# ---- SPI controller (protocols/spi_ctrl, pins: sck = FAB_OUT0, mosi = FAB_OUT1,
#      cs_n = FAB_OUT2, miso = FAB_IN0) -------------------------------------------------------

def spi_transfer(w, data):
    """One SPI transaction (CS low for all bytes): returns the bytes read on MISO."""
    got = []
    for i, b in enumerate(data):
        w.ch_write(b, last=(i == len(data) - 1))
        got.append(w.ch_read())
    return got


# ---- I2C controller (protocols/i2c_ctrl, pins: sda = FAB_IO0, scl = FAB_IO1, open drain;
#      external pull-ups) ----------------------------------------------------------------------

I2C_START, I2C_WRITE, I2C_READ_ACK, I2C_READ_NACK, I2C_STOP = 0x00, 0x40, 0x80, 0x81, 0xC0


class I2CNack(Exception):
    pass


def _i2c_write_byte(w, b):
    w.ch_write(I2C_WRITE)
    w.ch_write(b)
    ack = w.ch_read()
    if ack != 0:
        raise I2CNack("NACK on 0x%02X" % b)


def i2c_write_regs(w, addr, reg, data):
    """[START][addr+W][reg][data...][STOP]: write consecutive registers of a device."""
    w.ch_write(I2C_START)
    try:
        _i2c_write_byte(w, addr << 1)
        _i2c_write_byte(w, reg)
        for b in data:
            _i2c_write_byte(w, b)
    finally:
        w.ch_write(I2C_STOP)


def i2c_read_regs(w, addr, reg, n):
    """[START][addr+W][reg][START][addr+R][n bytes, NACK on the last][STOP]."""
    out = []
    w.ch_write(I2C_START)
    try:
        _i2c_write_byte(w, addr << 1)
        _i2c_write_byte(w, reg)
        w.ch_write(I2C_START)                       # repeated START
        _i2c_write_byte(w, addr << 1 | 1)
        for i in range(n):
            w.ch_write(I2C_READ_NACK if i == n - 1 else I2C_READ_ACK)
            out.append(w.ch_read())
    finally:
        w.ch_write(I2C_STOP)
    return out


def i2c_probe(w, addr):
    """True if a device ACKs its address."""
    w.ch_write(I2C_START)
    try:
        _i2c_write_byte(w, addr << 1)
        return True
    except I2CNack:
        return False
    finally:
        w.ch_write(I2C_STOP)
