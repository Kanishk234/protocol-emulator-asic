"""Reject corrupted mappings, including maps whose total bit count looks right."""

import unittest

from tools.fabric_audit.configmem import audit


HEADER = "frame_name,frame_index,bits_used_in_frame,used_bits_mask,ConfigBits_ranges\n"


class ConfigMemTests(unittest.TestCase):
    def check(self, rows, **kwargs):
        return audit(HEADER + rows, frame_width=4, frames=2, **kwargs)

    def test_padding_is_not_storage(self):
        # The metadata column says 4; only mask bits are actual configuration.
        result = self.check("F0,0,4,11_00,2;0\nF1,1,4,0010,1\n", expected_bits=3)
        self.assertEqual(result["mapped_config_bits"], 3)
        self.assertEqual(result["padding_bits"], 5)

    def test_descending_range_and_empty_frame(self):
        result = self.check("F0,0,4,1111,3:0\nF1,1,4,0000,NULL\n")
        self.assertEqual(result["mapped_config_bits"], 4)

    def test_ascending_range(self):
        result = self.check("F0,0,4,1111,0:3\nF1,1,4,0000,NULL\n")
        self.assertEqual(result["mapped_config_bits"], 4)

    def test_single_bit_and_reordered_frames(self):
        result = self.check("F1,1,4,0000,NULL\nF0,0,4,0001,0\n")
        self.assertEqual(result["per_frame"][0]["mapped_bits"], 1)

    def test_bad_mappings(self):
        cases = {
            "duplicate within frame": "F0,0,4,1100,0;0\nF1,1,4,0000,NULL\n",
            "duplicate across frames": "F0,0,4,1000,0\nF1,1,4,1000,0\n",
            "hole": "F0,0,4,1100,0;2\nF1,1,4,0000,NULL\n",
            "missing mapping": "F0,0,4,1100,0\nF1,1,4,0000,NULL\n",
            "NULL with used mask": "F0,0,4,1000,NULL\nF1,1,4,0000,NULL\n",
            "short mask": "F0,0,4,100,0\nF1,1,4,0000,NULL\n",
            "invalid mask": "F0,0,4,10x0,0\nF1,1,4,0000,NULL\n",
            "negative bit": "F0,0,4,1000,-1\nF1,1,4,0000,NULL\n",
            "duplicate frame": "F0,0,4,1000,0\nF1,0,4,0000,NULL\n",
            "out of range frame": "F0,2,4,1000,0\nF1,1,4,0000,NULL\n",
            "missing frame": "F0,0,4,1000,0\n",
        }
        for name, rows in cases.items():
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.check(rows)

    def test_expected_count_detects_missing_tail(self):
        with self.assertRaises(ValueError):
            self.check("F0,0,4,1100,0;1\nF1,1,4,0000,NULL\n", expected_bits=3)

    def test_invalid_dimensions(self):
        for width, frames in [(0, 1), (1, 0), (-1, 2)]:
            with self.subTest(width=width, frames=frames), self.assertRaises(ValueError):
                audit(HEADER, frame_width=width, frames=frames)


if __name__ == "__main__":
    unittest.main()
