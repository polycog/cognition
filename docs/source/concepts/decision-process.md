# Decision Processes

Polycog agents use a **decision process** as the core pattern to organize and manage task execution. From a developer's perspective, configuring a decision process is as straightforward as programming a traditional workflow. 

However, the underlying execution model is fundamentally different: rather than hardcoding an explicit sequence of steps, you define **decision criteria** declaratively. Polycog's runtime engine - `cognition` - continuously evaluates these criteria against the current state to dynamically compute and adjust the workflow in real-time.

### Running Example: Home Assistant Agent
To illustrate how a decision process operates, we will build a home assistant agent using the `cognition` library. While a production agent might manage an ecosystem of connected appliances—such as smart plugs, dishwashers, and washing machines—we will focus on a simplified environment: a single room with a single lamp. This lamp features a manual switch that can be toggled by either the homeowner or the agent.

Our goal is to implement a specific automation rule for the agent's **NIGHT** mode. When activated, the agent's objective is straightforward: if the lamp is on, disable the switch to turn it off. 

The following sections demonstrate how to build this exact decision process using `cognition`.

A decision process comprises of three concepts. 

---
## 1. State
The **State** collectively captures what is currently true in the environment and tracks where the agent is at in its task execution. 

As an agent designer, you can define and customize the state using standard Python classes. You use variables and methods that best reflect your understanding of the world and the tasks the agent will engage in. 

### Implementation Example

Here is an example of a state class tracking our room's environment:

```python
from enum import Enum

class Switch(Enum):
    ENABLED = 1
    DISABLED = 2

class State:
    """Represents the current environmental and task state for the agent."""
    
    def __init__(self) -> None:
        # Tracks environmental factors
        self.is_light_on: bool = True
        self.switch: Switch = Switch.ENABLED
        
        # Tracks agent execution outputs
        self.output: bool = False
```

## 2. Transitions

A **Transition** is a core component provided by the `cognition` library that describes how to transform the state. When defining a transition, you must override two essential lifecycle methods that dictate the conditional execution flow:

* **`can_perform` ("When"):** Corresponds to a trigger. This method evaluates the current state and returns a boolean indicating whether this specific transition is eligible to be executed.
* **`perform` ("Then"):** Describes the exact business logic and state modifications that happen when this transition is applied.

### Implementation Example

```python
from cognition import (
    IOContainer,
    EnhancedTask as DecisionProcess,
    NamedOperator as Transition
)

class TurnLightOff(Transition[State]):
    """Turns the light off whenever it is currently turned on."""

    def can_perform(self, state: State, _io: IOContainer) -> bool:
        # "When" - Trigger condition: only execute if the light is on
        return state.is_light_on
    
    def perform(self, state: State, _io: IOContainer) -> None: 
        # "Then" - State transformation logic: flip the switch and update output
        state.switch = Switch.DISABLED
        state.output = True
```

## 3. Terminal Check (`is_terminal`)

The final step in defining a decision process is implementing a method to evaluate whether a state is **terminal**. This evaluation allows the `cognition` engine to recognize when a desired outcome or goal has been reached, signaling it to conclude the execution loop.

### Implementation Example

```python
def is_terminal(state: State, _io: IOContainer) -> bool:
    """Evaluates whether the current state has reached a terminal condition."""  
    if state.output:
        return True
    return False
```

## Putting It All Together

With the **State**, **Transitions**, and **Terminal Check** defined, you can now assemble and initialize the full decision process within the `cognition` engine. 

### Initialization Example

```python
# 1. Initialize the state object
state: State = State()

# 2. Instantiate the decision process, passing a lambda that returns the state. This state is supplied by the cognition engine to transitions and is_terminal check. 
dp: DecisionProcess[State] = DecisionProcess(lambda: state)

# 3. Register your transition operators (actions)
dp.add_operator(TurnLightOff("turn_light_off"))

# 4. Define the termination/goal criteria
dp.add_goal_check(is_terminal)

# 5. Inspect the initial state of the decision process
print(dp)

# 6. Execute the decision process
# You can step through execution by specifying a set number of cycles:
# dp.run_cycles(2)

# Or run the engine continuously until a terminal condition evaluates to True:
dp.run_until_done()

# 7. Inspect the final state after execution completes
print(dp)
```

