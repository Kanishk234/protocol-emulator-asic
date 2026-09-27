# Chip-level tests (test_internal/chip): trw_chip through its pins, with the SRAM macro's behavioural model.
# Run inside the project venv (source .venv/bin/activate): make
# The macro model is fetched once into the cache by spikes/r3_sram/fetch_macro.sh (as the R3/R4 checks do).
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
SRC_DIR ?= $(PWD)/../../src
PDK_REV ?= 2bbec755dc67ca3db0261c3d6163e15735d66710
MACRO_DIR ?= $(HOME)/.cache/tripwire/macro-$(PDK_REV)/RM_IHPSG13_1P_512x16_c2_bm_bist

CHIP_SOURCES = trw_chip.v trw_sync.v trw_fabric.v trw_chan_port.v trw_chan_prod.v trw_host.v trw_spi.v \
               trw_lane.v trw_alu.v trw_slots.v trw_sram.v trw_pin_cfg.v trw_pin_io.v trw_pin_tx.v \
               trw_pin_rx.v trw_pin_unit.v trw_pins.v
MACRO_MODELS = $(MACRO_DIR)/RM_IHPSG13_1P_core_behavioral_bm_bist.v $(MACRO_DIR)/RM_IHPSG13_1P_512x16_c2_bm_bist.v
ifneq ($(GATES),yes)
# RTL
SIM_BUILD = sim_build/rtl
VERILOG_SOURCES = $(addprefix $(SRC_DIR)/,$(CHIP_SOURCES)) $(MACRO_MODELS) $(PWD)/tb_chip.v
COMPILE_ARGS += -I$(SRC_DIR) -DFUNCTIONAL
else
# Gate level: the Yosys netlist from synth/chip/run_chip.sh and the cmos5l cell models (with the UDP file,
# BUGS #1). Run with Tiny Tapeout's Icarus 13 (ICARUS_BIN_DIR=...), as scripts/gl_local.sh does.
SIM_BUILD = sim_build/gl
PDK_ROOT ?= $(HOME)/.cache/tripwire/pdk-$(PDK_REV)
CELLS = $(PDK_ROOT)/ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/verilog
VERILOG_SOURCES = $(CELLS)/sg13cmos5l_stdcell.v $(CELLS)/sg13cmos5l_udp.v $(MACRO_MODELS) \
                  $(PWD)/../../synth/chip/build/net.v $(PWD)/tb_chip.v
COMPILE_ARGS += -DFUNCTIONAL -DGL_TEST -DSIM
COCOTB_RESULTS_FILE = results_gl.xml
endif
TOPLEVEL = tb_chip
COCOTB_TEST_MODULES ?= test_chip

include $(shell cocotb-config --makefiles)/Makefile.sim
