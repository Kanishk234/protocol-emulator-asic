"""tripsim: TRIPWIRE token-level, cycle-accurate model (architecture model now, golden model later).

Independence rule (CLAUDE.md): written from docs/design/ARCHITECTURE.md and ISA.md only;
never read src/ while working on this package.
"""

from .chip import Chip, PAD_UI, PAD_UIO, PAD_UO  # noqa: F401
