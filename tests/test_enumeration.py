"""
Tests for enumeration code
"""

import unittest

from cognition import AutoDocEnum, DocEnum, EnumDispatch

#

_HI_VAL = "howdy"
_HI_DOC = "greeting"

_BYE_VAL = "have a good one"
_BYE_DOC = "close"

_OTHER_VAL = "?"


class DocPhrase(DocEnum):
    """Phrase types"""

    SALUTATION = _HI_VAL, _HI_DOC
    VALEDICTION = _BYE_VAL, _BYE_DOC
    OTHER = _OTHER_VAL


class AutoDocPhrase(AutoDocEnum):
    """Phrase types"""

    SALUTATION = _HI_DOC
    VALEDICTION = _BYE_DOC


class PhraseDispatch(EnumDispatch[DocPhrase]):
    """Example dispatch"""

    def salutation(self) -> str:
        """simple hi"""

        return "👋"

    def valediction(self, num: int) -> str:
        """simple bye"""

        return num * "✌️"


class TestEnumeration(unittest.TestCase):
    """Tests for enumeration code"""

    def test_doc(self) -> None:
        """
        Documented enums
        """

        self.assertEqual(DocPhrase.SALUTATION.value, _HI_VAL)
        self.assertEqual(DocPhrase.SALUTATION.__doc__, _HI_DOC)

        self.assertEqual(DocPhrase.VALEDICTION.value, _BYE_VAL)
        self.assertEqual(DocPhrase.VALEDICTION.__doc__, _BYE_DOC)

        self.assertEqual(DocPhrase.OTHER.value, _OTHER_VAL)
        self.assertIsNone(DocPhrase.OTHER.__doc__)

    def test_autodoc(self) -> None:
        """
        Documented auto-valued enums
        """

        self.assertEqual(AutoDocPhrase.SALUTATION.value, 1)
        self.assertEqual(AutoDocPhrase.SALUTATION.__doc__, _HI_DOC)

        self.assertEqual(AutoDocPhrase.VALEDICTION.value, 2)
        self.assertEqual(AutoDocPhrase.VALEDICTION.__doc__, _BYE_DOC)

    def test_dispatch(self) -> None:
        """
        Method dispatch via enum
        """

        o = PhraseDispatch()

        self.assertEqual(o(DocPhrase.SALUTATION), o.salutation())
        self.assertEqual(o(DocPhrase.VALEDICTION, 3), o.valediction(3))
        self.assertIsNone(o(DocPhrase.OTHER))
