# RTL tests for the 1-Wire controller user design (cocotb + Icarus).
#   make [PRIMS=1]            US = 50 (50 MHz)
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
PRIMS ?= 0

SRC = $(PWD)/..
ROOT = $(PWD)/../../..
VERILOG_SOURCES = $(SRC)/onewire_top.v
VERILOG_SOURCES += $(ROOT)/tools/compile/prims/warp_prims_sim.v $(ROOT)/arch/prims/wp_timer.v $(ROOT)/arch/prims/wp_shift.v
COMPILE_ARGS += -Ponewire_top.PRIMS=$(PRIMS)
SIM_BUILD = sim_build/p$(PRIMS)

TOPLEVEL = onewire_top
COCOTB_TEST_MODULES = test_onewire
export PYTHONPATH := $(PWD)/../../../tools:$(PYTHONPATH)
export PRIMS

include $(shell cocotb-config --makefiles)/Makefile.sim
