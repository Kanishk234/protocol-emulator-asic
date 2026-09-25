"""Pin-unit configuration registers (ARCHITECTURE.md §7.2, spec `pin_config`, D-036).

encode(cfg) packs a PinConfig into the unit's host words; decode(words) unpacks them.
Chip.pin_config round-trips every configuration through these words, so the model only
runs values the hardware registers can hold (times in 16.8 clocks, the sample offset as a
fixed 16.8 offset rather than a fraction).
"""

import dataclasses

import tripwire_spec as S

from .pinunit import PinConfig

PAD_NONE = 31


def _code(name, kind, value, cfg):
    if kind == "bool":
        return int(bool(value))
    if kind == "uint":
        return 0 if value is None else int(value)
    if kind == "m1":
        return int(value) - 1
    if kind == "pad":
        return PAD_NONE if value is None else int(value)
    if kind == "enum":
        vals = S.PIN_CFG_ENUMS[name]
        key = "none" if value is None else value
        if key not in vals:
            raise ValueError(f"{name} = {value!r}: not one of {sorted(map(str, vals))}")
        return vals[key]
    if kind == "q8":
        return round(value * 256)
    if kind == "sofs":
        return round(value * cfg.period_q8)
    raise ValueError(kind)


def _value(name, kind, code, fields):
    if kind == "bool":
        return bool(code)
    if kind == "uint":
        return None if name == "rx_nbits" and code == 0 else code
    if kind == "m1":
        return code + 1
    if kind == "pad":
        return None if code == PAD_NONE else code
    if kind == "enum":
        key = {v: k for k, v in S.PIN_CFG_ENUMS[name].items()}[code]
        return None if key == "none" else key
    if kind == "q8":
        return code / 256
    if kind == "sofs":
        return code / round(fields["period"] * 256)
    raise ValueError(kind)


def encode(cfg: PinConfig) -> list:
    """The unit's block of host words; ValueError if a value does not fit its field."""
    words = [0] * S.PIN_CFG_STRIDE
    for name, (bit, width, kind) in S.PIN_CFG_FIELDS.items():
        code = _code(name, kind, getattr(cfg, name), cfg)
        if not 0 <= code < (1 << width):
            raise ValueError(f"pin config {name} = {getattr(cfg, name)!r} does not fit {width} bits")
        for i in range(width):
            if code >> i & 1:
                w, b = divmod(bit + i, 16)
                words[w] |= 1 << b
    return words


def decode(words) -> PinConfig:
    raw = {}
    for name, (bit, width, _) in S.PIN_CFG_FIELDS.items():
        raw[name] = sum(((words[(bit + i) // 16] >> ((bit + i) % 16)) & 1) << i for i in range(width))
    fields = {}
    for name in ("period",) + tuple(n for n in S.PIN_CFG_FIELDS if n != "period"):
        fields[name] = _value(name, S.PIN_CFG_FIELDS[name][2], raw[name], fields)
    return PinConfig(**fields)


def check_fields():
    """The register layout covers exactly the PinConfig fields (no silent model-only settings)."""
    model = {f.name for f in dataclasses.fields(PinConfig)}
    return model ^ set(S.PIN_CFG_FIELDS)
