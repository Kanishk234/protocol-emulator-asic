# Configured timing edge observations

Source: [44393291255](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/44393291255),
commit `2872eedf12756d30999eebc360c298078ff2476c`.
The workflow completed successfully; its result explicitly rejects the candidate
and retains `timing_acceptance=false` and `physical_acceptance=false`.

The existing X2Y3 LD_I1 selector is observed as S=0 in the control and S=1 in
the candidate. OpenSTA reports A1→X disabled by constant in the control and
A0→X disabled by constant in the candidate. At the south I/O mux, S0=S1=0;
only A0→X remains enabled among its data inputs. The tool applies the changed
selector and prunes the corresponding unselected data edges. Failure to apply
that selector is therefore not an explanation for this experiment's result.
This does not prove that all configured edges in the design are correct.

All reported endpoint values remain identical between control and candidate.
Six endpoints remain sensitive to static versus dynamic loop handling. Worst
cell-only setup slack remains +1.508933 ns. No candidate image was loaded.

For primitive endpoint X2Y2/_2158_/D, static loop handling chooses launch register
X1Y3/_1736_; dynamic handling chooses input Tile_X2Y4_B_OUT_top. The authenticated
primary testbench connects that port to `h_wvalid`, a real host input. Removing
it from analysis would discard an exercised interface. Both reports eventually
pass through X2Y3 combinational logic into the primitive. The changed startpoint
shows why examining only one unused local input was insufficient; it does not
by itself establish which loop or timing treatment is responsible.

The next timing investigation must follow the active reconvergent paths and
preserve host input coverage. Binary truth-table independence alone does not
justify ignoring delay or hazards. No timing exceptions were added.

In parallel, [44394572610](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/44394572610)
starts D124 detailed routing of the other 25 frozen leaf contexts. Primitive1
has a separate repeated control in run 44394572275. Their results must be checked
individually before any aggregate routing claim. Full fabric/shell assembly and
extracted timing remain outstanding regardless of leaf-router success.
