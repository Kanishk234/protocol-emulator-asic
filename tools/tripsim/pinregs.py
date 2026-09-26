"""Pin-unit configuration registers (ARCHITECTURE.md §7.2, spec `pin_config`, D-036).

encode(cfg, unit) packs a PinConfig into the unit's host words; decode(words, unit) unpacks them.
Chip.pin_config round-trips every configuration through these words, so the model only
runs values the hardware registers can hold (times in 16.8 clocks, the sample offset as a
fixed 16.8 offset rather than a fraction).

Units differ (D-040): the fields of an optional feature (PULSE, carrier, BITSYNC) exist only
on the units that have it. On the other units they are not stored: encode leaves their bits
0, decode returns their defaults, and a configuration that uses a missing feature (a
non-default field, or one of its modes) is a ValueError.
"""

import dataclasses
import os

import tripwire_spec as S

from .pinunit import PinConfig

PAD_NONE = 31
# Exploration knob (phase 2 task 2.0): TRIPSIM_FRAC=4 rounds every time setting to 1/16 clock,
# as a 4-bit-fraction timer would. The encoding keeps its 8-bit fraction fields.
_QSTEP = 1 << (8 - int(os.environ.get("TRIPSIM_FRAC", "8")))
_DEFAULT = PinConfig()


def features(unit):
    """The optional features a unit has (all of them for a unit the spec does not list)."""
    if unit is None or unit >= len(S.PIN_UNIT_FEATURES):
        return tuple(S.PIN_FEATURES)
    return S.PIN_UNIT_FEATURES[unit]


def units_with(feature):
    return [u for u, fs in enumerate(S.PIN_UNIT_FEATURES) if feature in fs]


def _absent_fields(unit):
    have = features(unit)
    return {f for k, (fields, _) in S.PIN_FEATURES.items() if k not in have for f in fields}


def check_unit(cfg: PinConfig, unit):
    """ValueError if the configuration uses an optional feature the unit lacks (D-040)."""
    have = features(unit)
    for feat, (fields, modes) in S.PIN_FEATURES.items():
        if feat in have:
            continue
        used = [f for f in fields if getattr(cfg, f) != getattr(_DEFAULT, f)]
        used += [f"{f}={getattr(cfg, f)}" for f, ms in modes.items() if getattr(cfg, f) in ms]
        if used:
            where = ", ".join(f"U{u}" for u in units_with(feat))
            raise ValueError(f"U{unit} has no {feat.upper()} ({', '.join(used)}); only {where} do")


def _code(name, kind, value, cfg):
    if kind == "bool":
        return int(bool(value))
    if kind == "uint":
        return 0 if value is None else int(value)
    if kind == "m1":
        return int(value) - 1
    if kind == "pad":
        if value is not None and not 0 <= value <= 23:        # §14 P42: 24-30 are not pads
            raise ValueError(f"{name} = {value}: pads are 0..23 (or unset)")
        return PAD_NONE if value is None else int(value)
    if kind == "enum":
        vals = S.PIN_CFG_ENUMS[name]
        key = "none" if value is None else value
        if key not in vals:
            raise ValueError(f"{name} = {value!r}: not one of {sorted(map(str, vals))}")
        return vals[key]
    if kind == "q8":
        return round(value * 256 / _QSTEP) * _QSTEP
    if kind == "sofs":
        return round(value * cfg.period_q8 / _QSTEP) * _QSTEP
    raise ValueError(kind)


def _value(name, kind, code, fields):
    if kind == "bool":
        return bool(code)
    if kind == "uint":
        return None if name == "rx_nbits" and code == 0 else code
    if kind == "m1":
        return code + 1
    if kind == "pad":
        return None if code >= 24 else code                    # §14 P42: 24-30 act as 31
    if kind == "enum":
        names = {v: k for k, v in S.PIN_CFG_ENUMS[name].items()}
        key = names.get(code, names[0])                        # §14 P43: unnamed codes act as 0
        return None if key == "none" else key
    if kind == "q8":
        return code / 256
    if kind == "sofs":
        return code / round(fields["period"] * 256)
    raise ValueError(kind)


def encode(cfg: PinConfig, unit=None) -> list:
    """The unit's block of host words; ValueError if a value does not fit its field, or if the
    unit lacks a feature the configuration uses."""
    check_unit(cfg, unit)
    absent = _absent_fields(unit)
    words = [0] * S.PIN_CFG_STRIDE
    for name, (bit, width, kind) in S.PIN_CFG_FIELDS.items():
        if name in absent:
            continue                              # not stored on this unit
        code = _code(name, kind, getattr(cfg, name), cfg)
        if not 0 <= code < (1 << width):
            raise ValueError(f"pin config {name} = {getattr(cfg, name)!r} does not fit {width} bits")
        for i in range(width):
            if code >> i & 1:
                w, b = divmod(bit + i, 16)
                words[w] |= 1 << b
    return words


def decode(words, unit=None) -> PinConfig:
    absent = _absent_fields(unit)
    raw = {}
    for name, (bit, width, _) in S.PIN_CFG_FIELDS.items():
        raw[name] = sum(((words[(bit + i) // 16] >> ((bit + i) % 16)) & 1) << i for i in range(width))
    fields = {}
    for name in ("period",) + tuple(n for n in S.PIN_CFG_FIELDS if n != "period"):
        fields[name] = (getattr(_DEFAULT, name) if name in absent
                        else _value(name, S.PIN_CFG_FIELDS[name][2], raw[name], fields))
    return PinConfig(**fields)


def check_fields():
    """The register layout covers exactly the PinConfig fields (no silent model-only settings)."""
    model = {f.name for f in dataclasses.fields(PinConfig)}
    return model ^ set(S.PIN_CFG_FIELDS)
