"""Boundary incidence for cell-free leaves; does not replace DRC or GDS LVS."""


def wire_boundary_connected(term):
    net = term.getNet()
    if net is None:
        return False
    if net.getSigType() in ('POWER', 'GROUND'):
        return bool(net.getSWires()) and any(pin.getBoxes() for pin in term.getBPins())
    return len(net.getBTerms()) > 1 and net.getWire() is not None
