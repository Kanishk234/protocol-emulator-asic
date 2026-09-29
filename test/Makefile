# Makefile
# See https://docs.cocotb.org/en/stable/quickstart.html for more info

# defaults
SIM ?= icarus
FST ?= -fst # Use more efficient FST format
TOPLEVEL_LANG ?= verilog
SRC_DIR = $(PWD)/../src
PROJECT_SOURCES = tt_um_warp.v wp_small_fabric.v wp_small_validated_reload.v wp_small_image_validator.v wp_reload_guard.v fabric_gen/Config_access.v fabric_gen/ConfigFSM.v fabric_gen/eFPGA_top.v fabric_gen/eFPGA.v fabric_gen/Frame_Data_Reg.v fabric_gen/Frame_Select.v fabric_gen/IO_1_bidirectional_frame_config_pass.v fabric_gen/LUT4AB_ConfigMem.v fabric_gen/LUT4AB_switch_matrix.v fabric_gen/LUT4AB.v fabric_gen/LUT4c_frame_config_dffesr.v fabric_gen/models_pack.v fabric_gen/MUX8LUT_frame_config_mux.v fabric_gen/N_term_single_switch_matrix.v fabric_gen/N_term_single.v fabric_gen/S_term_single_switch_matrix.v fabric_gen/S_term_single.v fabric_gen/W_IO_ConfigMem.v fabric_gen/W_IO_switch_matrix.v fabric_gen/W_IO.v

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

# Allow sharing configuration between design and testbench via `include`:
COMPILE_ARGS 		+= -I$(SRC_DIR)

# Include the testbench sources:
VERILOG_SOURCES += $(PWD)/tb.v
TOPLEVEL = tb

# List test modules to run, separated by commas and without the .py suffix:
COCOTB_TEST_MODULES = test

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim
