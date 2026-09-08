import argparse

from importlib.metadata import version
from . import concat
from . import search
from . import annotate
from . import integrate
from . import registry
from . import filter


def main():

    parser = argparse.ArgumentParser(
        prog="genometabletools",
        description=(
            "Toolkit for manipulating tables"
        ),
        epilog="Documentation: https://github.com/irvink182/GenomeTableTools"
    )

    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {version('genometabletools')}",
    )

    subparsers = parser.add_subparsers(
        required=True
    )

    concat.add_parser(subparsers)
    search.add_parser(subparsers)
    annotate.add_parser(subparsers)
    integrate.add_parser(subparsers)
    registry.add_parser(subparsers)
    filter.add_parser(subparsers)

    args = parser.parse_args()

    args.func(args)

if __name__ == "__main__":
    main()