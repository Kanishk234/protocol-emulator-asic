# L1-HOST tests (white-box): the host SPI protocol and register map (D-046) through the input synchronisers.
# Run inside the project venv (source .venv/bin/activate): make
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
SRC_DIR ?= $(PWD)/../../src

VERILOG_SOURCES = $(SRC_DIR)/trw_sync.v $(SRC_DIR)/trw_spi.v $(SRC_DIR)/trw_host.v $(SRC_DIR)/trw_pins.v \
                  $(SRC_DIR)/trw_chan_prod.v $(PWD)/tb_host.v
COMPILE_ARGS += -I$(SRC_DIR)
TOPLEVEL = tb_host
COCOTB_TEST_MODULES ?= test_host

include $(shell cocotb-config --makefiles)/Makefile.sim
