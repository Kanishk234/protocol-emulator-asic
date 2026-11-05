"""Make native Tcl errors fatal across OpenROAD's Python string-eval boundary."""


def checked(design, command):
    script = ('if {[catch {' + command + '} tripwire_tcl_error]} '
              '{list TRIPWIRE_TCL_ERROR $tripwire_tcl_error} '
              'else {list TRIPWIRE_TCL_OK}')
    result = str(design.evalTclString(script))
    if result != 'TRIPWIRE_TCL_OK':
        raise RuntimeError(f'Native Tcl failed: {command}: {result}')


def placement_command(distance):
    if type(distance) is not int or distance <= 0:
        raise ValueError('Expected positive integer displacement in microns')
    return f'detailed_placement -max_displacement {{{distance} {distance}}}'
