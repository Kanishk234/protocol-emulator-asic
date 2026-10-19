# Frozen G1 physical and current gate-test refresh

[Run39280550500](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39280550500) at0165bef01b34e02420e79757c1cb0871f3a92402 succeeds in GDS, precheck, gl_test and viewer. This uses the existing unmodified template jobs. No hardware/spec/constraint change accompanies the run.

The independent phase5 review found that historical gate tests dynamically import tools/board/warp.py, which changed even though physical and direct test trees did not. This fresh run covers that current helper. The downloaded results.xml contains30 executed passing cases and zero failures/errors/skips; strict autonomy.check_xml accepts it. Those cases include board loader, board SPI examples and board I2C examples. SHA256 `9396e979816cd98b334604ddc50b3e9526909ac443f1a16fb07a2895d5f21c2a`.

Downloaded precheck results.md lists all nine checks passing: pin-label/drawing, SG13CMOS5L DRC, zero-area, KLayout checks, pin, boundary, layer, cell-name and analog-pin checks. SHA256 `110b9623329adb5831d80d501e191948194d39a4b640f24f43d3dd70857efedf`.

GitHub job wall durations: GDS21m51s, precheck5m36s, gl_test29m51s. End-to-end from GDSjobstart to gl_testcompletion51m45s; jobs overlap. These are hosted job elapsed times, not isolated router runtimes. Raw gate waveform/XML and precheck reports remain in CI artifacts and ignored build/gds111_gate and build/gds111_precheck.

Scope remains D023: hardened shell gate netlist with generated RTL-fabric simulation accommodation and real loaded images. This is not native configured full-chip gate/SDF timing, board operation, or compact-successor routing acceptance. Frozen G1 remains the baseline; compact best121 still has nonzero native overflow.
