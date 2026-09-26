# RTL tests for the I2C controller user design (cocotb + Icarus).
#   make [Q=4]
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
Q ?= 4

SRC = $(PWD)/..
VERILOG_SOURCES = $(SRC)/i2c_ctrl_top.v
COMPILE_ARGS += -Pi2c_ctrl_top.Q=$(Q)
SIM_BUILD = sim_build/q$(Q)

TOPLEVEL = i2c_ctrl_top
COCOTB_TEST_MODULES = test_i2c_ctrl
export PYTHONPATH := $(PWD)/../../../tools:$(PYTHONPATH)
export Q

include $(shell cocotb-config --makefiles)/Makefile.sim
