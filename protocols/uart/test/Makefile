# RTL tests for the UART user design (cocotb + Icarus).
#   make                      DIV=16, fixed divisor
#   make DIV=13               odd divisor
#   make RUNTIME_DIV=1        divisor loaded at run time
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
DIV ?= 16
RUNTIME_DIV ?= 0

SRC = $(PWD)/..
VERILOG_SOURCES = $(SRC)/uart_tx.v $(SRC)/uart_rx.v $(SRC)/uart_top.v
COMPILE_ARGS += -Puart_top.DIV=$(DIV) -Puart_top.RUNTIME_DIV=$(RUNTIME_DIV)
SIM_BUILD = sim_build/div$(DIV)_rt$(RUNTIME_DIV)

TOPLEVEL = uart_top
COCOTB_TEST_MODULES = test_uart
export PYTHONPATH := $(PWD)/../../../tools:$(PYTHONPATH)
export DIV RUNTIME_DIV

include $(shell cocotb-config --makefiles)/Makefile.sim
