SIM ?= icarus
TOPLEVEL_LANG ?= verilog
ROOT := $(abspath ../../..)
UART_PRIMS ?= 1
I2C_PRIMS ?= 0
VERILOG_SOURCES = $(wildcard $(ROOT)/protocols/uart/*.v) $(ROOT)/protocols/i2c_ctrl/i2c_ctrl_top.v $(ROOT)/protocols/uart_i2c/uart_i2c_top.v
VERILOG_SOURCES += $(ROOT)/tools/compile/prims/warp_prims_sim.v $(ROOT)/arch/prims/wp_timer.v $(ROOT)/arch/prims/wp_shift.v
COMPILE_ARGS += -Puart_i2c_top.DIV=16 -Puart_i2c_top.Q=4 -Puart_i2c_top.UART_PRIMS=$(UART_PRIMS) -Puart_i2c_top.I2C_PRIMS=$(I2C_PRIMS)
SIM_BUILD = sim_build/system12_u$(UART_PRIMS)_i$(I2C_PRIMS)
TOPLEVEL = uart_i2c_top
COCOTB_TEST_MODULES = test_uart_i2c
export PYTHONPATH := $(ROOT)/tools:$(ROOT)/protocols/uart_spi/test:$(PYTHONPATH)
include $(shell cocotb-config --makefiles)/Makefile.sim
