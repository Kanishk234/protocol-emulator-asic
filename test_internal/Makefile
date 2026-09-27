# White-box tests (CLAUDE.md: tests in test/ touch only top-level ports; these may look inside).
# G1 hard primitives against the Python reference models.
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
ARCH_DIR = $(CURDIR)/../arch
VERILOG_SOURCES = $(ARCH_DIR)/prims/wp_timer.v $(ARCH_DIR)/prims/wp_shift.v $(CURDIR)/tb_prims.v
COCOTB_TOPLEVEL = tb_prims
COCOTB_TEST_MODULES = test_prims
SIM_BUILD = sim_build
include $(shell cocotb-config --makefiles)/Makefile.sim
