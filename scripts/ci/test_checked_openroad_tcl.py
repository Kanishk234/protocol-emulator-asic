import os
from pathlib import Path
import subprocess

import pytest

from checked_openroad_tcl import checked, placement_command


@pytest.mark.parametrize('result', [None, '', 'TRIPWIRE_TCL_ERROR {placement failed}'])
def test_non_success_eval_result_is_fatal(result):
    class Design:
        def evalTclString(self, script): return result
    with pytest.raises(RuntimeError, match='Native Tcl failed'):
        checked(Design(), 'check_placement -verbose')


@pytest.mark.parametrize('command,ok', [(placement_command(20), True),
    ('detailed_placement -max_displacement 20 20', False),
    ('check_placement -verbose', False)])
def test_real_tcl_preserves_list_and_propagates_caught_errors(tmp_path, command, ok):
    class Design:
        def evalTclString(self, script):
            # The API may return an error as text rather than raise. Execute
            # catch/list handling in Tcl, including the original malformed call.
            preamble = r'''
proc detailed_placement {args} {
    if {[llength $args] != 2 || [lindex $args 0] ne "-max_displacement"} {
        error "detailed_placement positional arguments not supported"
    }
    if {[llength [lindex $args 1]] != 2} {error "Expected displacement pair"}
    return
}
proc check_placement {args} {error "overlap check failed"}
'''
            path = tmp_path / 'eval.tcl'
            path.write_text(preamble + '\nset result [' + script + ']\nputs "TRW_RESULT:$result"\n')
            result = subprocess.run([os.environ.get('TRIPWIRE_TCLSH', 'tclsh'), str(path)],
                                    capture_output=True, text=True, check=True)
            return result.stdout.split('TRW_RESULT:', 1)[1].strip()
    if ok:
        checked(Design(), command)
    else:
        with pytest.raises(RuntimeError, match='Native Tcl failed'):
            checked(Design(), command)


@pytest.mark.parametrize('distance', [0, -1, 0.5, True])
def test_invalid_displacement_rejects(distance):
    with pytest.raises(ValueError): placement_command(distance)
