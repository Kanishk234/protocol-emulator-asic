# Pinned independent PS/2 decoder

Unmodified decoder files from official libsigrokdecode revision
`71f451443029322d57376214c330b518efd84f88`. Source headers declare GPL-2.0-or-later;
the upstream GPL-3.0 COPYING text is retained, using the permitted later-version
option. Original copyright notices remain intact. PROVENANCE.json binds both
source files and the license to their hashes.

The installed 0.5 decoder waits for a twelfth falling edge before emitting an
eleven-bit device-to-host frame. This upstream revision completes the frame at
its actual final rising edge. It is used through sigrok-cli's decoder search
path for PS/2 subprocesses only. No local decoder edits or synthetic capture
edges are needed. It is a device-to-host decoder, not general bidirectional
host-to-device framing qualification.

This is an external verification tool, excluded from ASIC/FPGA sources. The
package does not import TRIPWIRE firmware, models or RTL. Other decoders continue
to use their installed packages; source/license identity is checked before use
and by the repository audit.
