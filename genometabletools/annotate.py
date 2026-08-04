"""
annotate.py

Annotation operations for GenomeTableTools.
"""

from datetime import datetime
import time
import pandas as pd

from .table import Table

class AnnotationResult:

    def __init__(self):

        self.table = None
        self.report = {}
    
    def summary(self):

        lines = []

        lines.append("=" * 60)
        lines.append("Annotation Report")
        lines.append("=" * 60)

        for key, value in self.report.items():
            lines.append(f"{key:25}: {value}")

        return "\n".join(lines)

    def write(self, prefix):

        self.table.save(f"{prefix}.tsv")

        with open(f"{prefix}_report.txt", "w") as f:
            f.write(self.summary())
            f.write("\n")

class AnnotationOperation:

    def __init__(self, target, reference):

        self.target = target
        self.reference = reference

        self.report = {
            "key": None,
            "rows_target": 0,
            "rows_reference": 0,
            "rows_output": 0,
            "columns_copied": [],
            "matched": 0,
            "not_annotated": 0,
            "execution_time": None,
            "timestamp": None,
        }

    def run(
        self,
        key,
        columns=None,
        exclude_columns=None,
        overwrite=False,
    ):

        start = time.perf_counter()

        # ------------------
        # Select columns
        # ------------------

        if columns is None:

            columns = [

                c

                for c in self.reference.columns

                if (

                    c != key

                    and c not in self.target.columns
                )
            ]
        
        if exclude_columns is not None:

            columns = [
                c
                for c in columns
                if c not in exclude_columns
            ]
        
        # ------------------
        # Validate key
        # ------------------

        missing = [

            c

            for c in columns

            if c not in self.reference.columns

        ]

        if missing:

            raise ValueError(
                f"Columns not found: {missing}"
            )

        if key not in self.target.columns:
            raise ValueError(
                f"'{key}' not found in target table."
            )

        if key not in self.reference.columns:
            raise ValueError(
                f"'{key}' not found in reference table."
            )

        ref = self.reference.df[
            [key] + columns
        ]



        shared_columns = [

            c

            for c in columns

            if c in self.target.columns
        ]

        new_columns = [

            c

            for c in columns

            if c not in self.target.columns
        ]


        # ------------------
        # Duplicated columns
        # ------------------

        duplicates = self.reference.df.duplicated(
            subset=[key],
            keep=False,
        )

        if duplicates.any():
            duplicated_keys = (
                self.reference.df.loc[duplicates, key]
                .unique()
                .tolist()
            )

            raise ValueError(
                f"Reference table contains duplicated '{key}' values "
                f"({len(duplicated_keys)} duplicated keys).")

        # ------------------
        # Merge columns
        # ------------------

        merged = pd.merge(

            self.target.df,

            ref,

            on=key,

            how="left",

            suffixes=("", "_ref"),

            indicator=True,

        )

        # ------------------
        # Overwrite=False
        # ------------------

        for col in new_columns:
            merged.rename(
                columns={
                    f"{col}_ref": col
                },

            inplace=True,
            )

        for col in shared_columns:
            ref_col = f"{col}_ref"

            if overwrite:
                merged[col] = merged[ref_col].combine_first(
                    merged[col]
                )
            else:
                merged[col] = merged[col].combine_first(
                    merged[ref_col]
                )

            merged.drop(
                columns=ref_col,
                inplace=True,
            )

        # ------------------
        # Stats
        # ------------------

        matched = (
            merged["_merge"] == "both"
        ).sum()

        not_annotated = (
            merged["_merge"] == "left_only"
        ).sum()

        merged.drop(
            columns="_merge",
            inplace=True,
        )

        # ------------------
        # Results
        # ------------------

        table = Table.from_dataframe(
            merged,
            template=self.target
        )

        self.report["key"] = key
        self.report["rows_target"] = self.target.n_rows
        self.report["rows_reference"] = self.reference.n_rows
        self.report["rows_output"] = table.n_rows
        self.report["shared_columns"] = shared_columns
        self.report["new_columns"] = new_columns
        self.report["columns_copied"] = columns
        self.report["matched"] = int(matched)
        self.report["not_annotated"] = int(not_annotated)
        self.report["execution_time"] = round(
            time.perf_counter() - start,
            3,
        )

        self.report["timestamp"] = datetime.now().isoformat()

        result = AnnotationResult()

        result.table = table

        result.report = self.report

        table.annotation_report = self.report

        return result
