"""Protocol kernels for tripsim.

The firmware itself now lives in programs/*.trw and is built by tripc; each module here
loads its program into a chip and keeps its original Python-assembled slots only as a
reference (tools/tripc/tests checks the compiled images are bit-identical to them).
"""

import pathlib

PROGRAMS = pathlib.Path(__file__).resolve().parents[2] / "programs"


def load_program(chip, name, **params):
    """Compile programs/<name>.trw with the given params and load it into `chip`."""
    import tripc
    image, _ = tripc.compile_file(PROGRAMS / f"{name}.trw", params)
    tripc.load(chip, image)
    return image
