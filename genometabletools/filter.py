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
    "notcontains",
    "startswith",
    "notstartswith",
    "endswith",
    "notendswith",
    "regex",
    "notregex",
    "in",
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

DATE_OPERATORS = {
    "before",
    "after",
}

PARSE_OPERATORS = [
    " isna",
    " notna",
    " notcontains ",
    " contains ",
    " notstartswith ",
    " startswith ",
    " notendswith ",
    " endswith ",
    " notregex ",
    " regex ",
    " between ",
    " before ",
    " after ",
    " in ",
    ">=",
    "<=",
    "!=",
    ">",
    "<",
    "=",
]

def apply_in(series, value):
    """
    Apply an 'in' filter to a text Series.
    """

    values = [
        normalize_text(v)
        for v in value.split(",")
    ]

    return series.isin(values)

OPERATORS = {

    "=": lambda s, v: s == v,
    "!=": lambda s, v: s != v,
    ">": lambda s, v: s > v,
    ">=": lambda s, v: s >= v,
    "<": lambda s, v: s < v,
    "<=": lambda s, v: s <= v,

    "contains": lambda s, v:
        s.str.contains(v, regex=False, na=False),
    "notcontains": lambda s, v:
        ~s.str.contains(v, regex=False, na=False),

    "startswith": lambda s, v:
        s.str.startswith(v, na=False),
    "notstartswith": lambda s, v:
        ~s.str.startswith(v, na=False),

    "endswith": lambda s, v:
        s.str.endswith(v, na=False),
    "notendswith": lambda s, v:
        ~s.str.endswith(v, na=False),

    "regex": lambda s, v:
        s.str.regex(v, regex=True, na=False),
    "notregex": lambda s, v:
        ~s.str.regex(v, regex=False, na=False),

    "isna": lambda s, _: s.isna(),
    "notna": lambda s, _: s.notna(),
    "before": lambda s, v: s < v,
    "after": lambda s, v: s > v,
    "in": apply_in,
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
# Filter preparation
###############################################################################

def prepare_numeric(series):
    """
    Prepare a numeric Series.
    """

    series = pd.to_numeric(
        series,
        errors="coerce",
    )

    if series.isna().all():
        raise ValueError(
            "Column is not numeric."
        )

    return series


def prepare_datetime(series):
    """
    Prepare a datetime Series.
    """

    series = pd.to_datetime(
        series,
        errors="coerce",
    )

    if series.isna().all():
        raise ValueError(
            "Column is not datetime."
        )

    return series


def prepare_text(series):
    """
    Prepare a text Series.
    """

    return normalize_series(series)

###############################################################################
# Filter evaluator
###############################################################################
def apply_between(series, value):
    """
    Apply a between filter to a numeric or datetime Series.
    """

    start, end = map(
        str.strip,
        value.split(","),
    )

    # Try numeric
    try:
        numeric = prepare_numeric(series)

        return (
            (numeric >= float(start))
            &
            (numeric <= float(end))
        )

    except ValueError:
        pass

    # Try datetime
    try:
        dates = prepare_datetime(series)

        return (
            (dates >= pd.to_datetime(start))
            &
            (dates <= pd.to_datetime(end))
        )

    except ValueError:

        raise ValueError(
            "Between is only supported for numeric or datetime columns."
        )

def apply_filter(df, column, operator, value):

    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found.")

    series = df[column]

    # Numeric operators
    if operator in NUMERIC_OPERATORS:

        series = prepare_numeric(series)

        value = float(value)

    # Date operators
    elif operator in DATE_OPERATORS:

        series = prepare_datetime(series)

        if operator != "between":
            value = pd.to_datetime(value)

    # Text operators
    elif operator in TEXT_OPERATORS:

        series = normalize_series(series)
        value = normalize_text(value)

    # Missing-value operators
    elif operator in MISSING_OPERATORS:

        # Nothing to prepare
        pass

    # Between operator
    elif operator == "between":

        return apply_between(
            series,
            value,
        )
    
    else:
        raise ValueError(f"Unknown operator: {operator}")

    return OPERATORS[operator](series, value)