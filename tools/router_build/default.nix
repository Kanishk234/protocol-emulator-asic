# WARP D099: preserve the existing pinned FABulous toolchain and override only
# OpenROAD's explicitly attributed experimental patch. Source stays unedited.
{ force ? true }:
let
  upstream = builtins.getFlake ("path:" + toString ../../build/router_toolchain);
  stock = upstream.legacyPackages.x86_64-linux.openroad;
in
assert stock.src.rev == "dcf36133a369abc8f3c5e5738cd4d82e4903c0e0";
if !force then stock else stock.overrideAttrs (old: {
  pname = "openroad-warp-force-review";
  patches = (old.patches or []) ++ [ ../../patches/openroad_force_reroute.patch ];
})
