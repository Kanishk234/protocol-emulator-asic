# Documentation map

Start with [How it works](HOW_IT_WORKS.md), then the [qualified baseline](BASELINE.md).

| Purpose | Source |
|---|---|
| Hardware contract | [Architecture](design/ARCHITECTURE.md) |
| Instructions and encodings | [ISA](design/ISA.md), `spec/tripwire.yaml` |
| Verification layers | [Verification](design/VERIFICATION.md) |
| Build and physical flow | [Physical design and CI](design/PHYSICAL_DESIGN_AND_CI.md) |
| Current evidence | [Phase 2 result](reports/PHASE2_OFFICIAL_GREEN_44189196098.md), [warnings](reports/PHASE2_WARNING_REVIEW_44189196098.md) |
| Protocol evidence and limits | [Support matrix](PROTOCOL_SUPPORT.md) |
| Phase 3 progress | [Summary](summaries/PHASE3.md), [I2C memory milestone](reports/PHASE3_I2C_MEMORY.md), [independent peer](reports/PHASE3_I2C_PEER.md), [firmware recovery guard](reports/PHASE3_I2C_GUARD.md) |
| Upcoming work | [Phase 3 plan](design/phases/PHASE3_SHOWCASE_PROTOCOLS.md) |
| Compiler reaction analysis | [Local selection guarantees and limits](reports/PHASE3_REACTION_SELECTION.md) |
| Decisions and bugs | [Decisions](DECISIONS.md), [bugs](BUGS.md) |
| Recent sessions | [Worklog](WORKLOG.md) |
| Old timing experiments | [Frozen archive](archive/README.md) |

The architecture and YAML define the current contract. Historical estimates, experiment results and dated decision discussions do not override it. The phase checklists are the completion gates; no Phase 3 task is marked complete by repository cleanup.
