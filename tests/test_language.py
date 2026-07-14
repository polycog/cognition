"""
Tests for language code
"""

from typing import Optional, cast

from enum import StrEnum, auto

import unittest

from pydantic import BaseModel

from cognition import (
    AutoDocEnum,
    DocEnum,
    EmpiricalConfidence,
    enum_description,
    enum_item_doc,
    enum_name_doc,
    enum_schema,
)

#


class Fruit(StrEnum):
    """Available fruits"""

    APPLE = auto()
    BANANA = auto()
    CHERRY = auto()


DOC_FRUIT: str = f"{Fruit.__name__} ({ Fruit.__doc__ })"
DOC_APPLE: str = Fruit.APPLE.value
DOC_BANANA: str = Fruit.BANANA.value
DOC_CHERRY: str = Fruit.CHERRY.value

DESC_FRUIT: str = (
    f"Enumeration: { DOC_FRUIT }"
    ", options...\n"
    f"* { DOC_APPLE }\n"
    f"* { DOC_BANANA }\n"
    f"* { DOC_CHERRY }"
)


class FruitSchema(BaseModel):
    """Response schema for Fruit"""

    value: Optional[Fruit]


class BinaryResponse(DocEnum):
    """Responding to a question with two possible responses"""

    YES = "yes", "Positive, for, true, 1"
    NO = "no", "Negative, against, false, 0"


DOC_BINARYRESPONSE: str = f"{BinaryResponse.__name__} ({ BinaryResponse.__doc__ })"
DOC_YES: str = f"{ BinaryResponse.YES.value } ({ BinaryResponse.YES.__doc__ })"
DOC_NO: str = f"{ BinaryResponse.NO.value } ({ BinaryResponse.NO.__doc__ })"

DESC_BINARYRESPONSE: str = (
    f"Enumeration: { DOC_BINARYRESPONSE }"
    ", options...\n"
    f"* { DOC_YES }\n"
    f"* { DOC_NO }"
)


class BinaryResponseSchema(BaseModel):
    """Response schema for BinaryResponse with custom name"""

    yn: Optional[BinaryResponse]


class UserRole(AutoDocEnum):
    """System access type for a computer account"""

    ADMIN = "Administrator with full system access"
    STANDARD = "Regular user"
    GUEST = "Temporary account with limited access"


DOC_USERROLE: str = f"{UserRole.__name__} ({ UserRole.__doc__ })"
DOC_ADMIN: str = f"{ UserRole.ADMIN.value } ({ UserRole.ADMIN.__doc__ })"
DOC_STANDARD: str = f"{ UserRole.STANDARD.value } ({ UserRole.STANDARD.__doc__ })"
DOC_GUEST: str = f"{ UserRole.GUEST.value } ({ UserRole.GUEST.__doc__ })"

DESC_USERROLE: str = (
    f"Enumeration: { DOC_USERROLE }"
    ", options...\n"
    f"* { DOC_ADMIN }\n"
    f"* { DOC_STANDARD }\n"
    f"* { DOC_GUEST }"
)


class UserRoleSchema(BaseModel):
    """Response schema for UserRole"""

    value: Optional[UserRole]


def _base_model_info(t: type[BaseModel]) -> dict[str, type]:
    return {k: cast(type, v.annotation) for k, v in t.model_fields.items()}


class TestLanguage(unittest.TestCase):
    """Tests for language code"""

    def test_empirical_confidence(self) -> None:
        """Tests for empirical confidence"""

        self.assertAlmostEqual(float(EmpiricalConfidence(1, 1)), 1.0)
        self.assertAlmostEqual(float(EmpiricalConfidence(1, 2)), 0.5)
        self.assertAlmostEqual(float(EmpiricalConfidence(3, 4)), 0.75)

    def test_enum_schema(self) -> None:
        """Tests for enum schema"""

        self.assertDictEqual(
            _base_model_info(enum_schema(Fruit)), _base_model_info(FruitSchema)
        )

        self.assertDictEqual(
            _base_model_info(enum_schema(BinaryResponse, field_name="yn")),
            _base_model_info(BinaryResponseSchema),
        )

        self.assertDictEqual(
            _base_model_info(enum_schema(UserRole)), _base_model_info(UserRoleSchema)
        )

    def test_enum_description(self) -> None:
        """Tests for enum description"""

        self.assertEqual(enum_name_doc(Fruit), DOC_FRUIT)
        self.assertEqual(enum_item_doc(Fruit.APPLE), DOC_APPLE)
        self.assertEqual(enum_item_doc(Fruit.BANANA), DOC_BANANA)
        self.assertEqual(enum_item_doc(Fruit.CHERRY), DOC_CHERRY)

        self.assertEqual(enum_name_doc(BinaryResponse), DOC_BINARYRESPONSE)
        self.assertEqual(enum_item_doc(BinaryResponse.YES), DOC_YES)
        self.assertEqual(enum_item_doc(BinaryResponse.NO), DOC_NO)

        self.assertEqual(enum_name_doc(UserRole), DOC_USERROLE)
        self.assertEqual(enum_item_doc(UserRole.ADMIN), DOC_ADMIN)
        self.assertEqual(enum_item_doc(UserRole.STANDARD), DOC_STANDARD)
        self.assertEqual(enum_item_doc(UserRole.GUEST), DOC_GUEST)

        self.assertEqual(enum_description(Fruit), DESC_FRUIT)
        self.assertEqual(enum_description(BinaryResponse), DESC_BINARYRESPONSE)
        self.assertEqual(enum_description(UserRole), DESC_USERROLE)
