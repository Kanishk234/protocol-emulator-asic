# Run inside the project venv. Long lockstep/mutation runs remain explicit.
.PHONY: all l1 chip l2 injections
all: l1 chip
l1:
	@set -e; for suite in chan alu lane slots pins host; do $(MAKE) -C $$suite; done
	$(MAKE) -C pin FULL=0
	$(MAKE) -C pin FULL=1
chip:
	$(MAKE) -C chip COCOTB_TEST_MODULES=test_chip,test_l3,test_rot
l2:
	$(MAKE) -C l2 L2_CYCLES=1000000
injections:
	cd .. && python test_internal/l2/run_injections.py
