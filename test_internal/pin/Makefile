# L1 pin-unit tests (white-box): make [FULL=0|1] [MODULE=test_pin_tx,test_pin_rx]
# Run inside the project venv (source .venv/bin/activate).
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
FULL ?= 0
FRAC ?= 8
SRC_DIR ?= $(PWD)/../../src
# Keep the harness compatible with both the earlier and promoted interfaces.
CACHED_CARRIER ?= $(shell grep -Eq 'output[[:space:]]+wire.*carrier_active' $(SRC_DIR)/trw_pin_cfg.v && echo 1 || echo 0)
CACHED_SAMPLE_DELTA ?= $(shell grep -Eq 'output[[:space:]]+wire.*sample_delta' $(SRC_DIR)/trw_pin_cfg.v && echo 1 || echo 0)
ifeq ($(CACHED_CARRIER),1)
COMPILE_ARGS += -DTRIPWIRE_CACHED_CARRIER
endif
ifeq ($(CACHED_SAMPLE_DELTA),1)
COMPILE_ARGS += -DTRIPWIRE_SAMPLE_DELTA
endif
SIM_BUILD = sim_build/full$(FULL)_frac$(FRAC)

VERILOG_SOURCES = $(SRC_DIR)/trw_pin_cfg.v $(SRC_DIR)/trw_pin_io.v $(SRC_DIR)/trw_pin_tx.v \
                  $(SRC_DIR)/trw_pin_rx.v $(SRC_DIR)/trw_pin_bs.v $(SRC_DIR)/trw_pin_unit.v $(PWD)/tb_pin.v
COMPILE_ARGS += -I$(SRC_DIR) -DSIM_ASSERT
ifeq ($(SIM),verilator)
COMPILE_ARGS += -GFULL=$(FULL) -GFRAC=$(FRAC)
else
COMPILE_ARGS += -Ptb_pin.FULL=$(FULL) -Ptb_pin.FRAC=$(FRAC)
endif
TOPLEVEL = tb_pin
COCOTB_TEST_MODULES ?= test_pin_tx,test_pin_rx,test_pin_full,test_pin_bs,test_pin_bs_frame,test_pin_bs_tx,test_pin_bs_b3
export FULL
COCOTB_RESULTS_FILE = results_full$(FULL)_frac$(FRAC).xml

include $(shell cocotb-config --makefiles)/Makefile.sim
