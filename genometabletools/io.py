"""
io.py

Input/Output utilities for GenomeTableTools
"""

from pathlib import Path
import csv

import pandas as pd


# -----------------------------------------------------
# Detect delimiter
# -----------------------------------------------------

def detect_separator(filepath):
    """
    Detect the delimiter of a text file.
    """

    with open(filepath, "r", encoding="utf-8") as f:
        sample = f.read(4096)

    dialect = csv.Sniffer().sniff(
        sample,
        delimiters=",\t;|"
    )

    return dialect.delimiter


# -----------------------------------------------------
# Read table
# -----------------------------------------------------

def read_table(filepath):

    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(
            f"File not found: {filepath}"
        )

    extension = filepath.suffix.lower()

    metadata = {
        "separator": None,
        "encoding": "utf-8",
        "sheet": None,
    }

    if extension == ".csv":

        metadata["separator"] = ","

        df = pd.read_csv(
            filepath,
            sep=",",
            dtype="string"
        )

    elif extension == ".tsv":

        metadata["separator"] = "\t"

        df = pd.read_csv(
            filepath,
            sep="\t",
            dtype="string"
        )

    elif extension == ".txt":

        sep = detect_separator(filepath)

        metadata["separator"] = sep

        df = pd.read_csv(
            filepath,
            sep=sep,
            dtype="string"
        )

    elif extension in [".xlsx", ".xls"]:

        df = pd.read_excel(
            filepath,
            dtype="string"
        )

        metadata["sheet"] = "Sheet1"

    else:

        raise ValueError(
            f"Unsupported file format: {extension}"
        )

    # Normalize empty strings and whitespace-only cells to missing values
    df = df.replace(r"^\s*$", pd.NA, regex=True)

    return df, metadata


# -----------------------------------------------------
# Write table
# -----------------------------------------------------

def write_table(df, output):

    output = Path(output)

    extension = output.suffix.lower()

    if extension == ".csv":

        df.to_csv(
            output,
            index=False
        )

    elif extension in [".tsv", ".txt"]:

        df.to_csv(
            output,
            sep="\t",
            index=False
        )

    elif extension == ".xlsx":

        df.to_excel(
            output,
            index=False
        )

    else:

        raise ValueError(
            f"Unsupported output format: {extension}"
        )