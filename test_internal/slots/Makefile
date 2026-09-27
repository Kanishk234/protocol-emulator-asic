# L1 slot-store tests (white-box): make [FLOPS=0|1]
# Run inside the project venv (source .venv/bin/activate).
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
FLOPS ?= 0
SRC_DIR ?= $(PWD)/../../src
SIM_BUILD = sim_build/flops$(FLOPS)

VERILOG_SOURCES = $(SRC_DIR)/trw_slots.v
COMPILE_ARGS += -I$(SRC_DIR)
ifeq ($(FLOPS),1)
COMPILE_ARGS += -DTRW_SLOTS_FLOPS
endif
TOPLEVEL = trw_slots
COCOTB_TEST_MODULES ?= test_slots
COCOTB_RESULTS_FILE = results_flops$(FLOPS).xml

include $(shell cocotb-config --makefiles)/Makefile.sim
