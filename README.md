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
| `registry`* |  Update curated laboratory metadata using newly downloaded GISAID metadata.  |

*The `registry` module is specific to GISAID workflows. It updates curated laboratory metadata by combining newly downloaded GISAID sequencing metadata with an existing laboratory metadata reference. Known records are preserved, while new records are resolved using historical laboratory information and conservative parsing of GISAID virus names.*

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

## GISAID METADATA workflow

```text
     GISAID sequencing metadata
                +
     laboratory_metadata.tsv
       (curated reference)
                │
                ▼
         registry update
                │
       ┌────────┼────────┐
       ▼        ▼        ▼
 laboratory_  registry_  registry_
 metadata.tsv new_records.tsv review.tsv
       │
       ▼
    integrate
       │
       ▼
   master table
    ├──────────────┐
    ▼              ▼
 filter          search
    │              │
    └──────┬───────┘
           ▼
        annotate
```

The `registry update` workflow uses the existing curated laboratory metadata as a historical reference to resolve laboratory information for newly added GISAID records.

It generates three complementary outputs:

- `laboratory_metadata.tsv`: complete laboratory metadata table containing both existing and newly added records.
- `registry_new_records.tsv`: all records added during the current update, including a `review_fields` column indicating whether manual review is required.
- `registry_review.tsv`: subset of new records containing laboratory metadata fields that could not be resolved unambiguously and require manual curation.

Existing accessions retain their curated laboratory metadata. For new accessions, laboratory information is inferred only when supported by the historical reference and the structure of the GISAID virus name. Ambiguous or unresolved metadata are left for manual review rather than assigned automatically.

## Features

- Read and write TSV, CSV, TXT and Excel tables.
- Available as both a Python API and a command-line interface (CLI).
- Concatenate and integrate multiple tables.
- Filter rows using flexible text and numeric expressions.
- Search one or more columns for specific values or identifiers.
- Annotate tables using reference metadata.
- Update and curate laboratory metadata for GISAID workflows using historical laboratory information.

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

### 1. Update laboratory metadata from new GISAID records

```bash
genometabletools registry update \
    --input sequencing_metadata.tsv \
    --reference laboratory_metadata.tsv \
    --output laboratory_metadata_updated.tsv \
    --new-records-output registry_new_records.tsv \
    --review-output registry_review.tsv
```
For development or validation purposes, a curated metadata table can optionally be provided using `--validation`:

```bash
genometabletools registry update \
    --input sequencing_metadata.tsv \
    --reference laboratory_metadata_previous.tsv \
    --validation laboratory_metadata_curated.tsv \
    --output laboratory_metadata_updated.tsv \
    --new-records-output registry_new_records.tsv \
    --review-output registry_review.tsv
```

### 2. Concatenate tables with the same headers
```bash
genometabletools concat \
    Table1.tsv \
    Table2.tsv \
    --output concatenated_table.tsv
```
### 3. Search records by "column_name" using a list of records (one record per line)

```bash
genometabletools search \
    concatenated_table.tsv \
    --columns "Accession ID" \
    --values accession_ids.txt \
    --output table_search
```

### 4. Filter RSV-B with >90% genome coverage, and illumina-sequenced records
```bash
genometabletools filter \
    concatenated_table.tsv \
    --where "Subtype=B" \
    --where "Sequencing technology contains illumina" \
    --where "Sequence Length>=13700" \
    --output filtered_table.tsv
```

### 5. Filter RSV-A after 2018, only Galicia and Comunitat Valenciana, and no duplicated records
```bash
genometabletools filter \
    concatenated_table.tsv \
    --where "Subtype=A" \
    --where "Collection date after 2018-01-01" \
    --where "autonomous_community in Galicia,Comunitat Valenciana" \
    --where "Additional host information notcontains same patient" \
    --output filtered_table.tsv
```

*Additional `filter` operators include:* `contains`, `notcontains`, `startswith`, `notstartswith`, `endswith`, `notendswith`, `regex`, `notregex`, `isna`, `notna`, `before`, `after`, `between`, `in`, `>`, `<`, `>=`, `<=`, `=` and `!=`.


## Examples

A complete fictitious demonstration dataset is available in:

```text
examples/demo_rsv/
```

The example demonstrates a complete RSV metadata workflow, from raw GISAID metadata tables to an integrated master table, including registry generation, metadata integration, filtering, searching, and annotation.

See `examples/demo_rsv/README.md` for the complete workflow.
