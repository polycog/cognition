"""
LLM fact descriptions
"""

from __future__ import annotations

from cognition import (
    BinaryRelation,
    DocEnum,
    Entity,
    FactDescriber,
    ModelPopulator,
    timed,
)
from dotenv import load_dotenv
from pydantic import Field
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider
from rich import print as rprint

load_dotenv()

# ===


class City(DocEnum):
    """City airport code"""

    BOSTON = "BOS", "Boston, MA"
    DENVER = "DEN", "Denver, CO"
    DETROIT = "DTW", "Detroit, MI"
    SAN_FRANCISCO = "SFO", "San Francisco, CA"
    SEATTLE = "SEA", "Seattle, WA"

    @property
    def office(self) -> Office:
        """associated office"""
        return Office(name=self.name, city=self)

    @property
    def airport(self) -> Airport:
        """associated airport"""
        return Airport(name=self.value, city=self)


class GasPrice(Entity):
    """Current gas pricing"""

    per_mile: float = Field(description="Cost in USD per mile of driving")


class Office(Entity):
    """A company office"""

    city: City = Field(description="City in which this office is located")


class Airport(Entity):
    """
    An airport location
    """

    city: City = Field(description="City in which this airport is located")


class Package(Entity):
    """A named package"""


class Vehicle(Entity):
    """A vehicle type"""


class Truck(Vehicle):
    """A named truck useful for delivering packages"""


class Airplane(Vehicle):
    """A named plane for transporting goods"""


# ===


class TruckRoute(BinaryRelation):
    """A truck route that allows for transporting goods."""

    entity1: Office = Field(description="Starting city of the route", frozen=True)
    entity2: Office = Field(description="Ending city of the route", frozen=True)
    distance: int = Field(description="Distance in miles to drive this route")


class AirRoute(BinaryRelation):
    """An air route that allows for transporting goods."""

    entity1: Airport = Field(description="Starting airport of the route", frozen=True)
    entity2: Airport = Field(description="Ending airport of the route", frozen=True)
    price: int = Field(description="Cost in USD to fly this route")


class At(BinaryRelation):
    """The location of an object"""

    entity1: Package | Vehicle = Field(description="The object of interest", frozen=True)
    entity2: Office | Airport | Vehicle = Field(description="The object's location", frozen=True)


# ===


def main() -> None:
    """get your describing on!"""

    num_trials = 3

    llm_model = OpenAIResponsesModel(
        "openai/gpt-oss-20b",
        provider=OpenAIProvider(
            base_url="http://localhost:1234/v1", api_key="not needed"
        ),
    )

    task_desc = "A logistics app in which packages are routed between office locations."

    facts = [
        City.BOSTON.office,
        City.SAN_FRANCISCO.office,
        City.SEATTLE.office,
        City.DETROIT.airport,
        City.SAN_FRANCISCO.airport,
        City.SEATTLE.airport,
        p1 := Package(name="package1"),
        Truck(name="truck1"),
        Airplane(name="airplane1"),
        GasPrice(name="gas_price", per_mile=0.2),
        TruckRoute(
            entity1=City.SAN_FRANCISCO.office,
            entity2=City.SEATTLE.office,
            distance=800,
        ),
        AirRoute(
            entity1=City.SAN_FRANCISCO.airport,
            entity2=City.DETROIT.airport,
            price=629,
        ),
        At(
            entity1=p1,
            entity2=City.SEATTLE.office,
        ),
    ]

    desc_extra = (
        "Note: fact name fields are considered critical and case-sensitive, and so be careful "
        "about (a) making sure to include them, and (b) putting them at the beginning of a "
        "sentence without care, since capitalization would then become ambiguous - "
        " either avoid names in that position, or quote them."
    )

    pop_extra = (
        "The names of offices and airports are derived from their corresponding city: "
        "\n"
        "* The name of an office is the corresponding city name."
        "\n"
        f"  For example, the name of the office in Boston ({City.BOSTON.office}) "
        f"  is the same as Boston's name ({City.BOSTON.name})"
        "\n"
        "* The name of an airport is the corresponding city value/code."
        "\n"
        f"  For example, the name of the airport in San Francisco ({City.SAN_FRANCISCO.airport}) "
        f"  is the same as San Francisco's value/code ({City.SAN_FRANCISCO.value})"
        "\n"
        "Note that in each case, spaces are converted to underscores."
    )

    print(f"Model: { llm_model.model_id }")
    print()

    for fact_type in {type(f) for f in facts}:
        describer = FactDescriber(fact_type, task_desc)
        populator = ModelPopulator(fact_type, task_desc)

        rprint(f"[bold underline]Describer Prompt ({fact_type.__name__})[/]")
        print()
        rprint(f"[i]{describer.prompt(
                   "<< target fact here >>",  # type: ignore
                   ("<< other fact 1 >>", "<< other fact 2 >>", "..."),  # type: ignore
                )}[/]")
        print()

        rprint(f"[bold underline]Populator Prompt ({fact_type.__name__})[/]")
        print()
        rprint(f"[i]{populator.prompt("<< utterance here >>")}[/]")
        print()

        rprint("[bold underline]Facts[/]")
        for typed_fact in (f for f in facts if isinstance(f, fact_type)):
            others = tuple(f for f in facts if f != typed_fact)

            @timed
            def _describe():  # type: ignore
                # pylint: disable=cell-var-from-loop
                # ruff: ignore[B023]
                return describer(typed_fact, others, llm_model, desc_extra)

            @timed
            def _populate(desc):  # type: ignore
                # pylint: disable=cell-var-from-loop
                # ruff: ignore[B023]
                return populator(desc, llm_model, pop_extra)

            rprint(f"Fact: {typed_fact}")
            for t in range(num_trials):
                print(f"* Trial { t + 1 }")

                d_result, d_time = _describe()
                print(f"  -describer ({d_time:.2f}sec)-> ", end="")
                rprint(f"[i]{d_result}[/]")

                p_result, p_time = _populate(d_result)
                print(f"  -populator ({p_time:.2f}sec)-> ", end="")
                rprint(f"[i]{p_result}[/]")

                match = p_result == typed_fact
                if match:
                    color = "green"
                else:
                    color = "red"

                rprint(f"   -match-> [bold { color }]{match}[/]")
            print()


if __name__ == "__main__":
    main()
