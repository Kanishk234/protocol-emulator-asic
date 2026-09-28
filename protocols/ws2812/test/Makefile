# RTL tests for the WS2812 transmitter user design (cocotb + Icarus).
#   make [PRIMS=1]            50 MHz parameters (TBIT 62, T1H 40, RESET_BITS 45)
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
PRIMS ?= 0
TBIT ?= 62
T1H ?= 40
RESET_BITS ?= 45

SRC = $(PWD)/..
ROOT = $(PWD)/../../..
VERILOG_SOURCES = $(SRC)/ws2812_top.v
VERILOG_SOURCES += $(ROOT)/tools/compile/prims/warp_prims_sim.v $(ROOT)/arch/prims/wp_timer.v $(ROOT)/arch/prims/wp_shift.v
COMPILE_ARGS += -Pws2812_top.PRIMS=$(PRIMS) -Pws2812_top.TBIT=$(TBIT) -Pws2812_top.T1H=$(T1H) -Pws2812_top.RESET_BITS=$(RESET_BITS)
SIM_BUILD = sim_build/p$(PRIMS)

TOPLEVEL = ws2812_top
COCOTB_TEST_MODULES = test_ws2812
export PYTHONPATH := $(PWD)/../../../tools:$(PYTHONPATH)
export PRIMS TBIT RESET_BITS

include $(shell cocotb-config --makefiles)/Makefile.sim
