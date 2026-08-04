"""
report.py

Utilities for printing GenomeTableTools reports.
"""


LABELS = {
    "main_table": "Main table",
    "secondary_tables": "Secondary tables",
    "total_tables": "Total tables",
    "rows_initial": "Rows (main)",
    "rows_final": "Rows (final)",
    "keys": "Merge keys",
    "preserve_duplicates_columns": "Preserved columns",
}


def print_header():

    print("=" * 60)
    print("GenomeTableTools")
    print("=" * 60)


def print_report(report, output=None):
    """
    Print an operation report.
    """

    print_header()

    print(f"Operation : {report['operation']}")
    print(f"Time      : {report['execution_time']} s\n")

    for key, value in report["summary"].items():

        # Special formatting for table list
        if key == "table_names":
            print("\nInput tables")
            for i, table in enumerate(value):
                suffix = " (main)" if i == 0 else ""
                print(f"  • {table}{suffix}")
            continue

        # Skip empty duplicate column list
        if key == "preserve_duplicates_columns" and not value:
            continue

        # Pretty-print lists
        if isinstance(value, list):
            value = ", ".join(map(str, value))

        label = LABELS.get(
            key,
            key.replace("_", " ").capitalize(),
        )

        print(f"{label:<20}: {value}")

    if output is not None:
        print(f"\nOutput{'':<13}: {output}")

    print("=" * 60)


def print_success(message):

    print(f"[OK] {message}")


def print_warning(message):

    print(f"[WARNING] {message}")


def print_error(message):

    print(f"[ERROR] {message}")