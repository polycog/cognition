"""
Tests for utility code
"""

import unittest
from collections.abc import Iterable
from typing import Annotated, Any, List, Set, cast  # ruff: ignore[UP035]

from cognition import (
    AttrReferral,
    MutableWrapper,
    TypedMixin,
    is_list,
    is_set,
    optionally_name,
    stringify,
    timed,
)

# ===


class TestUtility(unittest.TestCase):
    """Tests for utility code"""

    def test_typecheck(self) -> None:
        """Confirming is_list/set"""

        bad_both: Iterable[Any] = (
            "howdy",
            (1, 2, 3),
            float,
            frozenset({"a", "b", "c"}),
            dict[str, int],
        )

        # ===

        good_list: Iterable[object] = (
            list[int],
            list,
            type([] + ["a"]),
            List,  # ruff: ignore[UP006]
            List[str],  # ruff: ignore[UP006]
            Annotated[list[float], "costs"],
        )

        for bad in bad_both:
            self.assertFalse(is_list(bad))
            self.assertFalse(is_list(type(bad)))

        for gl in good_list:
            gl = cast(type[Any], gl)
            self.assertTrue(is_list(gl))

        # ===

        good_set: Iterable[object] = (
            set[int],
            set,
            type({"a"} | {"a", "b"}),
            Set,  # ruff: ignore[UP006]
            Set[str],  # ruff: ignore[UP006]
            Annotated[set[float], "rational"],
        )

        for bad in bad_both:
            self.assertFalse(is_set(bad))
            self.assertFalse(is_set(type(bad)))

        for gs in good_set:
            gs = cast(type[Any], gs)
            self.assertTrue(is_set(gs))

    def test_typed(self) -> None:
        """Confirming typed classes"""

        # pylint: disable=too-few-public-methods
        class _Foo(TypedMixin): ...

        test_foo = _Foo()
        self.assertEqual(test_foo.type, "_Foo")

    def test_timed(self) -> None:
        """Confirming @timed"""

        @timed
        def _inc(x: int) -> int:
            return x + 1

        result1, time1 = _inc(42)  # pylint: disable=unpacking-non-sequence
        self.assertEqual(result1, 43)
        self.assertGreater(time1, 0)

        result2, time2 = _inc(51)  # pylint: disable=unpacking-non-sequence
        self.assertEqual(result2, 52)
        self.assertGreater(time2, 0)

    def test_mutable_wrapper(self) -> None:
        """Confirming MutableWrapper"""

        start = "start"
        end = "end"

        r1 = MutableWrapper(start)
        r2 = r1

        self.assertEqual(r1.value, start)
        self.assertEqual(r2.value, start)
        self.assertEqual(str(r1), start)
        self.assertEqual(repr(r1), f"{ type(r1).__name__ }({ start !r })")

        r2.value = end

        self.assertEqual(r1.value, end)
        self.assertEqual(r2.value, end)
        self.assertEqual(str(r2), end)
        self.assertEqual(repr(r2), f"{ type(r1).__name__ }({ end !r })")

    def test_optionally_name(self) -> None:
        """Confirming optionally_name"""

        func_name: str = "test"

        def double(x: int) -> int:
            """double trouble"""

            return 2 * x

        f1 = optionally_name(double, func_name)
        f2 = optionally_name(double, None)

        self.assertNotEqual(str(double), str(f1))

        self.assertEqual(str(f1), func_name)

        self.assertEqual(str(f2), str(double))

    def test_stringify(self) -> None:
        """Confirming stringify"""

        func_name: str = "test"

        @stringify(func_name)
        def not_named_the_same() -> None:
            """nothin' but a function"""
            print("bar")

        self.assertEqual(str(not_named_the_same), func_name)

    def test_attrreferral_bad(self) -> None:
        """Confirming AttrReferral read-only"""

        a_start = 1
        b_start = "bee"

        src = {
            "a": a_start,
            "b": b_start,
        }

        obj = AttrReferral(src)
        view = AttrReferral.view(obj)

        # should not be able to access
        # a key not in the source
        self.assertFalse(hasattr(obj, "c"))
        self.assertFalse("c" in view)
        with self.assertRaises(AttributeError):
            _ = obj.c

        # should not be able to change
        # the source
        with self.assertRaises(AttributeError):
            obj.a += 1

        self.assertEqual(src["a"], a_start)
        self.assertEqual(src["b"], b_start)

    def test_attrreferral_good(self) -> None:
        """Testing AttrReferral golden path"""

        src = {"a": 1, "b": "bee"}

        obj = AttrReferral(src)
        view = AttrReferral.view(obj)

        # ===

        self.assertTrue(hasattr(obj, "a"))
        self.assertTrue("a" in view)
        self.assertEqual(obj.a, src["a"])
        self.assertEqual(view["a"], src["a"])

        self.assertTrue(hasattr(obj, "b"))
        self.assertTrue("b" in view)
        self.assertEqual(obj.b, src["b"])
        self.assertEqual(view["b"], src["b"])

        self.assertFalse(hasattr(obj, "c"))
        self.assertFalse("c" in view)

        self.assertDictEqual(src, dict(view))
        self.assertEqual(str(obj), f"AttrReferral({src})")

        # ===

        src["a"] = cast(int, src["a"]) + 1
        src["c"] = 3.14

        self.assertTrue(hasattr(obj, "a"))
        self.assertTrue("a" in view)
        self.assertEqual(obj.a, src["a"])
        self.assertEqual(view["a"], src["a"])

        self.assertTrue(hasattr(obj, "b"))
        self.assertTrue("b" in view)
        self.assertEqual(obj.b, src["b"])
        self.assertEqual(view["b"], src["b"])

        self.assertTrue(hasattr(obj, "c"))
        self.assertTrue("c" in view)
        self.assertAlmostEqual(obj.c, src["c"])
        self.assertAlmostEqual(view["c"], src["c"])

        self.assertDictEqual(src, dict(view))
        self.assertEqual(str(obj), f"AttrReferral({src})")
