SIM ?= icarus
TOPLEVEL_LANG ?= verilog
STAMP_SHIFT ?= 0
ROOT := $(abspath ../../..)
VERILOG_SOURCES = $(ROOT)/protocols/uart_capture/uart_capture_top.v
VERILOG_SOURCES += $(wildcard $(ROOT)/protocols/uart/*.v)
VERILOG_SOURCES += $(ROOT)/tools/compile/prims/warp_prims_sim.v $(ROOT)/arch/prims/wp_timer.v $(ROOT)/arch/prims/wp_shift.v
COMPILE_ARGS += -Puart_capture_top.STAMP_BITS=6 -Puart_capture_top.STAMP_SHIFT=$(STAMP_SHIFT)
SIM_BUILD = sim_build/shift$(STAMP_SHIFT)
TOPLEVEL = uart_capture_top
COCOTB_TEST_MODULES = test_queue
export STAMP_SHIFT
include $(shell cocotb-config --makefiles)/Makefile.sim
