"""
LLM fact descriptions
"""

from __future__ import annotations

from pydantic import Field

from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

from rich import print as rprint

from cognition import (
    BinaryRelation,
    DocEnum,
    Entity,
    FactDescriber,
    timed,
)

from dotenv import load_dotenv

load_dotenv()

#


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


#


class TruckRoute(BinaryRelation):
    """A truck route that allows for transporting goods."""

    entity1: Office = Field(description="Starting city of the route")
    entity2: Office = Field(description="Ending city of the route")
    distance: int = Field(description="Distance in miles to drive this route")


class AirRoute(BinaryRelation):
    """An air route that allows for transporting goods."""

    entity1: Airport = Field(description="Starting airport of the route")
    entity2: Airport = Field(description="Ending airport of the route")
    price: int = Field(description="Cost in USD to fly this route")


class At(BinaryRelation):
    """The location of an object"""

    entity1: Package | Vehicle = Field(description="The object of interest")
    entity2: Office | Airport | Vehicle = Field(description="The object's location")


#


def main() -> None:
    """get your describing on!"""

    num_trials = 3

    llm_model = OpenAIResponsesModel(
        "openai/gpt-oss-20b",
        provider=OpenAIProvider(
            base_url="http://localhost:1234/v1", api_key="not needed"
        ),
    )

    task_desc = "A logistics app in which packages are routed between office locations"

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

    print(f"Model: { llm_model.model_id }")
    print()

    for fact_type in {type(f) for f in facts}:
        describer = FactDescriber(fact_type, task_desc)

        rprint(f"[bold underline]Prompt ({fact_type.__name__})[/]")
        print()
        rprint(("[i]" f"{describer.prompt(
                "<< target fact here >>",  # type: ignore
                ("<< other fact 1 >>", "<< other fact 2 >>", "..."),  # type: ignore
            )}" "[/]"))
        print()

        rprint("[bold underline]Facts[/]")
        for typed_fact in (f for f in facts if isinstance(f, fact_type)):
            others = set(facts) - {typed_fact}

            @timed
            def _describe():  # type: ignore
                # pylint: disable=cell-var-from-loop
                return describer(typed_fact, others, llm_model)

            rprint(f"Fact: {typed_fact}")
            for _ in range(num_trials):
                result, time = _describe()
                print(f"* ({time:.2f}sec): ", end="")
                rprint(f"[i]{result}[/]")
            print()


if __name__ == "__main__":
    main()
