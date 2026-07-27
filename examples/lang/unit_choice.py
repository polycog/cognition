"""
LLM choices ala unit testing
"""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum, StrEnum, auto

from cognition import (
    AutoDocEnum,
    DocEnum,
    EnumClassifier,
    enum_name_doc,
    timed,
)
from dotenv import load_dotenv
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider
from rich import print as rprint

load_dotenv()

# ===


class Fruit(StrEnum):
    """Available fruits"""

    APPLE = auto()
    BANANA = auto()
    CHERRY = auto()


class BinaryResponse(DocEnum):
    """Responding to a question with two possible responses"""

    YES = "yes", "Positive, for, true, 1"
    NO = "no", "Negative, against, false, 0"


class UserRole(DocEnum):
    """System access type for a computer account"""

    ADMIN = 1, "Administrator with full system access"
    STANDARD = 2, "Regular user"
    GUEST = 3, "Temporary account with limited access"


class PhoneIntent(AutoDocEnum):
    """Options for the department within a medical group"""

    EMERGENCY = "Medical emergency"
    SCHEDULING = "Scheduling, appointments, or cancellations"
    MEDICATIONS = "Prescriptions, refills, or pharmacy inquiries"
    RECORDS = "Billing, insurance, or medical records"
    STAFF = "Medical questions, test results, or symptom advice"


# ===


@dataclass(frozen=True)
class ChoiceTestCase[T: Enum]:
    """individual test of an enum choice"""

    in_text: str
    """input"""

    expected_result: T | None
    """expected output"""


@dataclass(frozen=True)
class ChoiceTestSuite[T: Enum]:
    """an enum choice evaluation to perform with associated tests"""

    enum_type: type[T]
    """enum to test"""

    task_desc: str
    """task context to supply"""

    tests: Sequence[ChoiceTestCase[T]]
    """tests to apply"""


test_suites: Sequence[ChoiceTestSuite[Enum]] = (
    ChoiceTestSuite(
        Fruit,
        "Interpreting a shopping list",
        (
            ChoiceTestCase("apple", Fruit.APPLE),
            ChoiceTestCase("🍎", Fruit.APPLE),
            ChoiceTestCase("granny smith", Fruit.APPLE),
            ChoiceTestCase("banana", Fruit.BANANA),
            ChoiceTestCase("🍌", Fruit.BANANA),
            ChoiceTestCase("cavendish", Fruit.BANANA),
            ChoiceTestCase("cherry", Fruit.CHERRY),
            ChoiceTestCase("🍒", Fruit.CHERRY),
            ChoiceTestCase("montmorency", Fruit.CHERRY),
            ChoiceTestCase("not at all a fruit", None),
            ChoiceTestCase("🏠", None),
            ChoiceTestCase("constitution", None),
        ),
    ),
    ChoiceTestSuite(
        BinaryResponse,
        "Interpreting a response to a meeting invitation",
        (
            ChoiceTestCase("Yes!", BinaryResponse.YES),
            ChoiceTestCase("Totally, let's do it!", BinaryResponse.YES),
            ChoiceTestCase("👍", BinaryResponse.YES),
            ChoiceTestCase("No.", BinaryResponse.NO),
            ChoiceTestCase("can't :(", BinaryResponse.NO),
            ChoiceTestCase("👎", BinaryResponse.NO),
            ChoiceTestCase("smush vs connections", None),
            ChoiceTestCase("how many woodchucks could a woodchuck chuck", None),
        ),
    ),
    ChoiceTestSuite(
        UserRole,
        "Suggesting the appropriate level of account access given a role description",
        (
            ChoiceTestCase("Just coming in for the day", UserRole.GUEST),
            ChoiceTestCase("A new visiting faculty member", UserRole.GUEST),
            ChoiceTestCase("needs sudo powers!", UserRole.ADMIN),
            ChoiceTestCase("A new CTO", UserRole.ADMIN),
            ChoiceTestCase("a regular student", UserRole.STANDARD),
            ChoiceTestCase("A new sales employee", UserRole.STANDARD),
            ChoiceTestCase("I am a 🍌", None),
            ChoiceTestCase("A Toyota Prius", None),
        ),
    ),
    ChoiceTestSuite(
        PhoneIntent,
        "Directing a caller to the appropriate department for assistance",
        (
            ChoiceTestCase("I cannot breath", PhoneIntent.EMERGENCY),
            ChoiceTestCase("My mom is having a seizure", PhoneIntent.EMERGENCY),
            ChoiceTestCase("I cannot make my visit tomorrow", PhoneIntent.SCHEDULING),
            ChoiceTestCase(
                "My son has a fever - can we get in today?", PhoneIntent.SCHEDULING
            ),
            ChoiceTestCase("I need to refill my inhaler", PhoneIntent.MEDICATIONS),
            ChoiceTestCase(
                "CVS says you haven't sent over the rx", PhoneIntent.MEDICATIONS
            ),
            ChoiceTestCase(
                "I moved and need to update my address", PhoneIntent.RECORDS
            ),
            ChoiceTestCase(
                "BCBS needs confirmation of my visit to process the claim",
                PhoneIntent.RECORDS,
            ),
            ChoiceTestCase(
                "I need to talk to a nurse about my cough", PhoneIntent.STAFF
            ),
            ChoiceTestCase(
                "Is 140/90 ok for blood pressure after a run?", PhoneIntent.STAFF
            ),
            ChoiceTestCase("please recommend a great margarita recipe", None),
            ChoiceTestCase("I would like to apply for a small-business loan", None),
        ),
    ),
)

# ===


def main() -> None:
    """get your choosing on!"""

    num_trials: int = 5
    llm_model = OpenAIResponsesModel(
        "openai/gpt-oss-20b",
        provider=OpenAIProvider(
            base_url="http://localhost:1234/v1", api_key="not needed"
        ),
    )

    print(f"Trials per test: { num_trials }")
    print(f"Model: { llm_model.model_id }")

    for suite in test_suites:
        print()
        rprint(f"[bold underline]{ enum_name_doc(suite.enum_type) }[/]")
        print()

        classifier = EnumClassifier(suite.enum_type, suite.task_desc)
        print(classifier.prompt("<< input here >>"))
        print()

        rprint("[bold italic]Tests...[/]")
        for test in suite.tests:
            print(f">>> {test.in_text} (expected={test.expected_result})")

            @timed
            def _classify():  # type: ignore
                # pylint: disable=cell-var-from-loop
                # ruff: ignore[B023]
                return classifier(test.in_text, llm_model, num_trials)

            (result, confidence), time = _classify()

            if result == test.expected_result:
                color = "green"
            else:
                color = "red"

            rprint(
                f"    [bold { color }]{result} ({100*float(confidence):.0f}% "
                f"@ {time / num_trials:.2f}sec/trial)[/]"
            )

        print()


if __name__ == "__main__":
    main()
