"""
Merge operations for GenomeTableTools.
"""

from datetime import datetime
import time

import pandas as pd

from .table import Table


class MergeOperation:
    """
    Merge two GenomeTableTools tables.
    """

    def __init__(
        self,
        left,
        right,
    ):

        self.left = left
        self.right = right

        self.report = {
            "operation": "merge",
            "execution_time": None,
            "timestamp": None,
            "rows_left": left.n_rows,
            "rows_right": right.n_rows,
            "rows_output": None,
            "keys": None,
            "columns": None,
            "matches": None,
            "how": None,
        }

    def run(
        self,
        keys,
        how="left",
        columns=None,
    ):
        """
        Merge two tables.
        """

        if isinstance(keys, str):
            keys = [keys]

        start = time.perf_counter()

        left = self.left.df.copy()

        right = self.right.df.copy()

        # Validate merge keys
        for key in keys:

            if key not in left.columns:
                raise ValueError(
                    f"'{key}' not found in left table."
                )

            if key not in right.columns:
                raise ValueError(
                    f"'{key}' not found in right table."
                )

        # Select columns to merge
        if columns is not None:

            if isinstance(columns, str):
                columns = [columns]

            missing = [
                c
                for c in columns
                if c not in right.columns
            ]

            if missing:
                raise ValueError(
                    f"Columns not found in right table: {', '.join(missing)}"
                )

            right = right[
                keys + columns
            ]

        else:

            columns = [
                c
                for c in right.columns
                if c not in keys
            ]

        # Perform merge
        merged = pd.merge(
            left,
            right,
            how=how,
            on=keys,
        )

        # Count matched rows
        matched = (
            merged[columns]
            .notna()
            .all(axis=1)
            .sum()
        )

        # Create output table
        result = Table.from_dataframe(
            merged,
            template=self.left,
        )

        self.report["execution_time"] = round(
            time.perf_counter() - start,
            3,
        )

        self.report["timestamp"] = (
            datetime.now().isoformat()
        )

        self.report["rows_output"] = (
            result.n_rows
        )

        self.report["keys"] = keys

        self.report["columns"] = columns

        self.report["matches"] = int(
            matched
        )

        self.report["how"] = how

        result.merge_report = self.report

        return result