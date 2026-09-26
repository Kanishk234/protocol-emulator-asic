# RTL tests for the SPI controller user design (cocotb + Icarus).
#   make MODE=0..3 [HALF=4]
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
MODE ?= 0
HALF ?= 4
CPOL := $(shell echo $$(( $(MODE) / 2 )))
CPHA := $(shell echo $$(( $(MODE) % 2 )))

SRC = $(PWD)/..
VERILOG_SOURCES = $(SRC)/spi_ctrl_top.v
COMPILE_ARGS += -Pspi_ctrl_top.CPOL=$(CPOL) -Pspi_ctrl_top.CPHA=$(CPHA) -Pspi_ctrl_top.HALF=$(HALF)
SIM_BUILD = sim_build/mode$(MODE)_half$(HALF)

TOPLEVEL = spi_ctrl_top
COCOTB_TEST_MODULES = test_spi_ctrl
export PYTHONPATH := $(PWD)/../../../tools:$(PYTHONPATH)
export CPOL CPHA HALF

include $(shell cocotb-config --makefiles)/Makefile.sim
