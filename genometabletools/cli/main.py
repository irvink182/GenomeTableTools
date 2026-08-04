import argparse

from . import concat
from . import search
from . import annotate
from . import integrate
from . import registry
from . import filter


def main():

    parser = argparse.ArgumentParser(
        prog="genometabletools"
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