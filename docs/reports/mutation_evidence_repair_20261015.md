# Controlled mutation evidence repair

The historical local campaign remains in `mutation.md`. Its runner treated
any command failure as a killed mutant, so that mechanism did not distinguish
an actual behavioral rejection from a missing tool or harness failure.
No assertion is made that the historical detections were all invalid.

The repaired runner establishes a pristine control for each distinct command
before planting any mutation. The same exact applicable tests must execute
for the control and mutant. Known excluded/idle-fabric cases are explicitly
listed rather than counted as executed. Missing or malformed XML, unexpected
case names, required skips, error elements, contradictory counters/outcomes,
tool/import exceptions and timeouts are errors, never kills. Simulation kills
require expected executed failures plus assertion evidence; formal kills
require FAIL status and an actual engine assertion-failure witness. An
infrastructure error in any control blocks its associated mutants.

Each command runs in a fresh throwaway copy with a bounded process group.
The result records source commit and workflow identity. Campaign output goes
to ignored `build/mutation/`, with a source-specific JSON and report; it no
longer merges stale subset results or overwrites the historical report.
The new hosted workflow retains control/mutant logs, XML and formal witnesses
without uploading whole repository copies. Actual hosted outcomes are pending;
fixtures alone do not establish that all eleven defects are detected.

The specialist agent reached its usage limit after preparing the patch. The
coordinator reviewed it, added mixed setup/assertion and contradictory-outcome
rejections, and independently ran its fixtures alongside compiler/route checks
(77PASS/2SKIP, skipped Tcl unavailable). No local simulation/formal run occurred.
