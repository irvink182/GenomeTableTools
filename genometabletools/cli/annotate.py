"""
Command-line interface for table annotate module.
"""

from genometabletools.table import Table

def run(args):

    target = Table(args.input)

    reference = Table(args.reference)

    result = target.annotate(
        reference,
        key=args.key,
        columns=args.columns,
        exclude_columns=args.exclude_columns,
        overwrite=args.overwrite,
    )

    result.write(args.output)

    if not args.quiet:
        print(result.summary())

def add_parser(subparsers):

    parser = subparsers.add_parser(
        "annotate",
        help="Annotate a table using a reference table."
    )

    parser.add_argument(
        "input",
        help="Input table."
    )

    parser.add_argument(
        "reference",
        help="Reference table used for annotation."
    )

    parser.add_argument(
    	"--key",
    	required=True,
    	help="Key column present in both target and reference tables."
    )

    parser.add_argument(
        "--columns",
        action="append",
        help="Columns from the referencia table to copy (can be repated).",
    )

    parser.add_argument(
        "--exclude-columns",
        action="append",
        help="Columns to exclude.",
    )

    parser.add_argument(
    	"--overwrite",
    	action="store_true",
    	help="Overwrite existing values."
    )

    parser.add_argument(
        "-o",
        "--output",
        default="annotated",
        help="Output file prefix."
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress console output."
    )

    parser.set_defaults(func=run)