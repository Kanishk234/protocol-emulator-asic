"""tripc: the TRIPWIRE compiler (v0). See compiler.py for the .trw language."""

from .compiler import TrwError, compile_file, compile_text  # noqa: F401
from .load import load  # noqa: F401
