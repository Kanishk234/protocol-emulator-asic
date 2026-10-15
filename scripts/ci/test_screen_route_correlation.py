"""Distinguish changed load topology from failures on unchanged connections."""
import unittest
from screen_route_correlation import compare

NL = 'sg13cmos5l_buf_1 driver (.A(in), .X(n));\nsg13cmos5l_buf_1 sink (.A(n), .X(out));'
DIODE = '\nsg13cmos5l_antennanp ant (.A(n));'


def layout(extra=''):
    return '\nNETS 1 ;\n- n ( driver X ) ( sink A ) ' + extra + ' ;\nEND NETS\n'


def report(kind='fanout'):
    totals = {'fanout': 0, 'slew': 0, 'cap': 0}
    totals[kind] = 1
    return 'slow\nmax ' + kind + '\ndriver/X 8 9 -1 (VIOLATED)\n===\n' + '\n'.join(
        f'max {k} violation count {v}' for k, v in totals.items())


class CorrelationTests(unittest.TestCase):
    def test_added_diode_is_topology_change(self):
        row = compare(NL, layout(), NL+DIODE, layout('( ant A )'), {'slow': report()})['nets'][0]
        self.assertEqual((row['before_loads'], row['after_loads']), (1, 2))
        self.assertEqual(row['added_diodes'], ['ant'])
        self.assertFalse(row['connectivity_unchanged'])

    def test_slew_with_unchanged_connections(self):
        row = compare(NL, layout(), NL, layout(), {'slow': report('slew')})['nets'][0]
        self.assertTrue(row['connectivity_unchanged'])
        self.assertEqual(row['added_diodes'], [])

    def test_rejects_logic_mutation(self):
        with self.assertRaises(ValueError):
            compare(NL, layout(), NL.replace('.A(n)', '.A(in)'), layout(), {'slow': report()})

    def test_rejects_added_non_diode_def_terminal(self):
        with self.assertRaises(ValueError):
            compare(NL, layout(), NL, layout('( sink X )'), {'slow': report()})

    def test_missing_report_is_not_a_pass(self):
        with self.assertRaises(ValueError):
            compare(NL, layout(), NL, layout(), {})


if __name__ == '__main__':
    unittest.main()
