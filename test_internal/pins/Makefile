# L1 pad-owner tests (white-box): trw_pins against §7.1 / §10.
# Run inside the project venv (source .venv/bin/activate): make
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
SRC_DIR ?= $(PWD)/../../src

VERILOG_SOURCES = $(SRC_DIR)/trw_pins.v $(SRC_DIR)/trw_sync.v
COMPILE_ARGS += -I$(SRC_DIR) -DSIM_ASSERT
TOPLEVEL = trw_pins
COCOTB_TEST_MODULES ?= test_pins

include $(shell cocotb-config --makefiles)/Makefile.sim
