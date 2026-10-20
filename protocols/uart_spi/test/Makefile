SIM ?= icarus
TOPLEVEL_LANG ?= verilog
ROOT := $(abspath ../../..)
UART_PRIMS ?= 1
SPI_PRIMS ?= 0
CPOL ?= 0
CPHA ?= 0
VERILOG_SOURCES = $(wildcard $(ROOT)/protocols/uart/*.v) $(ROOT)/protocols/spi_ctrl/spi_ctrl_top.v $(ROOT)/protocols/uart_spi/uart_spi_top.v
VERILOG_SOURCES += $(ROOT)/tools/compile/prims/warp_prims_sim.v $(ROOT)/arch/prims/wp_timer.v $(ROOT)/arch/prims/wp_shift.v
COMPILE_ARGS += -Puart_spi_top.DIV=16 -Puart_spi_top.HALF=4 -Puart_spi_top.UART_PRIMS=$(UART_PRIMS) -Puart_spi_top.SPI_PRIMS=$(SPI_PRIMS) -Puart_spi_top.CPOL=$(CPOL) -Puart_spi_top.CPHA=$(CPHA)
SIM_BUILD = sim_build/system12_u$(UART_PRIMS)_s$(SPI_PRIMS)_m$(CPOL)$(CPHA)
TOPLEVEL = uart_spi_top
COCOTB_TEST_MODULES = test_uart_spi
export CPOL CPHA
include $(shell cocotb-config --makefiles)/Makefile.sim
