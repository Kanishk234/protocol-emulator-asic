# Makefile
# See https://docs.cocotb.org/en/stable/quickstart.html for more info

# defaults
SIM ?= icarus
FST ?= -fst # Use more efficient FST format
TOPLEVEL_LANG ?= verilog
SRC_DIR = $(PWD)/../src
PROJECT_SOURCES = tt_um_warp.v wp_fabric_cfg.v wp_shell.v wp_spi_target.v wp_sync.v wp_crc32.v wp_fifo.v fabric_gen/ConfigFSM.v fabric_gen/Frame_Data_Reg.v fabric_gen/Frame_Select.v

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
# WARP (BUGS #1): the flip-flop primitives (ihp_dff_r, ...) live in a separate UDP file; the template omits it
VERILOG_SOURCES += $(PDK_ROOT)/ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/verilog/sg13cmos5l_udp.v

# this gets copied in by the GDS action workflow
VERILOG_SOURCES += $(PWD)/gate_level_netlist.v

endif

# WARP (D-019, D-022): the fabric macro model. The macro is not in info.yaml source_files /
# PROJECT_SOURCES (it is the MACROS entry in src/config.json), so the tests add it here:
#   gl   (GATES=yes, CI gl_test): the hardened macro's gate-level netlists (macro/warp_tiny)
#   rtl  (WARP_FABRIC=rtl):       the generated fabric RTL + the pinned tile library's primitives
#   stub (default, CI test job):  the port-only black box src/warp_tiny.v; bitstream tests skip
MACRO_DIR = $(PWD)/../macro/warp_tiny
ifeq ($(GATES),yes)
WARP_FABRIC = gl
else
WARP_FABRIC ?= stub
endif
ifeq ($(WARP_FABRIC),gl)
VERILOG_SOURCES += $(MACRO_DIR)/warp_tiny.nl.v $(wildcard $(MACRO_DIR)/tiles/*.nl.v)
else ifeq ($(WARP_FABRIC),rtl)
WARP_TILES ?= $(shell $(PWD)/../scripts/fetch_tiles.sh)
VERILOG_SOURCES += $(MACRO_DIR)/warp_tiny.v $(wildcard $(MACRO_DIR)/rtl/*.v) $(WARP_TILES)/models_pack.v
VERILOG_SOURCES += $(foreach p,FABULOUS_LC IOBUF GBUF SYS_RESET,$(WARP_TILES)/primitives/$(p)/fabulous/$(p).v)
COMPILE_ARGS += -DWARP_FABRIC_RTL
else
VERILOG_SOURCES += $(SRC_DIR)/warp_tiny.v
endif
export WARP_FABRIC

# Allow sharing configuration between design and testbench via `include`:
COMPILE_ARGS 		+= -I$(SRC_DIR)

# Include the testbench sources:
VERILOG_SOURCES += $(PWD)/tb.v
TOPLEVEL = tb

# List test modules to run, separated by commas and without the .py suffix:
COCOTB_TEST_MODULES = test,test_bitstream

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim
