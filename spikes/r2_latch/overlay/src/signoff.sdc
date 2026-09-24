# TRIPWIRE R2 (branch spike/r2-latch, DECISIONS D-032): constraints for sign-off STA.
# Exactly LibreLane's default. It is set explicitly because, without SIGNOFF_SDC_FILE, sign-off
# would reuse PNR_SDC_FILE (pnr.sdc) and lose the latch setup check.
source $::env(SCRIPTS_DIR)/base.sdc
