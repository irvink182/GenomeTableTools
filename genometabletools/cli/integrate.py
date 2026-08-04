"""
Command-line interface for table integration.
"""

from genometabletools.table import Table
from .report import print_report

def add_parser(subparsers):

    parser = subparsers.add_parser(
        "integrate",
        help="Integrate multiple tables."
    )

    parser.add_argument(
        "target",
        help="Target table."
    )

    parser.add_argument(
        "tables",
        nargs="+",
        help="Tables to integrate."
    )

    parser.add_argument(
        "--keys",
        required=True,
        nargs="+",
        help="Merge key(s)."
    )

    parser.add_argument(
        "--preserve_duplicates_columns",
        nargs="+",
        default=[],
        metavar="COLUMN",
        help="Duplicate columns to preserve by renaming."
    )

    parser.add_argument(
        "-o",
        "--output",
        required=True,
    )

    parser.set_defaults(func=run)

def run(args):

    # Load target table
    target = Table(args.target)

    # Load tables to integrate
    tables = [Table(f) for f in args.tables]

    # Integrate
    result = target.integrate(
        *tables,
        keys=args.keys,
        preserve_duplicates_columns=args.preserve_duplicates_columns,
    )

    # Save output
    result.save(args.output)

    # Print report
    print_report(
        result.integration_report,
        output=args.output,
    )