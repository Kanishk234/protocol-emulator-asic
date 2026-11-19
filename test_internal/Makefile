# Run inside the project venv. Long lockstep/mutation runs remain explicit.
.PHONY: all l1 chip peer l2 injections
all: l1 chip peer
l1:
	@set -e; for suite in chan alu lane slots pins host; do $(MAKE) -C $$suite; done
	$(MAKE) -C pin FULL=0
	$(MAKE) -C pin FULL=1
chip:
	PYTHONPATH=../tools python -m capture_replay --fetch
	$(MAKE) -C chip COCOTB_TEST_MODULES=test_chip,test_l3,test_rot,test_phase3,test_ack_path,test_spi_flash,test_onewire_overdrive,test_ps2_framing,test_uart_bridge,test_capture_replay,test_metamorphic_tap,test_metamorphic_loop,test_metamorphic_perm
peer:
	$(MAKE) -C i2c_peer
l2:
	$(MAKE) -C l2 L2_CYCLES=1000000
injections:
	cd .. && python test_internal/l2/run_injections.py
