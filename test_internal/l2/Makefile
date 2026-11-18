# Long model/RTL lockstep for one explicitly selected RTL candidate.
# Run from the project venv, for example:
#   source .venv/bin/activate
#   make -C test_internal/l2 SIM=verilator L2_CYCLES=1000000

SIM ?= verilator
TOPLEVEL_LANG = verilog
TOPLEVEL = tb_l2
COCOTB_TEST_MODULES = test_l2
RTL_DIR ?= $(abspath $(CURDIR)/../../src)
RTL_REV ?= $(shell git -C $(RTL_DIR) rev-parse HEAD)-working-tree
MACRO_DIR ?= $(abspath $(CURDIR)/../../macro/RM_IHPSG13_1P_512x16_c2_bm_bist)

RTL_FILES = tt_um_tripwire.v trw_chip.v trw_sync.v trw_fabric.v trw_chan_port.v trw_chan_prod.v \
            trw_host.v trw_spi.v trw_lane.v trw_alu.v trw_slots.v trw_sram.v trw_pin_cfg.v \
            trw_pin_io.v trw_pin_tx.v trw_pin_rx.v trw_pin_bs.v trw_pin_unit.v trw_pins.v
VERILOG_SOURCES = $(addprefix $(RTL_DIR)/,$(RTL_FILES)) \
                  $(MACRO_DIR)/RM_IHPSG13_1P_core_behavioral_bm_bist.v \
                  $(MACRO_DIR)/RM_IHPSG13_1P_512x16_c2_bm_bist.v $(CURDIR)/tb_l2.v
COMPILE_ARGS += -I$(RTL_DIR) -DFUNCTIONAL -DSIM_ASSERT
ifeq ($(SIM),verilator)
EXTRA_ARGS += --timing -Wno-fatal --public-flat-rw
endif
export RTL_DIR RTL_REV

include $(shell cocotb-config --makefiles)/Makefile.sim
