# Independent native terminal parser review — October 19

Reviewed `tools/autonomy/native_terminals.py` and its focused tests against
terminal observer patch
`5ec2f809d784e5d81e59a1470bef566423f7a35cb1aea573564b35734396393b`
and pinned OpenROAD `dcf36133a369abc8f3c5e5738cd4d82e4903c0e0` source.
No concrete blocker remains for bounded actual-export qualification. No parser,
test or runtime source was edited, and no EDA/build/dispatch was performed.

## Corrected clock finding

An earlier independent reviewer caught a real source-semantics error before this
review: native FrNet `isClock` is built from the database signal type CLOCK,
whereas GlobalRouter `Net::isClockNet` caches a distinct nonleaf-clock
classification. Equating them would reject valid leaf-clock exports. The current
parser correctly compares raw native clock to `DATABASE_NET.clock` and preserves
`GLOBAL_NET.clock` without asserting equality. The regression exercises both
leaf and nonleaf GlobalRouter flags while requiring the database/raw signal-type
join. The false-rejection issue is resolved in the reviewed source.

## Source and structural checks

Exact contract headers, LF completion/encoding, bounded canonical integer
fields, layer indexing/levels/directions, sorted unique database IDs/names and
GlobalRouter map membership are checked. Database/native slot references must
match the complete native slot inventory, including empty slots. Global and
native counts, ordered physical/native pins, layer intervals, driver indices,
tree counts, member-parent references, node references and completion totals are
validated before they can become a supported join. All common raw-resource and
terminal-export fields are cross-checked, including exact grid geometry, names,
IDs, driver, native pins and tree census.

`_trunc` reproduces C++ signed division toward zero. Physical coordinates,
connection-layer clamp, original source eligibility (including y=−1), exact
membership lists, ordered deduplication and first-unique driver updates are
replayed against native observations. A duplicate later driver does not override
the existing root; a new unique driver does. Native root starts0 as in
`GlobalRouter::findFastRoutePins`. Missing native membership or unresolved
physical IDs remain explicit unsupported observations rather than invented
identity. Parent collectors must still provide authenticated live source/input
provenance; names/IDs inside two supplied files alone do not prove their origin.

`RSMT.cpp:122–129` maps terminal nodes by successive occurrences of each x/y
position through `FrNet::getPinIdxFromPosition`. The parser reproduces that rule,
including colocated pins on different layers, rather than joining by x/y alone.
Node-to-pin −1 and incomplete maps remain unsupported. Alias indices outside
bounds remain unsupported; valid aliases must refer to the same coordinate.
Via-range min/max/count is independently recomputed from all native pins at the
node, preserving no-match sentinels32767/−1. Terminal alias layer sentinels,
unsupported tree-access state and merged membership cannot silently pass the
join gate. Pinless Steiner ranges and nonterminal edge-ID sentinels are not
misinterpreted as missing physical terminal access.

The supported gate is conservative: any unresolved/sentinel/coverage/merged or
out-of-map membership observation leaves `model_gate=FAIL`, with named reasons.
That is a diagnostic outcome, not a malformed-file success or a physical access
proof. All reports retain native input authentication, physical acceptance and
timing acceptance false. Database physical-term counts and GlobalRouter pin
counts are compared; missing coverage is disclosed, not repaired by assuming a
subset is complete. Physical via templates, enclosure/spacing/OBS rules and a
verified whole-chip solver graph remain outside this module.

## Independent validation

Executed in the project venv:

```sh
PYTHONPATH=tools pytest -q tools/autonomy/tests/test_native_terminals.py
```

**56 passed in 0.15 s**, no skips. Fixtures cover duplicate/new driver rules,
coordinate/clamp/eligibility arithmetic, exact raw cross-joins, colocated
multilayer occurrence ordering, aliases/sentinels, unsupported local/merged/
missing coverage, malformed fields/counts/completion and the corrected leaf-clock
classification distinction. No actual native export was parsed as part of this
source/test review; the selected hosted result remains the next evidence gate.

Reviewed SHA256:

- Parser: `8a1ac5554686dc40e97548c5a86fe5f10b4304dffeea45fe1015c915481f1b62`.
- Tests: `7d28815d54cf384ef8299090d969c049155a26b1f9fa1bb5b4a434a37072bcd8`.

The underlying raw corridor parser still requires its authenticated in-bounds
pin-grid contract. The terminal observer preserves broader source eligibility;
that does not enlarge the accepted solver graph or justify silently normalizing
out-of-grid terminals. Actual121 raw pins already passed the earlier native
accounting contract; future changed checkpoints require their own review.
