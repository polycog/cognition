"""
Choosing cogent
"""

from cognition import Cogent, DecisionProcess

from container import ChoiceContainer
from dp import (
    ChooseFieldGenerator,
    ChooseValueGenerator,
    ChosenField,
    lookahead_sorting,
    random_field_selection,
)
from env import ChoiceEnvironment
from outfit import Outfit

###################################################
# Start the app
###################################################


def main() -> None:
    """dispatch the choice agent"""

    num_choice_trials = 10
    container: ChoiceContainer = Outfit()

    # ===

    env = ChoiceEnvironment(container)

    cogent = Cogent(
        DecisionProcess(ChosenField)
        .add_generator_c(ChooseFieldGenerator, env)
        .add_generator_c(ChooseValueGenerator, env)
    )

    env.add_sensors_actuators(cogent)

    # ===
    # option #1: ordering over field selection
    # ===

    # 1a) random (comment out if using random)
    cogent.dp.add_action_evaluator(random_field_selection)

    # 1b) sorted (need to import above)
    # cogent.dp.add_action_evaluator(field_sorting(10, colors=1))

    # ===
    # option #2: preferences over value selection
    # ===

    # 2a) random (need to import above)
    # cogent.dp.add_action_evaluator(random_value_selection)

    # 2b) 1-step lookahead to avoid unacceptable assignments
    #     (comment out if using random)
    cogent.dp.add_action_evaluator(lookahead_sorting(env))

    # ===

    total_attempts = 0
    for trial in range(num_choice_trials):
        attempts = 1
        container.reset()

        print(f"== Trial {trial+1} ==")
        print(f"[start={container}]")
        while not container.acceptable:
            print(f"# Attempt {attempts}")
            total_attempts += 1

            while not container.done:
                cogent()
                print(f"-> {container}")

            if container.acceptable:
                print("✅")
            else:
                print("❌")
                container.reset()
                attempts += 1
            print()

    print(
        f"Complete: attempts={total_attempts}, attempts/trial={total_attempts / trial:.2f}"
    )


if __name__ == "__main__":
    main()
