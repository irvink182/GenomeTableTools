from pathlib import Path

from ..registry import registry_update

def run_update(args):

    registry_update(
        metadata_file=args.input,
        reference_file=args.reference,
        validation_file=args.validation,
        output_file=args.output,
        review_output_file=args.review_output,
        new_records_output_file=args.new_records_output,
    )


def add_parser(subparsers):

    parser = subparsers.add_parser(
        "registry",
        help="Laboratory metadata registry tools",
    )

    registry_subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    ###########################################################################
    # update
    ###########################################################################

    update = registry_subparsers.add_parser(
        "update",
        help="Update laboratory metadata from new GISAID metadata",
    )

    update.add_argument(
        "--input",
        required=True,
        help="Input GISAID sequencing metadata TSV file",
    )

    update.add_argument(
        "--reference",
        required=True,
        help="Historical laboratory metadata TSV file",
    )

    update.add_argument(
        "--validation",
        help=(
            "Optional curated laboratory metadata TSV "
            "used to validate predictions"
        ),
    )

    update.add_argument(
        "--output",
        required=True,
        help="Output laboratory metadata TSV file",
    )

    update.add_argument(
        "--review-output",
        help="Optional TSV file for records requiring manual review",
    )

    update.add_argument(
        "--new-records-output",
        help="Optional TSV file containing records added in the current update",
    )

    update.set_defaults(
        func=run_update
    )
