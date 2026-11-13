# Changelog

All notable changes to GenomeTableTools will be documented in this file.

## [1.3.0]

### Added

- Added the new `registry update` command for updating curated laboratory metadata from newly downloaded GISAID sequencing metadata.
- Added historical laboratory metadata resolution for newly added accessions.
- Added conservative laboratory code resolution based on known laboratory codes and GISAID virus name identifiers.
- Added field-level resolution of laboratory metadata, including:
  - originating laboratory
  - laboratory code
  - normalized laboratory code
  - autonomous community code
  - autonomous community
  - institution
  - city
  - submitter laboratory code
  - submitter laboratory name
- Added `registry_new_records.tsv` output containing all records introduced during the current registry update.
- Added `registry_review.tsv` output containing new records that require manual curation.
- Added a `review_fields` column to identify unresolved laboratory metadata fields.
- Added optional `--validation` support for evaluating laboratory assignments against a curated metadata table.
- Added a fully fictitious RSV demonstration dataset for the updated registry workflow.

### Changed

- Redesigned the laboratory registry workflow around a curated `laboratory_metadata.tsv` reference.
- Existing accessions now preserve their curated laboratory metadata without modification.
- New accessions are resolved using historical laboratory relationships and conservative parsing of GISAID virus names.
- Laboratory metadata are resolved independently at field level, allowing unambiguous fields to be retained when other fields require manual review.
- Updated the registry command-line interface to use an explicit `--input` argument.
- Updated the RSV example workflow to use `registry update` before metadata integration.
- Updated the main documentation and example documentation to reflect the new registry workflow.

### Removed

- Removed the previous `registry build` workflow.
- Removed the previous `registry parse` workflow.
- Removed the legacy automatic generation and use of:
  - `laboratories.tsv`
  - `submitters.tsv`
  - `lab_aliases.tsv`
- Removed legacy registry candidate and conflict outputs used by the previous parsing workflow.
- Removed the legacy registry files and directories from the RSV demonstration dataset.

### Notes

The registry workflow prioritizes precision over automatic coverage. Laboratory metadata are assigned only when supported unambiguously by the curated historical reference and the structure of the GISAID virus name. Ambiguous or unresolved fields are left for manual review rather than assigned automatically.

The demonstration dataset included in `examples/demo_rsv/` is entirely fictitious and does not contain real GISAID records or curated laboratory metadata.