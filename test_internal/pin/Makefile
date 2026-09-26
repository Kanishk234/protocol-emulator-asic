# L1 pin-unit tests (white-box): make [FULL=0|1] [MODULE=test_pin_tx,test_pin_rx]
# Run inside the project venv (source .venv/bin/activate).
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
FULL ?= 0
FRAC ?= 8
SRC_DIR ?= $(PWD)/../../src
SIM_BUILD = sim_build/full$(FULL)_frac$(FRAC)

VERILOG_SOURCES = $(SRC_DIR)/trw_pin_cfg.v $(SRC_DIR)/trw_pin_io.v $(SRC_DIR)/trw_pin_tx.v \
                  $(SRC_DIR)/trw_pin_rx.v $(SRC_DIR)/trw_pin_unit.v $(PWD)/tb_pin.v
COMPILE_ARGS += -I$(SRC_DIR) -Ptb_pin.FULL=$(FULL) -Ptb_pin.FRAC=$(FRAC)
TOPLEVEL = tb_pin
COCOTB_TEST_MODULES ?= test_pin_tx,test_pin_rx
COCOTB_RESULTS_FILE = results_full$(FULL)_frac$(FRAC).xml

include $(shell cocotb-config --makefiles)/Makefile.sim
