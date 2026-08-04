"""
integrate.py

Integration operations for GenomeTableTools.
"""

from datetime import datetime
from pathlib import Path
import time

from .table import Table


class IntegrationOperation:

    def __init__(self, target):

        self.target = target

        self.report = {
            "operation": "integrate",
            "execution_time": None,
            "timestamp": None,
            "summary": {
                "rows_initial": target.n_rows,
                "rows_final": None,
            },
            "tables": [],
        }



    def run(
        self,
        *tables,
        keys,
        preserve_duplicates_columns=None,
    ):

        if preserve_duplicates_columns is None:
            preserve_duplicates_columns= []

        elif isinstance(preserve_duplicates_columns, str):
            preserve_duplicates_columns = [preserve_duplicates_columns]

        if isinstance(keys, str):
            keys = [keys]

        start = time.perf_counter()

        result = self.target.copy()

        # -------------------------------------------------
        # Integrate each table
        # -------------------------------------------------

        for i, item in enumerate(tables, start=1):

            if isinstance(item, tuple):

                name, table = item
            
            else: 

                table = item

                name = Path(table.filename).stem

            if not isinstance(table, Table):

                raise TypeError(
                    "All inputs must be Table objects"
                )

            for key in keys:
                if key not in result.columns:
                    raise ValueError(
                        f"'{key}' not found in target table."
                    )

                if key not in table.columns:
                    raise ValueError(
                        f"'{key}' not found in '{name}'."
                    )
            
            # Prefixes, suffixes to duplicated columns
            table = table.copy()

            rename_map = {}
            for col in table.columns:
                if col in keys:
                    continue

                if (
                    col in result.columns
                    and col in preserve_duplicates_columns
                ):
                    rename_map[col] = f"{name}.{col.replace(' ', '_')}"

            table.df = table.df.rename(
                columns=rename_map,
            )

            # Columns that do not already exist
            new_columns = [
                c
                for c in table.columns
                if c not in keys
                and c not in result.columns
            ]

            skipped_columns = [

                c

                for c in table.columns

                if (

                    c not in keys

                    and c in result.columns

                    and c not in preserve_duplicates_columns

                )

            ]

            # Nothing new to add
            if len(new_columns) == 0:

                self.report["tables"].append({

                    "name": name,

                    "rows": table.n_rows,

                    "columns_integrated": [],

                    "columns_skipped": skipped_columns,

                    "columns_renamed": dict(rename_map),

                    "merge_report": None,

                    "matches": None,

                })

                continue

            # Merge only new columns
            result = result.merge(

                table,

                keys=keys,

                columns=new_columns,

            )

            merge_report = result.merge_report

            self.report["tables"].append({

                "name": name,

                "rows": table.n_rows,

                "columns_integrated": new_columns,

                "columns_skipped": skipped_columns,

                "columns_renamed": dict(rename_map),

                "merge_report": None,

                "matches": merge_report["matches"],

            })

        # -------------------------------------------------
        # Final report
        # -------------------------------------------------

        self.report["summary"]["secondary_tables"] = len(tables)
        self.report["summary"]["total_tables"] = len(tables) + 1
        self.report["summary"]["main_table"] = self.target.filename
        self.report["summary"]["table_names"] = [
            self.target.filename,
            *[t.filename for t in tables],
        ]

        self.report["summary"]["rows_final"] = result.n_rows
        self.report["summary"]["keys"] = keys
        self.report["summary"]["preserve_duplicates_columns"] = (
            preserve_duplicates_columns
        )

        self.report["execution_time"] = round(
            time.perf_counter() - start,
            3,
        )

        self.report["timestamp"] = datetime.now().isoformat()

        result.integration_report = self.report

        return result