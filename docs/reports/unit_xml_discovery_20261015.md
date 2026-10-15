# Strict XML UART discovery correction, October 15

Unit run38777137520 at77edd2dfdc12184a9b69c98cfa5041e9137ac016 fails
its first UART matrix entry after successful package setup and shell random
transactions. The tools pytest job passes. The actual failing command reports
`check_xml.py: error: XML contains failures, errors or skipped tests`.
UART's fixed-divisor design intentionally cannot run `test_runtime_divisor`;
the original decorator registered it with `skip=not RUNTIME_DIV`.

The strict checker is correct to reject skipped evidence. Pinned cocotb2.0.1
does not solve this with `COCOTB_TEST_FILTER`: local installed
`cocotb/regression.py::_record_test_excluded` also writes a testcase with a
skipped element for an excluded test. `_init.py` applies the regex to the
test's full name, and the Icarus Makefile forwards the variable, but those
facts do not remove the excluded XML entry. No filter workaround is retained.

The corrected UART module defines the same runtime-divisor coroutine and
registers it with `cocotb.test()` only when `RUNTIME_DIV` is enabled. Fixed
variants discover seven applicable cases; the runtime variant discovers all
eight. The workflow keeps strict failure/error/skip rejection and now requires
at least seven/eight executed cases respectively. No RTL, model, runtime test
body or expected behavior changes. All eight protocol-suite test directories
were searched; the UART runtime case was the only conditional skip decorator.

Local validation imports the actual test module using the project's pinned
cocotb package, with `RUNTIME_DIV=0` then1, and counts objects of its real
`cocotb._decorators.Test` type, the discovery mechanism used by its regression manager.
The observed counts are7/8, every registered case has `skip=False`, and the
runtime case is registered only in the second import. This is discovery
validation without local EDA, not a hosted matrix pass. Actual corrected
hosted simulation is still required.

Separately, autonomy observer38777137622 passes all63 supervisor checks and
its exact-revision read-only observation/artifact-upload steps on77edd2d.
That workflow's success does not convert the unit failure to success.
