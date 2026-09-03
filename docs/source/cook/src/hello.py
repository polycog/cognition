"""
Hello World!
"""

from cognition import Cogent, DecisionProcess, IOContainer, Operator

# ===

# dp state is boolean, starting as False
my_cogent = Cogent(DecisionProcess(lambda: False))


@my_cogent.dp.operator(
    "hello", terminal=True
)  # shortcut to create + add an operator instance
#    (named "hello" with the terminal flag to stop the DP)
class HelloOperator(Operator[bool]):
    """
    Says hello!
    """

    def can_perform(self, state: bool, _io: IOContainer) -> bool:
        # this will only apply if the state is False
        return not state

    def perform(self, _state: bool, _io: IOContainer) -> bool:
        print("Hello, World!")

        # mutable state can be just changed;
        # returned values replace state
        return True


# initial state
print(f"{my_cogent.dp.state}")

# nifty way to run the cogent 🤓
# 0. no arguments/sensors/actuators, so just starts the DP
# 1. elaborate: no elaborators, done!
# 2. terminal: no checks; no prior action selected; done!
# 3. propose: hello (via can_perform, where state=False) is proposed!
# 4. rank: only one action, so hello is selected
# 5. apply: print, new state applied (via perform, where state=False)
# 6. elaborate: no elaborators, done!
# 7. terminal: no checks; prior action was terminal -> stop!
# 8. by default, cogent doesn't continue after dp -> done!
my_cogent()

# final state
print(f"{my_cogent.dp.state}")
