# RTL tests for the I2C target user design (cocotb + Icarus).
#   make [Q=4] [NREGS=4] [PRIMS=1]     Q: controller phase length; PRIMS=1: on the WARP hard primitives
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
Q ?= 4
NREGS ?= 4
PRIMS ?= 0

SRC = $(PWD)/..
ROOT = $(PWD)/../../..
VERILOG_SOURCES = $(SRC)/i2c_target_top.v
VERILOG_SOURCES += $(ROOT)/tools/compile/prims/warp_prims_sim.v $(ROOT)/arch/prims/wp_timer.v $(ROOT)/arch/prims/wp_shift.v
COMPILE_ARGS += -Pi2c_target_top.NREGS=$(NREGS) -Pi2c_target_top.PRIMS=$(PRIMS)
SIM_BUILD = sim_build/n$(NREGS)_p$(PRIMS)

TOPLEVEL = i2c_target_top
COCOTB_TEST_MODULES = test_i2c_target
export PYTHONPATH := $(PWD)/../../../tools:$(PYTHONPATH)
export Q NREGS PRIMS

include $(shell cocotb-config --makefiles)/Makefile.sim
