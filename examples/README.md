# GenomeTableTools Examples

This example dataset demonstrates the complete GenomeTableTools workflow using a fictitious RSV (Respiratory Syncytial Virus) surveillance dataset inspired by GISAID metadata.

The examples cover:

- Laboratory registry updates
- Metadata integration
- Filtering
- Searching
- Annotation

## Workflow

```text
       sequencing_metadata.tsv
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
         ├──── patient_metadata.tsv
         │
         └──── date_location_metadata.tsv
         │
         ▼
      integrate
         │
         ▼
   RSV-AB_master.tsv
      ├──────────┐
      ▼          ▼
   filter       search
      │
      ▼
   annotate
```

## Steps

### 1. Update laboratory metadata

This example uses a small fictitious laboratory metadata reference to demonstrate how `registry update` processes newly added records. The reference contains 30 historical records, while the current sequencing metadata contains 36 records.

The six newly added records are resolved using laboratory information from the historical reference. All laboratory names, codes, accessions, and sample identifiers in this example are fictitious and are provided for demonstration purposes only.

```bash
genometabletools registry update \
    --input examples/demo_rsv/input/RSV-AB_sequencing_metadata.tsv \
    --reference examples/demo_rsv/input/laboratory_metadata.tsv \
    --output examples/demo_rsv/output/RSV-AB_laboratory_metadata.tsv \
    --new-records-output examples/demo_rsv/output/registry_new_records.tsv \
    --review-output examples/demo_rsv/output/registry_review.tsv
```
The command generates:

- `RSV-AB_laboratory_metadata.tsv`: complete updated laboratory metadata containing all 36 records.
- `registry_new_records.tsv`: the six records added during the current update.
- `registry_review.tsv`: records requiring manual review when laboratory metadata cannot be resolved unambiguously.

### 2. Integrate metadata

```bash
genometabletools integrate \
    examples/demo_rsv/input/RSV-AB_sequencing_metadata.tsv \
    examples/demo_rsv/output/RSV-AB_laboratory_metadata.tsv \
    examples/demo_rsv/input/RSV-AB_patient_metadata.tsv \
    examples/demo_rsv/input/RSV-AB_date_location_metadata.tsv \
    --keys "Accession ID" \
    --preserve_duplicates_columns comments \
    --output examples/demo_rsv/output/RSV-AB_master.tsv
```

### 3. Filter records

#### Filter RSV-A subtype records
```bash
genometabletools filter \
    examples/demo_rsv/output/RSV-AB_master.tsv \
	--where "Subtype=A" \
	--output examples/demo_rsv/output/RSV-AB_filter_st_A.tsv
```
#### Filter illumina-sequenced records
```bash
genometabletools filter \
	examples/demo_rsv/output/RSV-AB_master.tsv \
	--where "Sequencing technology contains illumina" \
	--output examples/demo_rsv/output/RSV-AB_filter_illumina.tsv
```
#### Filter RSV-B subtype with >90% genome coverage, and illumina-sequenced records
```bash
genometabletools filter \
	examples/demo_rsv/output/RSV-AB_master.tsv \
	--where "Subtype=B" \
	--where "Sequencing technology contains illumina" \
	--where "Sequence Length>=13703" \
	--output examples/demo_rsv/output/RSV-AB_filter_stB_illumina_cov90.tsv
```
#### Filter RSV-A records after 2018-01-01 from Galicia and Comunitat Valenciana
```bash
genometabletools filter \
    examples/demo_rsv/output/RSV-AB_master.tsv \
    --where "Subtype=A" \
    --where "Collection date after 2018-01-01" \
    --where "autonomous_community in Galicia,Comunitat Valenciana" \
    --output examples/demo_rsv/output/RSV-AB_filter_stA_date_region.tsv
```

### 4. Search records by "Accession ID"

```bash
genometabletools search \
	examples/demo_rsv/output/RSV-AB_master.tsv \
	--columns "Accession ID" \
	--values examples/demo_rsv/queries/accession_ids.txt \
	--output examples/demo_rsv/output/RSV-AB_search
```

### 5. Annotate metadata from a reference table

```bash
genometabletools annotate \
	examples/demo_rsv/output/RSV-AB_master.tsv \
	examples/demo_rsv/reference/institutions.tsv \
	--key "institution" \
	--columns institute_type \
	--output examples/demo_rsv/output/RSV-AB_annotation
```