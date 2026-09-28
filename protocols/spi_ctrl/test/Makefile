# RTL tests for the SPI controller user design (cocotb + Icarus).
#   make MODE=0..3 [HALF=4] [PRIMS=1]     PRIMS=1: on the WARP hard primitives
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
MODE ?= 0
HALF ?= 4
PRIMS ?= 0
CPOL := $(shell echo $$(( $(MODE) / 2 )))
CPHA := $(shell echo $$(( $(MODE) % 2 )))

SRC = $(PWD)/..
ROOT = $(PWD)/../../..
VERILOG_SOURCES = $(SRC)/spi_ctrl_top.v
VERILOG_SOURCES += $(ROOT)/tools/compile/prims/warp_prims_sim.v $(ROOT)/arch/prims/wp_timer.v $(ROOT)/arch/prims/wp_shift.v
COMPILE_ARGS += -Pspi_ctrl_top.CPOL=$(CPOL) -Pspi_ctrl_top.CPHA=$(CPHA) -Pspi_ctrl_top.HALF=$(HALF) -Pspi_ctrl_top.PRIMS=$(PRIMS)
SIM_BUILD = sim_build/mode$(MODE)_half$(HALF)_p$(PRIMS)

TOPLEVEL = spi_ctrl_top
COCOTB_TEST_MODULES = test_spi_ctrl
export PYTHONPATH := $(PWD)/../../../tools:$(PYTHONPATH)
export CPOL CPHA HALF PRIMS

include $(shell cocotb-config --makefiles)/Makefile.sim
