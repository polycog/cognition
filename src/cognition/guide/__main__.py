"""
Command line access to the packaged agent guide

* ``python -m cognition.guide``: list headings (indented by level)
* ``python -m cognition.guide "Gotchas" "Debugging"``: print those sections
* ``python -m cognition.guide --path``: print the guide's file location
"""

import argparse
import sys

from .sections import guide_file, guide_section, guide_sections

# ===


def main(argv: list[str] | None = None) -> int:
    """
    Runs the command line interface

    :param argv: arguments (``None`` for ``sys.argv[1:]``)
    :return: exit status (0 on success, 1 for an unknown heading)
    """

    parser = argparse.ArgumentParser(
        prog="python -m cognition.guide",
        description=(
            "Print sections of the cognition agent guide (AGENTS.md) "
            "for the installed version. With no headings, list them."
        ),
    )
    parser.add_argument(
        "headings",
        nargs="*",
        help="exact heading text (backticks optional), e.g. Gotchas",
    )
    parser.add_argument(
        "--path", action="store_true", help="print the guide's file location"
    )
    args = parser.parse_args(argv)

    if args.path:
        print(guide_file())
        return 0

    if not args.headings:
        for section in guide_sections():
            print(f"{'  ' * (section.level - 1)}{section.name}")
        return 0

    try:
        texts = [guide_section(h).text for h in args.headings]
    except KeyError as err:
        print(err.args[0], file=sys.stderr)
        return 1

    print("\n".join(texts), end="")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
