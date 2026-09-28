# Co-simulation: the UART as a bitstream on the chip's fabric (RTL fabric model) against the
# UART's source RTL, in one Icarus simulation (test_cosim.py). White-box test (it instantiates the
# source RTL next to the chip), so it lives in test_internal/.
#   make
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
ROOT = $(CURDIR)/../..
SRC = $(ROOT)/src
FABRIC := $(shell cat $(ROOT)/arch/CURRENT)
MACRO_DIR = $(ROOT)/macro/$(FABRIC)
WARP_TILES ?= $(shell $(ROOT)/scripts/fetch_tiles.sh)

PROJECT_SOURCES = tt_um_warp.v wp_fabric_cfg.v wp_shell.v wp_spi_target.v wp_sync.v wp_crc32.v wp_fifo.v wp_frame_select.v fabric_gen/ConfigFSM.v fabric_gen/Frame_Data_Reg.v
VERILOG_SOURCES = $(addprefix $(SRC)/,$(PROJECT_SOURCES))
VERILOG_SOURCES += $(MACRO_DIR)/$(FABRIC).v $(wildcard $(MACRO_DIR)/rtl/*.v) $(WARP_TILES)/models_pack.v
VERILOG_SOURCES += $(foreach p,FABULOUS_LC IOBUF GBUF SYS_RESET,$(WARP_TILES)/primitives/$(p)/fabulous/$(p).v)
VERILOG_SOURCES += $(wildcard $(ROOT)/arch/prims/*.v)
VERILOG_SOURCES += $(ROOT)/protocols/uart/uart_top.v $(ROOT)/protocols/uart/uart_tx.v $(ROOT)/protocols/uart/uart_rx.v
VERILOG_SOURCES += $(ROOT)/protocols/uart/uart_tx_p.v $(ROOT)/protocols/uart/uart_rx_p.v
VERILOG_SOURCES += $(ROOT)/tools/compile/prims/warp_prims_sim.v
VERILOG_SOURCES += $(CURDIR)/tb.v
COMPILE_ARGS += -DWARP_FABRIC_RTL -I$(SRC) -I$(ROOT)/test

TOPLEVEL = tb
COCOTB_TEST_MODULES = test_cosim
export PYTHONPATH := $(ROOT)/tools:$(ROOT)/test:$(PYTHONPATH)
export WARP_FABRIC = rtl

include $(shell cocotb-config --makefiles)/Makefile.sim
