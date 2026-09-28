"""
Hello World!
(at a low level)
"""

from collections.abc import Iterable

from cognition import Action, BaseDecisionProcess, IOContainer, stringify

# ===


@stringify("hello")
def hello_factory(s: bool, _io: IOContainer) -> Iterable[Action[bool]]:
    """action factory"""

    @stringify("hello")
    def hello(_a_s: bool, _a_io: IOContainer) -> bool:
        """potentially proposed action"""

        # if selected, say hello!
        print("Hello, World!")

        # return new state
        return True

    # if init state, propose hello!
    if not s:
        return (hello,)

    # otherwise, nothing to propose
    return ()


# ===

dp = BaseDecisionProcess(lambda: False)

dp.add_action_factory(hello_factory)

# done if state is True
dp.add_termination_check(stringify("done?")(lambda s, _io: s))

# ===

# initial state
print(f"{dp.state}")

dp.run_until_done()

# uncomment to see the result of stringify'd components
# print(dp)

# final state
print(f"{dp.state}")
