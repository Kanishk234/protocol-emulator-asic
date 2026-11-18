# Independent RTL bus peer; uses the same maintained chip/official-netlist runner.
TOPLEVEL = tb_i2c_peer
COCOTB_TEST_MODULES = test_i2c_peer
TB_DIR = $(abspath $(CURDIR)/../chip)
EXTRA_VERILOG_SOURCES = $(abspath $(CURDIR)/../vendor/verilog_i2c/i2c_master.v) $(CURDIR)/tb_i2c_peer.v
export PYTHONPATH := $(CURDIR):$(TB_DIR):$(PYTHONPATH)
include ../chip/Makefile
