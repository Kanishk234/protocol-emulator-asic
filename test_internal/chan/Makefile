# L1-CHAN tests (white-box): the generated fabric with a producer register on every producer.
# Run inside the project venv (source .venv/bin/activate): make
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
SRC_DIR ?= $(PWD)/../../src

VERILOG_SOURCES = $(SRC_DIR)/trw_chan_prod.v $(SRC_DIR)/trw_chan_port.v $(SRC_DIR)/trw_fabric.v $(PWD)/tb_chan.v
COMPILE_ARGS += -I$(SRC_DIR)
TOPLEVEL = tb_chan
COCOTB_TEST_MODULES ?= test_chan

include $(shell cocotb-config --makefiles)/Makefile.sim
