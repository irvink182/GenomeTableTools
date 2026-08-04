from pathlib import Path

from ..registry import (
    registry_build,
    registry_parse,
)

def run_build(args):

    registry_build(
        metadata_file=args.input,
        registry_dir=Path(args.registry),
    )


def run_parse(args):

    registry_parse(
        metadata_file=args.input,
        registry_dir=Path(args.registry),
        output_file=args.output,
    )

def add_parser(subparsers):

    parser = subparsers.add_parser(
        "registry",
        help="Registry management tools",
    )

    registry_subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    ###########################################################################
    # build
    ###########################################################################

    build = registry_subparsers.add_parser(
        "build",
        help="Build registry candidates",
    )

    build.add_argument(
        "input",
        help="Input metadata TSV file",
    )

    build.add_argument(
        "--registry",
        default="registry",
        help="Registry directory",
    )

    build.set_defaults(func=run_build)

    ###########################################################################
    # parse
    ###########################################################################

    parse = registry_subparsers.add_parser(
        "parse",
        help="Parse metadata using the registry",
    )

    parse.add_argument(
        "input",
        help="Input metadata TSV file",
    )

    parse.add_argument(
        "-o",
        "--output",
    )

    parse.add_argument(
        "--registry",
        default="registry",
    )

    parse.set_defaults(func=run_parse)