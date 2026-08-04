"""
Command-line interface for table filter module.
"""

from genometabletools.table import Table
from .report import print_report


def add_parser(subparsers):

    parser = subparsers.add_parser(
        "filter",
        help="Filter tabular metadata",
        description=(
            "Filter rows from a table using one or more expressions."
            "Multiple --where options are comibined with AND."
        ),
    )

    parser.add_argument(
        "input",
        help="Input table",
    )

    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output table",
    )

    parser.add_argument(
        "--where",
        action="append",
        required=True,
        help=(
            "Filter expression (can be repeated). "
            "Examples: "
            "'Subtype=A'; "
            "'Sequence Length>=15000'; "
            "'Sequencing technology contains illumina'; "
            "'Virus name startswith hRSV-A'; "
            "'Assembly method isna'."
        ),
    )

    parser.set_defaults(func=run)


def run(args):

    table = Table(args.input)

    filtered = table.filter(*args.where)

    filtered.save(args.output)

    print_report(filtered.filter_report)