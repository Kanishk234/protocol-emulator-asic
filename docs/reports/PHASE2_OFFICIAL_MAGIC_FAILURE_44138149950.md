# Official full-design run44138149950: SRAM signoff checker failure

The unchanged official GDS job ran3h41m57s and failed only the deferred
57923MagicDRC/10illegal-overlap errors. Precheck, GL and viewer did not execute.
Detailed route finishes0DRC, antenna0, LVS matches, final setup/hold checkers and
max-slew/max-cap checkers pass. Independent final three-corner electrical-report
inspection confirms no reported violations. This is not an official green run.

The routed ODB357f0136..., routed NL1eb51e9e..., and final post-fill NL537f41ad...
are byte-identical to route/extraction44031468510 and22-case replay44123392388.
The official run therefore reproduced the proven physical checkpoint, rather than
introducing a new timing/routing regression. Final hold fast/typical/slow remains
+0.150773287/+0.391302668/+0.742154359ns. Ordinary setupWS0is retained; the prior
positive functional reserve is separate evidence on the matching physical design.

Merged GDS SHA256ddf9668fc20eba68fc936f408bdeee3446ba0dd026c8cf8b99ee8b0e12d5f9fb.
All57923Magic text-report boxes lie inside SRAM boundsx12..248.8/y40..231.34um:
NW.d229, subcell-abut376, Cnt.c21, layer-overlap25944, M2-area30720,
SRAM-contact39, tie-extension594. Magic's XML conversion loses the21Cnt.c entries
because two rules share the same category; use the full text inventory, not its
incomplete XML count. All10feedback boxes are obsm4-metal4 inside the macro,
at the supply-column interruption near y186..192um. This spatial inventory alone
does not prove that actual GDS geometry passes DRC.

Historical R3/R4 reports identify the same57923macro baseline and10abstract
power-stripe overlaps. The competition-linked primary SRAM walkthrough documents
Magic limitations and explicitly uses merged-GDS KLayout DRC instead:
https://kdp1965.github.io/ihp-um-janestreet-prism/ihp_sram_macro.html#
Its checker waivers have NOT been copied into main. The pre-launch readiness
review missed this known compatibility blocker; passing OpenROAD route DRC was
insufficient to qualify Magic signoff.

Next diagnostic: separate manual gds-official-macro-signoff-audit on this exact
archived GDS, using pinned LibreLane3.1.0.dev4/Ciel89d42ee and stock CMOS5L deck.
It performs no synthesis, placement, routing or physical repair; requires fresh
KLayout DRC0and unchanged GDS hash; retains Magic counts and official_signoff=false.
Main source/config and every official workflow remain unchanged. Five admission
regressions, actual artifact admission and workflow shell/YAML checks pass.

Only after the actual geometry result can we propose a precise SRAM-aware
signoff policy or fix real geometry. No failed check will be silently disabled,
no thresholds relaxed, and no Phase2exit box ticked. A subsequent official run,
precheck/GL/viewer and required main CI remain required.
