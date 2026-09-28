# L1-ALU tests (white-box): the shared operation table against a Python reference from ISA.md §3.
# Run inside the project venv (source .venv/bin/activate): make
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
SRC_DIR ?= $(PWD)/../../src

VERILOG_SOURCES = $(SRC_DIR)/trw_alu.v
COMPILE_ARGS += -I$(SRC_DIR) -DSIM_ASSERT
TOPLEVEL = trw_alu
COCOTB_TEST_MODULES ?= test_alu

include $(shell cocotb-config --makefiles)/Makefile.sim
