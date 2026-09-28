# RTL tests for the SWD host bit engine (cocotb + Icarus), driven by tools/board/swd.py.
#   make [PRIMS=1] [HALF=4]
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
PRIMS ?= 0
HALF ?= 4

SRC = $(PWD)/..
ROOT = $(PWD)/../../..
VERILOG_SOURCES = $(SRC)/swd_top.v
VERILOG_SOURCES += $(ROOT)/tools/compile/prims/warp_prims_sim.v $(ROOT)/arch/prims/wp_timer.v $(ROOT)/arch/prims/wp_shift.v
COMPILE_ARGS += -Pswd_top.PRIMS=$(PRIMS) -Pswd_top.HALF=$(HALF)
SIM_BUILD = sim_build/p$(PRIMS)_h$(HALF)

TOPLEVEL = swd_top
COCOTB_TEST_MODULES = test_swd
export PYTHONPATH := $(PWD)/../../../tools:$(PYTHONPATH)
export PRIMS

include $(shell cocotb-config --makefiles)/Makefile.sim
