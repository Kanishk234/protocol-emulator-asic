# RTL tests for the CAN 2.0A controller user design (cocotb + Icarus).
#   make [PRIMS=1] [BIT=20]
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
PRIMS ?= 0
BIT ?= 20

SRC = $(PWD)/..
ROOT = $(PWD)/../../..
VERILOG_SOURCES = $(SRC)/can_top.v
VERILOG_SOURCES += $(ROOT)/tools/compile/prims/warp_prims_sim.v $(ROOT)/arch/prims/wp_timer.v $(ROOT)/arch/prims/wp_shift.v
COMPILE_ARGS += -Pcan_top.PRIMS=$(PRIMS) -Pcan_top.BIT=$(BIT)
SIM_BUILD = sim_build/p$(PRIMS)_b$(BIT)

TOPLEVEL = can_top
COCOTB_TEST_MODULES = test_can
export PYTHONPATH := $(PWD)/../../../tools:$(PYTHONPATH)
export PRIMS BIT

include $(shell cocotb-config --makefiles)/Makefile.sim
