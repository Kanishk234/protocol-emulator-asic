# L1 lane tests (white-box): EVAL, the pipeline, routines, halt/STEP and host writes.
# Run inside the project venv (source .venv/bin/activate): make
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
SRC_DIR ?= $(CURDIR)/../../src

VERILOG_SOURCES = $(SRC_DIR)/trw_alu.v $(SRC_DIR)/trw_lane.v $(CURDIR)/tb_lane.v
COMPILE_ARGS += -I$(SRC_DIR) -DSIM_ASSERT
TOPLEVEL = tb_lane
COCOTB_TEST_MODULES ?= test_lane,test_response_contracts

include $(shell cocotb-config --makefiles)/Makefile.sim
