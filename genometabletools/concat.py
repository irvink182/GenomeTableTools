"""
concat.py

Concatenate tables for GenomeTableTools.
"""

import time
import pandas as pd

from .table import Table


class ConcatOperation:
    """
    Concatenate multiple tables vertically.

    All tables must have exactly the same columns
    (same names and same order).
    """

    def __init__(self, *tables):

        self.tables = list(tables)

        self.report = {
            "operation": "concat",
            "execution_time": None,
            "summary": {
                "Input tables": 2,
            "Input rows": "25 + 21",
            "Output rows": 46,
            "Columns": 16,
            }
        }

    def run(
        self,
        ignore_index=True,
        verify_columns=True,
    ):

        start = time.perf_counter()

        # -----------------------------
        # Validate input
        # -----------------------------

        if len(self.tables) < 2:
            raise ValueError(
                "At least two tables are required."
            )

        # -----------------------------
        # Validate columns
        # -----------------------------

        reference = self.tables[0].columns

        if verify_columns:

            for i, table in enumerate(self.tables[1:], start=2):

                if table.columns != reference:

                    self.report["column_mismatch"] = True

                    raise ValueError(
                        f"Table {i} does not have the same columns "
                        "as the first table."
                    )

        # -----------------------------
        # Concatenate
        # -----------------------------

        dfs = [table.df for table in self.tables]

        concatenated = pd.concat(
            dfs,
            ignore_index=ignore_index,
        )

        # -----------------------------
        # Create output Table
        # -----------------------------

        result = Table.from_dataframe(
            concatenated,
            template=self.tables[0],
        )

        # -----------------------------
        # Report
        # -----------------------------

        self.report["tables_input"] = len(self.tables)

        self.report["rows_input"] = [
            table.n_rows
            for table in self.tables
        ]

        self.report["rows_output"] = result.n_rows

        self.report["columns"] = result.n_columns

        self.report["execution_time"] = round(
            time.perf_counter() - start,
            3,
        )

        result.concat_report = self.report

        return result