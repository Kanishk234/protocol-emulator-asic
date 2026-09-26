# RTL tests for the I2C target user design (cocotb + Icarus).
#   make [Q=4]      Q = SCL phase length of the reference controller, in clocks (>= 4)
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
Q ?= 4

SRC = $(PWD)/..
VERILOG_SOURCES = $(SRC)/i2c_target_top.v
SIM_BUILD = sim_build/rtl

TOPLEVEL = i2c_target_top
COCOTB_TEST_MODULES = test_i2c_target
export PYTHONPATH := $(PWD)/../../../tools:$(PYTHONPATH)
export Q

include $(shell cocotb-config --makefiles)/Makefile.sim
