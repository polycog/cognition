"""
Tests for utility code
"""

from typing import cast

import unittest

from cognition import (
    AttrReferral,
    optionally_name,
    stringify,
)

#

class TestUtility(unittest.TestCase):
    """Tests for utility code"""

    def test_optionally_name(self) -> None:
        """Confirming optionally_name"""

        func_name: str = "test"

        def double(x: int) -> int:
            """double trouble"""

            return 2 * x

        f1 = optionally_name(double, func_name)
        f2 = optionally_name(double, None)

        self.assertNotEqual(
            str(double),
            str(f1)
        )

        self.assertEqual(
            str(f1),
            func_name
        )

        self.assertEqual(
            str(f2),
            str(double)
        )


    def test_stringify(self) -> None:
        """Confirming stringify"""

        func_name: str = "test"

        @stringify(func_name)
        def not_named_the_same() -> None:
            """nothin' but a function"""
            print("bar")

        self.assertEqual(
            str(not_named_the_same),
            func_name
        )


    def test_attrreferral_bad(self) -> None:
        """Confirming AttrReferral read-only"""

        a_start = 1
        b_start = 'bee'

        src = {
            'a': a_start,
            'b': b_start,
        }

        obj = AttrReferral(src)

        # should not be able to access
        # a key not in the source
        self.assertFalse(hasattr(obj, 'c'))
        with self.assertRaises(AttributeError):
            _ = obj.c

        # should not be able to change
        # the source
        with self.assertRaises(AttributeError):
            obj.a += 1

        self.assertEqual(src['a'], a_start)
        self.assertEqual(src['b'], b_start)


    def test_attrreferral_good(self) -> None:
        """Testing AttrReferral golden path"""

        src = {
            'a': 1,
            'b': 'bee'
        }

        obj = AttrReferral(src)

        #

        self.assertTrue(hasattr(obj, 'a'))
        self.assertEqual(
            obj.a,
            src['a']
        )

        self.assertTrue(hasattr(obj, 'b'))
        self.assertEqual(
            obj.b,
            src['b']
        )

        self.assertFalse(hasattr(obj, 'c'))

        #

        src['a'] = cast(int, src['a']) + 1
        src['c'] = 3.14

        self.assertTrue(hasattr(obj, 'a'))
        self.assertEqual(
            obj.a,
            src['a']
        )

        self.assertTrue(hasattr(obj, 'b'))
        self.assertEqual(
            obj.b,
            src['b']
        )

        self.assertTrue(hasattr(obj, 'c'))
        self.assertAlmostEqual(
            obj.c,
            src['c']
        )
