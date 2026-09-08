# GenomeTableTools Examples

This example dataset demonstrates the complete GenomeTableTools workflow using a fictitious RSV (Respiratory Syncytial Virus) surveillance dataset inspired by GISAID metadata.

The examples cover:

- Registry generation
- Laboratory metadata parsing
- Metadata integration
- Filtering
- Searching
- Annotation

## Workflow

```Text
sequencing_metadata.tsv
patient_metadata.tsv
date_location_metadata.tsv
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
    RSV-AB_master_metadata.tsv
      ├──────────────┐
      ▼              ▼
   filter         search
      │
      ▼
   annotate
```
## Steps
### 1. Build registry

```bash
genometabletools registry build \
	examples/demo_rsv/input/RSV-AB_sequencing_metadata.tsv \
	--registry examples/demo_rsv/registry/
```

### 2. Parse laboratory metadata

```bash
genometabletools registry parse \
	examples/demo_rsv/input/RSV-AB_sequencing_metadata.tsv \
	--registry examples/demo_rsv/registry/ \
	--output examples/demo_rsv/input/RSV-AB_laboratory_metadata.tsv
```

### 3. Integrate metadata

```bash
genometabletools integrate \
	examples/demo_rsv/input/RSV-AB_sequencing_metadata.tsv \
	examples/demo_rsv/input/RSV-AB_laboratory_metadata.tsv \
	examples/demo_rsv/input/RSV-AB_patient_metadata.tsv \
	examples/demo_rsv/input/RSV-AB_date_location_metadata.tsv \
	--keys "Accession ID" \
	--preserve_duplicates_columns comments \
	--output examples/demo_rsv/output/RSV-AB_master.tsv
```

### 4. Filter records

#### Filter RSV-A subtype records
```bash
genometabletools filter \
	examples/demo_rsv/output/RSV-AB_master_metadata.tsv \
	--where "Subtype=A" \
	--output examples/demo_rsv/output/RSV-AB_filter_st_A.tsv
```
#### Filter illumina-sequenced records
```bash
genometabletools filter \
	examples/demo_rsv/output/RSV-AB_master_metadata.tsv \
	--where "Sequencing technology contains illumina" \
	--output examples/demo_rsv/output/RSV-AB_filter_illumina.tsv
```
#### Filter RSV-B subtype with >90% genome coverage, and illumina-sequenced records
```bash
genometabletools filter \
	examples/demo_rsv/output/RSV-AB_master_metadata.tsv \
	--where "Subtype=B" \
	--where "Sequencing technology contains illumina" \
	--where "Sequence Length>=13703" \
	--output examples/demo_rsv/output/RSV-AB_filter_stB_illumina_cov90.tsv
```
#### Filter RSV-A after 2025-10-12 and only Galicia and Comunitat Valenciana records
```bash
genometabletools filter \
    concatenated_table.tsv \
    --where "Subtype=A" \
    --where "Collection date after 2018-01-01" \
    --where "autonomous_community in Galicia,Comunitat Valenciana" \
    --output filtered_table.tsv
```

### 5. Search records by "Accession ID"

```bash
genometabletools search \
	examples/demo_rsv/output/RSV-AB_master_metadata.tsv \
	--columns "Accession ID" \
	--values examples/demo_rsv/queries/accession_ids.txt \
	--output examples/demo_rsv/output/RSV-AB_search
```

### 6. Annotate metadata from a reference table

```bash
genometabletools annotate \
	examples/demo_rsv/output/RSV-AB_master_metadata.tsv \
	examples/demo_rsv/reference/institutions.tsv \
	--key "institution" \
	--columns institute_type \
	--output examples/demo_rsv/output/RSV-AB_annotation
```