# L1 lane tests (white-box): EVAL, the pipeline, routines, halt/STEP and host writes.
# Run inside the project venv (source .venv/bin/activate): make
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
SRC_DIR ?= $(PWD)/../../src

VERILOG_SOURCES = $(SRC_DIR)/trw_alu.v $(SRC_DIR)/trw_lane.v $(PWD)/tb_lane.v
COMPILE_ARGS += -I$(SRC_DIR)
TOPLEVEL = tb_lane
COCOTB_TEST_MODULES ?= test_lane

include $(shell cocotb-config --makefiles)/Makefile.sim
