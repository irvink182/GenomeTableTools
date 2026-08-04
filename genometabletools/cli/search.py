"""
Command-line interface for table search module.
"""

from genometabletools.table import Table



def run(args):
    """
    Search values in a table.
    """

    table = Table(args.input)

    result = table.search(
        columns=args.columns,
        values=args.values,
        ignore_case=not args.keep_case,
        strip_spaces=not args.keep_spaces,
    )

    result.write(args.output)

    if not args.quiet:
        print(result.summary())


def add_parser(subparsers):

    parser = subparsers.add_parser(
        "search",
        help="Search values in a table."
    )

    parser.add_argument(
        "input",
        help="Input table."
    )

    parser.add_argument(
        "--columns",
        action="append",
        required=True,
        help="Columns to search (can be repeated).",
    )

    parser.add_argument(
        "--values",
        help="Value to search or file containing values (txt, csv, tsv, xlsx)."
    )

    parser.add_argument(
        "-o",
        "--output",
        default="search",
        help="Output file prefix."
    )

    parser.add_argument(
        "--keep-case",
        action="store_true",
        help="Case-sensitive search."
    )

    parser.add_argument(
        "--keep-spaces",
        action="store_true",
        help="Do not strip leading/trailing spaces."
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress console output."
    )

    parser.set_defaults(func=run)