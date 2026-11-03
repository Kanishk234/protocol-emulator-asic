# Protected endpoint feasibility probe

This tiny circuit tests preservation of a kept buffer–diode–buffer relay through the unchanged stock Classic flow. It is not the TRIPWIRE candidate or an official GDS run. A counter provides clocked load; the relay maps ui_in[1] to uo_out[0]. The main checkout hardware is not edited: CI copies this probe only into its ephemeral checkout.

The manual protected-endpoint-feasibility workflow runs two cases with identical probe RTL: native RSZ_DONT_TOUCH_RX disabled/enabled. Both use the existing pinned TT tools, installer and stock LibreLane image digest. The enabled case must retain the two exact buffers and diode on one node and must exercise native protection in four repair stages. The disabled case records connectivity without requiring its destruction. If both survive without meaningful repair pressure, that limits the conclusion.

Each case runs stock Classic through STAMidPNR-3 and a fresh read-only native antenna check. Uploaded native timing/electrical/antenna reports are measurements,not acceptance of this toy or the full design. No detailed routing,extraction,signoff or full protocol replay. A green job establishes only flow completion and the stated connectivity checks. Native resizer protections do not establish fixed placement or guaranteed antenna immunity.

The relay adds two propagation delays and protects its own buffer input,not the existing full-design NAND/delay inputs. Any eventual integration requires a general primitive,full functional verification,actual diode-to-gate evidence and unchanged final full-design screen/signoff gates. No technology-wrapper adoption is authorized by this feasibility result alone.
