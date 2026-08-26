"""
Tests for language code
"""

import unittest
from enum import StrEnum, auto
from typing import Any, Self, cast

from pydantic import BaseModel
from pydantic.fields import Field, FieldInfo
from pydantic_ai.messages import ModelResponse, TextPart
from pydantic_ai.models.function import FunctionModel

from cognition import (
    AutoDocEnum,
    DocEnum,
    EmpiricalConfidence,
    EnumClassifier,
    FactDescriber,
    Function,
    basemodel_dep_types,
    basemodel_description,
    basemodel_field_doc,
    basemodel_name_doc,
    enum_description,
    enum_item_doc,
    enum_name_doc,
    enum_schema,
)

# ===


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

    value: Fruit | None


DOC_FRUIT_SCHEMA: str = f"{FruitSchema.__name__} ({ FruitSchema.__doc__ })"
DOC_FRUIT_VALUE: str = "value (Fruit | NoneType)"

DESC_FRUIT_SCHEMA: str = (
    f"Base Model: { DOC_FRUIT_SCHEMA }"
    ", fields...\n"
    f"* { DOC_FRUIT_VALUE }\n"
    "\n"
    f"{DESC_FRUIT}"
)

DESC_FRUIT_PROMPT__FRUIT_TASK__A_BC: str = """== Context ==
Fruit Task

== Task Description ==
Your task is to provide a 1-sentence description of a supplied fact.

== Object to Describe ==
value=<Fruit.APPLE: 'apple'>

== Other Facts ==
value=<Fruit.BANANA: 'banana'>
value=<Fruit.CHERRY: 'cherry'>

== Structural Description ==
Base Model: FruitSchema (Response schema for Fruit), fields...
* value (Fruit | NoneType)

Enumeration: Fruit (Available fruits), options...
* apple
* banana
* cherry

== Guiding Style ==
* Do NOT use any markup or superfluous punctuation.
* Do NOT reproduce the object in your description, nor its type, nor explicitly refer to words like 'object', 'field', or 'attribute'.
* Limit factual knowledge to the object and its structural description.

== Example ==
Given the following structural description...

Base Model: EgOnTop (Represents spatial relations between blocks), fields...
* entity1 (EgBlock; block on top)
* entity2 (EgBlock | EgSurface; block or surface below the block)

Base Model: EgBlock (A block), fields...
* name (str; name of the block)
* color (EgColor; block color)

Base Model: EgSurface (A surface for blocks), fields...
* name (str; name of the surface)

Enumeration: EgColor (Example choice of colors), options...
* 1 (the color red)
* 2 (the color green)
* 3 (the color blue)

And the following additional known facts...

EgBlock(name=B1, color=EgColor.BLUE)
EgBlock(name=B2, color=EgColor.RED)
EgSurface(name=table)
EgOnTop(entity1=EgBlock(name=B1, color=EgColor.BLUE), entity2=EgBlock(name=B2, color=EgColor.RED))
EgOnTop(entity1=EgBlock(name=B2, color=EgColor.RED), entity2=EgSurface(name=table))

Good descriptions include...
* EgBlock(name=B1, color=EgColor.BLUE)
  There is a block named 'B1' that has the color 'blue'
* EgOnTop(entity1=EgBlock(name=B2, color=EgColor.RED), entity2=EgSurface(name=table))
  The red block named 'B2' is on top of the surface named 'table'"""


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

    yn: BinaryResponse | None


DOC_BINARYRESPONSE_SCHEMA: str = (
    f"{BinaryResponseSchema.__name__} ({ BinaryResponseSchema.__doc__ })"
)
DOC_BINARYRESPONSE_YN: str = "yn (BinaryResponse | NoneType)"

DESC_BINARYRESPONSE_SCHEMA: str = (
    f"Base Model: { DOC_BINARYRESPONSE_SCHEMA }"
    ", fields...\n"
    f"* { DOC_BINARYRESPONSE_YN }\n"
    "\n"
    f"{DESC_BINARYRESPONSE}"
)


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

    value: UserRole | None


DOC_USERROLE_SCHEMA: str = f"{UserRoleSchema.__name__} ({ UserRoleSchema.__doc__ })"
DOC_USERROLE_VALUE: str = "value (UserRole | NoneType)"

DESC_USERROLE_SCHEMA: str = (
    f"Base Model: { DOC_USERROLE_SCHEMA }"
    ", fields...\n"
    f"* { DOC_USERROLE_VALUE }\n"
    "\n"
    f"{DESC_USERROLE}"
)


class ComplexSchema(BaseModel):
    """Multiple pieces"""

    a: int = Field(description="apple")
    b: str | None
    c: list[str] = Field(description="annotation")
    e: BinaryResponse = Field(description="binary")
    q: FruitSchema | BinaryResponseSchema | UserRoleSchema = Field(
        description="ternary"
    )


DOC_COMPLEX_SCHEMA: str = f"{ComplexSchema.__name__} ({ ComplexSchema.__doc__ })"
DOC_COMPLEX_A: str = "a (int; apple)"
DOC_COMPLEX_B: str = "b (str | NoneType)"
DOC_COMPLEX_C: str = "c (list[str]; annotation)"
DOC_COMPLEX_E: str = "e (BinaryResponse; binary)"
DOC_COMPLEX_Q: str = "q (FruitSchema | BinaryResponseSchema | UserRoleSchema; ternary)"

DESC_COMPLEX_SCHEMA_SHALLOW: str = (
    f"Base Model: { DOC_COMPLEX_SCHEMA }"
    ", fields...\n"
    f"* { DOC_COMPLEX_A }\n"
    f"* { DOC_COMPLEX_B }\n"
    f"* { DOC_COMPLEX_C }\n"
    f"* { DOC_COMPLEX_E }\n"
    f"* { DOC_COMPLEX_Q }\n"
    "\n"
    f"{DESC_BINARYRESPONSE}\n"
    "\n"
    f"Base Model: { DOC_FRUIT_SCHEMA }"
    ", fields...\n"
    f"* { DOC_FRUIT_VALUE }\n"
    "\n"
    f"Base Model: { DOC_BINARYRESPONSE_SCHEMA }"
    ", fields...\n"
    f"* { DOC_BINARYRESPONSE_YN }\n"
    "\n"
    f"Base Model: { DOC_USERROLE_SCHEMA }"
    ", fields...\n"
    f"* { DOC_USERROLE_VALUE }"
)

DESC_COMPLEX_SCHEMA_DEEP: str = (
    f"{DESC_COMPLEX_SCHEMA_SHALLOW}\n\n{DESC_FRUIT}\n\n{DESC_USERROLE}"
)


def _base_model_info(t: type[BaseModel]) -> dict[str, type]:
    return {k: cast(type, v.annotation) for k, v in t.model_fields.items()}


# pylint: disable=too-few-public-methods
class CountingModelFunc:
    """
    Function that returns json
    based upon a function over
    the number of requests
    """

    def __init__(self, response_func: Function[int, BaseModel]) -> None:
        """
        :param response_func: function that indicates which data to return
                              based upon the request count
        """

        self._count = 0
        self._f = response_func
        self.__name__ = response_func.__name__

    def __call__(self, *args: Any, **kwargs: Any) -> ModelResponse:
        self._count += 1
        return ModelResponse(parts=(TextPart(self._f(self._count).model_dump_json()),))

    @classmethod
    def always(cls, data: BaseModel) -> Self:
        """
        Shorthand to produce the same response

        :param data: model to always return
        """

        return cls(lambda _: data)


class TestLanguage(unittest.IsolatedAsyncioTestCase):
    """Tests for language code (async for pydantic language agents)"""

    def test_enum_classification(self) -> None:
        """Tests for enum classification"""

        model_apple = FunctionModel(
            CountingModelFunc.always(FruitSchema(value=Fruit.APPLE)),
            model_name="always_apple",
        )
        model_first_none_then_banana = FunctionModel(
            CountingModelFunc(
                lambda ct: FruitSchema(value=Fruit.BANANA if ct != 1 else None),
            ),
            model_name="first_none_then_banana",
        )
        model_mod = FunctionModel(
            CountingModelFunc(
                lambda ct: FruitSchema(
                    value=(
                        None
                        if (_mod := ct % (len(Fruit) + 1)) == 0
                        else list(Fruit)[_mod - 1]
                    )
                )
            ),
            model_name="loops_through_options_and_none",
        )

        classifier = EnumClassifier(Fruit, "Interpreting a shopping list")
        num_trials = len(Fruit) + 2

        with self.assertRaises(ValueError):
            classifier("🧑‍💻", model_apple, num_trials=0)

        self.assertEqual(
            classifier("🧑‍💻", model_apple, num_trials=num_trials),
            (Fruit.APPLE, EmpiricalConfidence(num_trials, num_trials)),
        )

        self.assertEqual(
            EnumClassifier.classify(
                "🧑‍💻", Fruit, model_apple, "Interpreting a shopping list", num_trials
            ),
            (Fruit.APPLE, EmpiricalConfidence(num_trials, num_trials)),
        )

        self.assertEqual(
            classifier("🍌", model_first_none_then_banana, num_trials=num_trials),
            (Fruit.BANANA, EmpiricalConfidence(num_trials - 1, num_trials)),
        )

        # ruff: ignore[RUF015]
        self.assertEqual(
            classifier("make the doctor happy", model_mod, num_trials=num_trials),
            (list(Fruit)[0], EmpiricalConfidence(2, num_trials)),
        )

        # ===

        assume_guest = FunctionModel(
            CountingModelFunc.always(UserRoleSchema(value=UserRole.GUEST)),
            model_name="always_guest",
        )

        self.assertEqual(
            EnumClassifier.classify(
                "total sketch",
                UserRole,
                assume_guest,
                "assign user rights on the server",
                num_trials=num_trials,
            ),
            (UserRole.GUEST, EmpiricalConfidence(num_trials, num_trials)),
        )

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

    def test_bm_description(self) -> None:
        """Tests for base model description"""

        self.assertEqual(basemodel_name_doc(FruitSchema), DOC_FRUIT_SCHEMA)
        self.assertEqual(
            basemodel_field_doc(
                "value", cast(FieldInfo, FruitSchema.model_fields.get("value"))
            ),
            DOC_FRUIT_VALUE,
        )
        self.assertListEqual(
            list(basemodel_dep_types(FruitSchema, False)), [FruitSchema, Fruit]
        )
        self.assertListEqual(
            list(basemodel_dep_types(FruitSchema, True)), [FruitSchema, Fruit]
        )

        self.assertEqual(basemodel_description(FruitSchema, False), DESC_FRUIT_SCHEMA)
        self.assertEqual(basemodel_description(FruitSchema, True), DESC_FRUIT_SCHEMA)

        # ===

        target = FruitSchema(value=Fruit.APPLE)
        f_b = FruitSchema(value=Fruit.BANANA)
        f_c = FruitSchema(value=Fruit.CHERRY)

        task_desc = "Fruit Task"
        others = (f_b, f_c)

        describer = FactDescriber(FruitSchema, task_desc)
        self.assertEqual(
            describer.prompt(
                target,
                others,
            ),
            DESC_FRUIT_PROMPT__FRUIT_TASK__A_BC,
        )

        knights_who_say = "Ni!"

        model_mphg = FunctionModel(
            lambda *args, **kwargs: ModelResponse(parts=(TextPart(knights_who_say),)),
            model_name="knights_who_say_ni",
        )

        self.assertEqual(
            describer(target, others, model_mphg),
            knights_who_say,
        )

        self.assertEqual(
            FactDescriber.describe(target, task_desc, others, model_mphg),
            knights_who_say,
        )

        # ===

        self.assertEqual(
            basemodel_name_doc(BinaryResponseSchema), DOC_BINARYRESPONSE_SCHEMA
        )
        self.assertEqual(
            basemodel_field_doc(
                "yn", cast(FieldInfo, BinaryResponseSchema.model_fields.get("yn"))
            ),
            DOC_BINARYRESPONSE_YN,
        )
        self.assertListEqual(
            list(basemodel_dep_types(BinaryResponseSchema, False)),
            [BinaryResponseSchema, BinaryResponse],
        )
        self.assertListEqual(
            list(basemodel_dep_types(BinaryResponseSchema, True)),
            [BinaryResponseSchema, BinaryResponse],
        )

        self.assertEqual(
            basemodel_description(BinaryResponseSchema, False),
            DESC_BINARYRESPONSE_SCHEMA,
        )
        self.assertEqual(
            basemodel_description(BinaryResponseSchema, True),
            DESC_BINARYRESPONSE_SCHEMA,
        )

        # ===

        self.assertEqual(basemodel_name_doc(UserRoleSchema), DOC_USERROLE_SCHEMA)
        self.assertEqual(
            basemodel_field_doc(
                "value", cast(FieldInfo, UserRoleSchema.model_fields.get("value"))
            ),
            DOC_USERROLE_VALUE,
        )
        self.assertListEqual(
            list(basemodel_dep_types(UserRoleSchema, False)),
            [UserRoleSchema, UserRole],
        )
        self.assertListEqual(
            list(basemodel_dep_types(UserRoleSchema, True)),
            [UserRoleSchema, UserRole],
        )

        self.assertEqual(
            basemodel_description(BinaryResponseSchema, False),
            DESC_BINARYRESPONSE_SCHEMA,
        )
        self.assertEqual(
            basemodel_description(BinaryResponseSchema, True),
            DESC_BINARYRESPONSE_SCHEMA,
        )

        # ===

        _ = FactDescriber(ComplexSchema, "")  # just confirming it does not error

        self.assertEqual(basemodel_name_doc(ComplexSchema), DOC_COMPLEX_SCHEMA)
        self.assertEqual(
            basemodel_field_doc(
                "a", cast(FieldInfo, ComplexSchema.model_fields.get("a"))
            ),
            DOC_COMPLEX_A,
        )
        self.assertEqual(
            basemodel_field_doc(
                "b", cast(FieldInfo, ComplexSchema.model_fields.get("b"))
            ),
            DOC_COMPLEX_B,
        )
        self.assertEqual(
            basemodel_field_doc(
                "e", cast(FieldInfo, ComplexSchema.model_fields.get("e"))
            ),
            DOC_COMPLEX_E,
        )
        self.assertEqual(
            basemodel_field_doc(
                "q", cast(FieldInfo, ComplexSchema.model_fields.get("q"))
            ),
            DOC_COMPLEX_Q,
        )
        self.assertListEqual(
            list(basemodel_dep_types(ComplexSchema, False)),
            [
                ComplexSchema,
                BinaryResponse,
                FruitSchema,
                BinaryResponseSchema,
                UserRoleSchema,
            ],
        )
        self.assertListEqual(
            list(basemodel_dep_types(ComplexSchema, True)),
            [
                ComplexSchema,
                BinaryResponse,
                FruitSchema,
                BinaryResponseSchema,
                UserRoleSchema,
                Fruit,
                UserRole,
            ],
        )

        self.assertEqual(
            basemodel_description(ComplexSchema, False),
            DESC_COMPLEX_SCHEMA_SHALLOW,
        )
        self.assertEqual(
            basemodel_description(ComplexSchema, True),
            DESC_COMPLEX_SCHEMA_DEEP,
        )
