# RTL tests for the UART user design (cocotb + Icarus).
#   make                      DIV=16, fixed divisor
#   make DIV=13               odd divisor
#   make RUNTIME_DIV=1        divisor loaded at run time
#   make PRIMS=1              on the WARP hard primitives (fixed divisor)
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
DIV ?= 16
RUNTIME_DIV ?= 0
PRIMS ?= 0

SRC = $(PWD)/..
ROOT = $(PWD)/../../..
VERILOG_SOURCES = $(wildcard $(SRC)/*.v)
VERILOG_SOURCES += $(ROOT)/tools/compile/prims/warp_prims_sim.v $(ROOT)/arch/prims/wp_timer.v $(ROOT)/arch/prims/wp_shift.v
COMPILE_ARGS += -Puart_top.DIV=$(DIV) -Puart_top.RUNTIME_DIV=$(RUNTIME_DIV) -Puart_top.PRIMS=$(PRIMS)
SIM_BUILD = sim_build/div$(DIV)_rt$(RUNTIME_DIV)_p$(PRIMS)

TOPLEVEL = uart_top
COCOTB_TEST_MODULES = test_uart
export PYTHONPATH := $(PWD)/../../../tools:$(PYTHONPATH)
export DIV RUNTIME_DIV PRIMS

include $(shell cocotb-config --makefiles)/Makefile.sim
