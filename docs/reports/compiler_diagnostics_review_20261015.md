# Compiler diagnostics review

Capacity/placement/routing diagnostics and failed-build report/image cleanup
remain covered by their existing regression fixtures. The fresh hosted nine
design-set seed builds in38777137439 passed independently; those are existing
compiler evidence, not validation of later CLI edits.

The review found a separate CLI parser defect: bare identifiers made solely of
hexadecimal letters entered `int(value,0)` and raised an uncaught ValueError.
Malformed integer-like values could also traceback or reach compilation with
the wrong type. The repaired parser accepts signed decimal and prefixed
binary/octal/hex integers with underscores; leading-zero unprefixed decimal
uses base10. It preserves ordinary strings and Verilog literals/expressions.
Malformed integer-like input reports `compile: error:` before starting tools.

Focused tests cover actual main() argument handling, captured parameter types,
malformed rejection before compile_design, and existing repeated --set groups.
The specialist agent reached its usage limit after preparing code/tests; the
coordinator reviewed and independently verified them. Hosted validation of
the final source remains required. No capacity increase, protocol behavior,
silicon or bitstream-format change is claimed.
