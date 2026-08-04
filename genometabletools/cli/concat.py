"""
Command-line interface for table concatenation.
"""

from genometabletools.table import Table
from .report import print_report


def add_parser(subparsers):

    parser = subparsers.add_parser(
        "concat",
        help="Concatenate two or more tables."
    )

    parser.add_argument(
        "input",
        nargs="+",
        help="Input tables."
    )

    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output table."
    )

    parser.add_argument(
        "--no-verify-columns",
        action="store_true",
        help="Skip column validation."
    )

    parser.set_defaults(func=run)


def run(args):

    # Load tables
    tables = [Table(f) for f in args.input]

    # Concatenate
    result = Table.concat(
        *tables,
        verify_columns=not args.no_verify_columns,
    )

    # Save output
    result.save(args.output)

    # Print report
    print_report(
        result.concat_report,
        output=args.output,
    )