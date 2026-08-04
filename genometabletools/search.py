"""
search.py

Search operations for GenomeTableTools.
"""

from pathlib import Path
from datetime import datetime
import time

import pandas as pd

from .table import Table


class SearchResult:
    """
    Object returned by a search operation.
    """

    def __init__(self):

        self.requested = None
        self.found = None
        self.missing = None

        self.report = {}

    def summary(self):

        lines = []

        lines.append("=" * 60)
        lines.append("Search Report")
        lines.append("=" * 60)

        for key, value in self.report.items():
            lines.append(f"{key:25}: {value}")

        return "\n".join(lines)

    def write(self, prefix):

        self.found.save(f"{prefix}_found.tsv")

        self.missing.save(f"{prefix}_missing.tsv")

        with open(f"{prefix}_report.txt", "w") as f:
            f.write(self.summary())
            f.write("\n")


class SearchOperation:

    def __init__(self, table):

        self.table = table

    def run(
        self,
        columns,
        values,
        ignore_case=True,
        strip_spaces=True,
    ):

        start = time.perf_counter()

        if isinstance(columns, str):
            columns = [columns]

        for column in columns:

            if column not in self.table.columns:
                raise ValueError(
                    f"Column '{column}' not found."
                )

        requested = self._load_values(values)

        duplicates_removed = len(requested) - len(set(requested))

        requested = list(dict.fromkeys(requested))

        if strip_spaces:

            requested = [
                str(x).strip()
                for x in requested
            ]

        if ignore_case:

            requested = [
                str(x).upper()
                for x in requested
            ]

        mask = pd.Series(False, index=self.table.df.index)

        all_found_values = set()

        for column in columns:

            search_column = self.table.df[column].astype(str)

            if strip_spaces:
                search_column = search_column.str.strip()

            if ignore_case:
                search_column = search_column.str.upper()

            mask |= search_column.isin(requested)

            all_found_values.update(search_column.dropna().unique())

        found_df = self.table.df.loc[mask].copy()

        missing = sorted(
            set(requested) - all_found_values
        )

        missing_df = pd.DataFrame(
            {
                "value": missing
            }
        )

        result = SearchResult()

        result.requested = requested

        result.found = Table.from_dataframe(
            found_df,
            template=self.table
        )

        result.missing = Table.from_dataframe(
            missing_df
        )

        result.report = {

            "searched_columns": ", ".join(columns),

            "requested": len(requested),

            "found": len(found_df),

            "missing": len(missing),

            "duplicates_removed": duplicates_removed,

            "execution_time": round(
                time.perf_counter() - start,
                3
            ),

            "timestamp": datetime.now().isoformat()

        }

        return result

    def _load_values(self, values):

        #
        # Python list
        #

        if isinstance(values, list):
            return values

        #
        # Table
        #

        if isinstance(values, Table):
            return values.df.iloc[:, 0].tolist()

        #
        # Single value or file
        #

        if isinstance(values, (str, Path)):

            path = Path(values)

            # Single value
            if not path.exists():
                return [str(values)]

            # File
            ext = path.suffix.lower()

            if ext == ".txt":
                with open(path) as f:
                    return [
                        line.strip()
                        for line in f
                        if line.strip()
                    ]

            elif ext in [".csv", ".tsv"]:

                sep = "\t" if ext == ".tsv" else ","

                df = pd.read_csv(
                    path,
                    sep=sep,
                    dtype=str,
                )

                return df.iloc[:, 0].tolist()

            elif ext in [".xlsx", ".xls"]:

                df = pd.read_excel(
                    path,
                    dtype=str,
                )

                return df.iloc[:, 0].tolist()

            else:
                raise ValueError(
                    f"Unsupported file format: {ext}"
                )