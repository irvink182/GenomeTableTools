"""
filter.py

Filtering operations for GenomeTableTools.
"""

from datetime import datetime
import time

import pandas as pd

import unicodedata

from .table import Table

###############################################################################
# Filter operation
###############################################################################


class FilterOperation:

    def __init__(self, table):

        self.table = table

        self.report = {
            "operation": "filter",
            "execution_time": None,
            "timestamp": None,
            "summary": {
                "rows_initial": table.n_rows,
                "rows_final": None,
                "rows_removed": None,
            },
            "filters": [],
        }

    def run(self, *filters):

        start = time.time()

        df = self.table.df

        mask = pd.Series(True, index=df.index)

        for expression in filters:

            column, operator, value = parse_filter(expression)

            mask &= apply_filter(
                df,
                column,
                operator,
                value,
            )

            self.report["filters"].append(expression)

        filtered_df = df.loc[mask].copy()

        result = Table.from_dataframe(
            filtered_df,
            template=self.table,
        )

        self.report["summary"]["rows_final"] = result.n_rows
        self.report["summary"]["rows_removed"] = (
            self.report["summary"]["rows_initial"]
            - result.n_rows
        )

        self.report["execution_time"] = round(
            time.time() - start,
            2,
        )

        self.report["timestamp"] = datetime.now().isoformat()

        result.filter_report = self.report

        return result


###############################################################################
# Filter parser
###############################################################################

TEXT_OPERATORS = {
    "=",
    "!=",
    "contains",
    "startswith",
    "endswith",
    "regex",
}

NUMERIC_OPERATORS = {
    ">=",
    "<=",
    ">",
    "<",
}

MISSING_OPERATORS = {
    "isna",
    "notna",
}

PARSE_OPERATORS = [
    " isna",
    " notna",
    " contains ",
    " startswith ",
    " endswith ",
    " regex ",
    ">=",
    "<=",
    "!=",
    ">",
    "<",
    "=",
]

OPERATORS = {

    "=": lambda s, v: s == v,
    "!=": lambda s, v: s != v,
    ">": lambda s, v: s > v,
    ">=": lambda s, v: s >= v,
    "<": lambda s, v: s < v,
    "<=": lambda s, v: s <= v,

    "contains": lambda s, v:
        s.str.contains(v, regex=False, na=False),

    "startswith": lambda s, v:
        s.str.startswith(v, na=False),

    "endswith": lambda s, v:
        s.str.endswith(v, na=False),

    "regex": lambda s, v:
        s.str.contains(v, regex=True, na=False),

    "isna": lambda s, _: s.isna(),
    "notna": lambda s, _: s.notna(),
}

def normalize_text(text):

    if pd.isna(text):
        return text

    text = str(text).casefold()

    # remove leading/trailing and duplicate spaces
    text = " ".join(text.split())

    # remove accents
    text = "".join(
        c for c in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(c)
    )

    return text

def normalize_series(series):
    """
    Normalize a pandas Series for text comparisons.
    """

    return series.map(normalize_text)

def parse_filter(expression):

    for op in PARSE_OPERATORS:

        if op in expression:

            if op.strip() in MISSING_OPERATORS:

                column = expression.replace(op, "").strip()

                return (
                    column,
                    op.strip(),
                    None,
                )

            column, value = expression.split(op, 1)

            return (
                column.strip(),
                op.strip(),
                value.strip(),
            )

    raise ValueError(f"Invalid filter: {expression}")

###############################################################################
# Filter evaluator
###############################################################################

def apply_filter(df, column, operator, value):

    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found.")

    series = df[column]

    # Numeric operators
    if operator in NUMERIC_OPERATORS:

        series = pd.to_numeric(series, errors="coerce")

        if series.isna().all():
            raise ValueError(
                f"Column '{column}' is not numeric."
            )

        value = float(value)

    # Text operators
    elif operator in TEXT_OPERATORS:

        series = normalize_series(series)
        value = normalize_text(value)

    # Missing-value operators
    elif operator in MISSING_OPERATORS:

        # Nothing to prepare
        pass

    else:
        raise ValueError(f"Unknown operator: {operator}")

    return OPERATORS[operator](series, value)