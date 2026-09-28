# pyuvm (UVM in Python) environment for the shell: constrained-random host transactions checked
# against tools/refmodels/shell.py, with functional coverage (test_shell_uvm.py). White-box.
#   make                          # default length (UVM_ITEMS=60 sessions)
#   make RANDOM_SEED=123 UVM_ITEMS=200
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
ROOT = $(CURDIR)/../..
SRC = $(ROOT)/src
VERILOG_SOURCES = $(addprefix $(SRC)/,wp_shell.v wp_spi_target.v wp_sync.v wp_crc32.v wp_fifo.v)
COMPILE_ARGS += -Pwp_shell.ARCH_VERSION=3 -I$(SRC)
TOPLEVEL = wp_shell
COCOTB_TEST_MODULES = test_shell_uvm
export UVM_ITEMS ?= 60
export WARP_ARCH_VERSION = 3

include $(shell cocotb-config --makefiles)/Makefile.sim
