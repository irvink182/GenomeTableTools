"""
table.py

Core Table class for GenomeTableTools.

Author: Irving Cancino
"""

from pathlib import Path
from datetime import datetime
import pandas as pd

from .io import read_table


class Table:
    """
    Main object representing a tabular dataset.
    """

    def __init__(self, filepath: str | Path):

        self.filepath = Path(filepath)
        self.filename = self.filepath.name
        self.extension = self.filepath.suffix.lower()

        # Metadata
        self.separator = None
        self.encoding = None
        self.sheet_name = None

        # Data
        self.df = None

        # Statistics
        # (calculated dynamically)

        self.loaded = False
        self.load_time = None

        self.load()

    def __repr__(self):
        return (
            "GenomeTableTools.Table(\n"
            f"  file='{self.filename}',\n"
            f"  rows={self.n_rows},\n"
            f"  columns={self.n_columns}\n"
            ")"
        )

    def __len__(self):
        return self.n_rows

    
    def __getitem__(self, key):
        return self.df[key]

    
    def __getattr__(self, name):
        """
        Delegate unknown attributes to the pandas DataFrame.
        """

        return getattr(self.df, name)

    def load(self):
        """
        Read table from disk.
        """

        self.df, metadata = read_table(self.filepath)

        self.separator = metadata.get("separator")
        self.encoding = metadata.get("encoding")
        self.sheet_name = metadata.get("sheet")

        self.loaded = True
        self.load_time = datetime.now()

    @property
    def shape(self):

        return self.df.shape

    @property
    def n_rows(self):
        return self.df.shape[0]

    @property
    def n_columns(self):
        return self.df.shape[1]

    @property
    def columns(self):
        return list(self.df.columns)

    @property
    def dtypes(self):
        return self.df.dtypes.to_dict()

    @property
    def empty(self):
        return self.df.empty

    @property
    def size(self):
        return self.df.size

    @property
    def index(self):
        return self.df.index

    @property
    def values(self):
        return self.df.values

    @property
    def memory_usage(self):

        return self.df.memory_usage(deep=True).sum()

    def head(self, n=5):
        return self.df.head(n)

    def tail(self, n=5):
        return self.df.tail(n)

    def sample(self, n=5):
        return self.df.sample(n)

    def info(self):

        print("="*60)
        print("GenomeTableTools")
        print("="*60)

        print(f"File:        {self.filename}")
        print(f"Rows:        {self.n_rows}")
        print(f"Columns:     {self.n_columns}")
        print(f"Format:      {self.extension}")
        separator = {
            "\t": "TAB",
            ",": "COMMA",
            ";": "SEMICOLON",
            "|": "PIPE"
        }.get(self.separator, self.separator)
        print(f"Separator:   {separator}")
        print(f"Encoding:    {self.encoding}")
        print(f"Memory:      {self.memory_usage/1024:.1f} KB")
        print()

        print("Columns")

        for col, dtype in self.dtypes.items():
            print(f"  {col:30} {dtype}")

    def save(self, output):

        from .io import write_table

        write_table(self.df, output)

    export = save

    def copy(self):
        """
        Return a deep copy of the current Table.
        """

        return Table.from_dataframe(
            self.df,
            template=self
        )

    @classmethod
    def from_dataframe(cls, df, template=None):
        """
        Create a Table object from an existing pandas DataFrame.
        
        Parameters
        ----------
        df : pandas.DataFrame
            DataFrame to wrap.

        template : Table, optional
            Existing Table from which metadata will be copied.

        Returns
        -------
        Table
        """

        obj = cls.__new__(cls)

        # No associated file
        obj.filepath = None
        obj.filename = "In-memory table"
        obj.extension = None

        # Metadata
        obj.separator = None
        obj.encoding = None
        obj.sheet_name = None

        if template is not None:
            obj.separator = template.separator
            obj.encoding = template.encoding
            obj.sheet_name = template.sheet_name

        # Data
        obj.df = df.copy()

        obj.loaded = True
        obj.load_time = datetime.now()

        obj.merge_report = None
        obj.search_report = None
        obj.concat_report = None
        obj.merge_report = None
        obj.search_report = None
        obj.annotation_report = None
        obj.integration_report = None
        obj.filter_report = None

        obj.history = []

        return obj

    @classmethod
    def concat(
        cls,
        *tables,
        ignore_index=True,
        verify_columns=True,
    ):

        """
        Concatenate two or more tables. 
        """

        from .concat import ConcatOperation

        return ConcatOperation(*tables).run(
            ignore_index=ignore_index,
            verify_columns=verify_columns,
        )

    def merge(
        self,
        other,
        keys,
        how="left",
        columns=None,
    ):

        from .merge import MergeOperation

        operation = MergeOperation(
            self,
            other,
        )

        return operation.run(
            keys=keys,
            how=how,
            columns=columns,
        )

    def search(
        self,
        columns,
        values,
        **kwargs,
    ):

        """
        Search rows matching a list of values.
        """

        from .search import SearchOperation
        operation = SearchOperation(self)

        return operation.run(
            columns=columns,
            values=values,
            **kwargs,
        )

    def annotate(
        self,
        reference,
        key,
        columns=None,
        exclude_columns=None,
        overwrite=False,
    ):

        """
        Annotate the current table using another reference table
        """

        from .annotate import AnnotationOperation

        operation = AnnotationOperation(
            self,
            reference,
        )

        return operation.run(
            key=key,
            columns=columns,
            exclude_columns=exclude_columns,
            overwrite=overwrite,
        )

    def integrate(
        self,
        *tables,
        keys,
        preserve_duplicates_columns=None,
    ):
        """
        Integrate one or more tables into the current table.
        """

        from .integrate import IntegrationOperation

        return IntegrationOperation(self).run(
            *tables,
            keys=keys,
            preserve_duplicates_columns=preserve_duplicates_columns,
        )

    def filter(
        self,
        *filters,
    ):
        """
        Filter rows according to one or more conditions.
        """

        from .filter import FilterOperation

        return FilterOperation(self).run(*filters)