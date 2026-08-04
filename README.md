# GenomeTableTools

GenomeTableTools is a Python package and command-line toolkit for loading, managing, integrating, and curating genomic metadata tables.

It was originally developed to simplify large-scale GISAID metadata processing for respiratory virus surveillance, but it can be applied to any tabular dataset.

## Overview
GenomeTableTools provides a collection of modules for common tabular data management tasks, including table concatenation, integration, filtering, searching, and annotation.

| Module      | Description                  |
| ----------- | ---------------------------- |
| `concat`    | Concatenate two or more tables           |
| `integrate` | Integrate multiple metadata tables into a master table    |
| `filter`    | Filter rows using query expressions.                  |
| `search`    | Search one or more columns for specific values or identifiers.           |
| `annotate`  | Add metadata from a reference table.            |
| `registry`* | Build and manage laboratory registries from GISAID metadata.  |

*The `registry` module is specific to GISAID workflows. It generates and manages laboratory metadata (originating laboratories, submitters, and laboratory codes) from downloadable GISAID metadata.*

## Supported tabular formats
| Format | Read | Write |
| ------ | :--: | :---: |
| TSV    |   ✓  |   ✓   |
| CSV    |   ✓  |   ✓   |
| TXT    |   ✓  |   ✓   |
| XLSX   |   ✓  |   ✓   |


## Installation

Clone the repository and install GenomeTableTools in editable mode:

```bash
git clone https://github.com/irvink182/GenomeTableTools.git
cd GenomeTableTools
pip install -e .
```

Verify the installation:

```bash
genometabletools --help
```

## Workflow (GISAID METADATA)

```text
    GenomeTableTools Workflow

        Sequencing metadata
        Patient metadata
        Date/location metadata
                 │
                 ▼
         registry build
                 │
                 ▼
         registry parse
                 │
                 ▼
     laboratory_metadata.tsv
                 │
                 ▼
            integrate
                 │
                 ▼
        RSV-AB_master.tsv
          ├──────────────┐
          ▼              ▼
       filter         search
          │              │
          └──────┬───────┘
                 ▼
             annotate
```
## Features

- Read and write TSV, CSV, TXT and Excel tables.
- Available as both a Python API and a command-line interface (CLI).
- Concatenate and integrate multiple tables.
- Filter rows using flexible text and numeric expressions.
- Search one or more columns for specific values or identifiers.
- Annotate tables using reference metadata.
- Build and manage laboratory registries for GISAID workflows.

## Python API

```python
from genometabletools import Table

#Load metadata table
table = Table("metadata.tsv")

#Filter complete RSV-A genomes
filtered = table.filter(
    "Subtype=A",
    "Sequence Length>=15000"
)

filtered.save("RSV-A.tsv")
```
## Quick start

### 1. Concatenate tables with the same headers
```bash
genometabletools concat \
    Table1.tsv \
    Table2.tsv \
	--output concatenated_table.tsv
```
### 2. Search records by "column_name" using a list of records (one record per line)

```bash
genometabletools search \
    concatenated_table.tsv \
    --columns "Accession ID" \
    --values accession_ids.txt \
    --output table_search
```

### 3. Filter RSV-B with >90% genome coverage, and illumina-sequenced records
```bash
genometabletools filter \
    concatenated_table.tsv \
    --where "Subtype=B" \
    --where "Sequencing technology contains illumina" \
    --where "Sequence Length>=13700" \
    --output filtered_table.tsv
```
*Additional `filter` operators include:* `contains`, `startswith`, `endswith`, `regex`, `isna`, `notna`, `>`, `<`, `>=`, `<=`, `=` and `!=`.


## Examples

A complete demonstration dataset is available in:

```text
examples/demo_rsv/
```

The example demonstrates a complete RSV metadata workflow, from raw GISAID metadata tables to an integrated master table, including registry generation, metadata integration, filtering, searching, and annotation.

See `examples/demo_rsv/README.md` for the complete workflow.
