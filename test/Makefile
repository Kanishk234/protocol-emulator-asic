# Makefile
# See https://docs.cocotb.org/en/stable/quickstart.html for more info

# defaults
SIM ?= icarus
FST ?= -fst # Use more efficient FST format
TOPLEVEL_LANG ?= verilog
SRC_DIR = $(PWD)/../src
PROJECT_SOURCES = tt_um_tripwire.v trw_chip.v trw_sync.v trw_fabric.v trw_chan_port.v trw_chan_prod.v trw_host.v trw_spi.v trw_lane.v trw_alu.v trw_slots.v trw_sram.v trw_pin_cfg.v trw_pin_io.v trw_pin_tx.v trw_pin_rx.v trw_pin_bs.v trw_pin_unit.v trw_pins.v

MACRO_DIR = $(abspath $(SRC_DIR)/../macro/RM_IHPSG13_1P_512x16_c2_bm_bist)
MACRO_MODELS = $(MACRO_DIR)/RM_IHPSG13_1P_core_behavioral_bm_bist.v $(MACRO_DIR)/RM_IHPSG13_1P_512x16_c2_bm_bist.v
VERILOG_SOURCES += $(MACRO_MODELS)

ifneq ($(GATES),yes)

# RTL simulation:
SIM_BUILD				= sim_build/rtl
VERILOG_SOURCES += $(addprefix $(SRC_DIR)/,$(PROJECT_SOURCES))

else

# Gate level simulation:
SIM_BUILD				= sim_build/gl
COMPILE_ARGS    += -DGL_TEST
COMPILE_ARGS    += -DFUNCTIONAL
COMPILE_ARGS    += -DSIM
VERILOG_SOURCES += $(PDK_ROOT)/ihp-sg13cmos5l/libs.ref/sg13cmos5l_io/verilog/sg13cmos5l_io.v
VERILOG_SOURCES += $(PDK_ROOT)/ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/verilog/sg13cmos5l_stdcell.v
# TRIPWIRE (BUGS #1): the flip-flop primitives (ihp_dff_r, ...) live in a separate UDP file; the template omits it
VERILOG_SOURCES += $(PDK_ROOT)/ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/verilog/sg13cmos5l_udp.v

# this gets copied in by the GDS action workflow
VERILOG_SOURCES += $(PWD)/gate_level_netlist.v

endif

# Allow sharing configuration between design and testbench via `include`:
COMPILE_ARGS 		+= -I$(SRC_DIR) -DFUNCTIONAL

# Include the testbench sources:
VERILOG_SOURCES += $(PWD)/tb.v
TOPLEVEL = tb

# List test modules to run, separated by commas and without the .py suffix:
COCOTB_TEST_MODULES = test

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim
