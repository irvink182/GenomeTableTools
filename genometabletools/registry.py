#!/usr/bin/env python3

"""
Laboratory metadata registry utilities.

GenomeTableTools
"""

import pandas as pd


COMMUNITY_PREFIXES = {
    "AN",
    "AR",
    "AS",
    "CB",
    "CL",
    "CM",
    "CN",
    "CT",
    "CV",
    "EX",
    "GA",
    "IB",
    "MC",
    "MD",
    "NA",
    "PV",
    "RI",
    "CE",
    "ML",
    "un",
    # Historical / alternative forms
    "MAD",
    "CVA",
    "PVA",
    "NC",
    "BC",
    "CAT",
    "VC",
}

###############################################################################
# I/O
###############################################################################

def load_metadata(metadata_file):

    return pd.read_csv(
        metadata_file,
        sep="\t",
        keep_default_na=False,
        dtype=str,
    )


###############################################################################
# IDENTIFIER PARSING
###############################################################################

def extract_identifier(virus_name):
    """
    Extract the sample identifier from a GISAID virus name.
    """

    if pd.isna(virus_name):
        return ""

    parts = str(virus_name).strip().split("/")

    if len(parts) < 4:
        return ""

    return parts[3].strip()


###############################################################################
# REGISTRY
###############################################################################

def split_known_and_new(
    metadata,
    reference,
    accession_column="Accession ID",
):
    """
    Split current metadata into accessions already present
    in the reference and newly observed accessions.
    """

    if accession_column not in metadata.columns:
        raise ValueError(
            f"Column not found in metadata: {accession_column}"
        )

    if accession_column not in reference.columns:
        raise ValueError(
            f"Column not found in reference: {accession_column}"
        )

    known_accessions = set(
        reference[accession_column]
        .dropna()
        .astype(str)
        .str.strip()
    )

    accessions = (
        metadata[accession_column]
        .astype("string")
        .str.strip()
    )

    is_known = accessions.isin(known_accessions)

    known = metadata.loc[is_known].copy()
    new = metadata.loc[~is_known].copy()

    return known, new

def build_lab_lookup(reference):
    """
    Build a historical lookup for each laboratory code.

    The lookup preserves both the unique historical metadata values
    and the individual relationships observed in the reference.
    """

    lookup = {}

    for lab_code, group in reference.groupby("lab_code"):

        if pd.isna(lab_code):
            continue

        lab_code = str(lab_code).strip().upper()

        if not lab_code:
            continue

        originating_labs = sorted(
            group["originating_lab"]
            .dropna()
            .astype(str)
            .str.strip()
            .replace("", pd.NA)
            .dropna()
            .unique()
        )

        submitter_codes = sorted(
            group["submitter_lab_code"]
            .dropna()
            .astype(str)
            .str.strip()
            .replace("", pd.NA)
            .dropna()
            .unique()
        )

        lab_metadata_fields = [
            "lab_code_normalized",
            "autonomous_community_code",
            "autonomous_community",
            "institution",
            "city",
        ]

        lab_metadata = {}

        for field in lab_metadata_fields:

            values = sorted(
                group[field]
                .dropna()
                .astype(str)
                .str.strip()
                .replace("", pd.NA)
                .dropna()
                .unique()
            )

            lab_metadata[field] = (
                values[0]
                if len(values) == 1
                else ""
            )

        records = []

        for _, row in group.iterrows():

            virus_name = str(
                row.get("Virus name", "")
            ).strip()

            identifier = extract_identifier(
                virus_name
            )

            originating_lab = str(
                row.get("originating_lab", "")
            ).strip()

            submitter_lab_code = str(
                row.get("submitter_lab_code", "")
            ).strip()

            records.append(
                {
                    "identifier": identifier,
                    "originating_lab": originating_lab,
                    "submitter_lab_code": submitter_lab_code,
                }
            )

        lookup[lab_code] = {
            "originating_labs": originating_labs,
            "submitter_lab_codes": submitter_codes,
            "lab_metadata": lab_metadata,
            "records": records,
        }

    return lookup

def strip_community_prefix(identifier):
    """
    Remove a known autonomous community prefix from an identifier.
    
    Examples
    --------
    CV-HGUV-12345     -> HGUV-12345
    MAD-GM3-7-13-1    -> GM3-7-13-1
    UN-ABC-123        -> ABC-123

    """

    if pd.isna(identifier):
        return ""

    identifier = str(identifier).strip()

    if not identifier:
        return ""

    for community in COMMUNITY_PREFIXES:

        for separator in ("-", "_"):

            prefix = community + separator

            if identifier.startswith(prefix):
                return identifier[len(prefix):]

    return identifier

def resolve_lab_code(
    identifier,
    known_lab_codes,
):
    """
    Resolve an identifier against known laboratory codes.

    Only explicit laboratory-code prefixes are accepted.
    Partial substring matches are not allowed.
    """

    identifier = strip_community_prefix(identifier)

    if not identifier:
        return ""

    identifier = identifier.upper()

    matches = []

    for lab_code in known_lab_codes:

        lab_code = str(lab_code).strip().upper()

        if not lab_code:
            continue

        if (
            identifier == lab_code
            or identifier.startswith(lab_code + "-")
            or identifier.startswith(lab_code + "_")
        ):
            matches.append(lab_code)

    if not matches:
        return ""

    # If overlapping known codes exist, prefer the most specific one.
    max_length = max(len(code) for code in matches)

    best_matches = [
        code
        for code in matches
        if len(code) == max_length
    ]

    if len(best_matches) == 1:
        return best_matches[0]

    return ""

def resolve_lab_metadata(
    lab_code,
    identifier,
    lab_lookup,
):
    """
    Resolve historical laboratory metadata for a laboratory code.

    Metadata is returned directly when the historical relationship
    is unambiguous.

    If the laboratory code has multiple historical relationships,
    records that explicitly encode the laboratory code in the
    identifier are used as additional evidence. A value is returned
    only when that subset is unambiguous.
    """

    if not lab_code:
        return {
            "originating_lab": "",
            "submitter_lab_code": "",
            "lab_code_normalized": "",
            "autonomous_community_code": "",
            "autonomous_community": "",
            "institution": "",
            "city": "",
        }

    lab_code = str(lab_code).strip().upper()

    if lab_code not in lab_lookup:
        return {
            "originating_lab": "",
            "submitter_lab_code": "",
            "lab_code_normalized": "",
            "autonomous_community_code": "",
            "autonomous_community": "",
            "institution": "",
            "city": "",
        }

    record = lab_lookup[lab_code]

    lab_metadata = record["lab_metadata"]
    originating_labs = record["originating_labs"]
    submitter_codes = record["submitter_lab_codes"]

    # ----------------------------------------------------------
    # Direct resolution from historical relationships
    # ----------------------------------------------------------

    originating_lab = (
        originating_labs[0]
        if len(originating_labs) == 1
        else ""
    )

    submitter_lab_code = (
        submitter_codes[0]
        if len(submitter_codes) == 1
        else ""
    )

    # ----------------------------------------------------------
    # Additional identifier-based resolution
    # ----------------------------------------------------------

    if not originating_lab or not submitter_lab_code:

        stripped_identifier = strip_community_prefix(
            identifier
        ).upper()

        explicit_lab_code = (
            stripped_identifier == lab_code
            or stripped_identifier.startswith(
                lab_code + "-"
            )
            or stripped_identifier.startswith(
                lab_code + "_"
            )
        )

        if explicit_lab_code:

            matching_records = []

            for historical_record in record["records"]:

                historical_identifier = (
                    strip_community_prefix(
                        historical_record["identifier"]
                    )
                    .upper()
                )

                historical_explicit = (
                    historical_identifier == lab_code
                    or historical_identifier.startswith(
                        lab_code + "-"
                    )
                    or historical_identifier.startswith(
                        lab_code + "_"
                    )
                )

                if historical_explicit:
                    matching_records.append(
                        historical_record
                    )

            if matching_records:

                if not originating_lab:

                    historical_originating_labs = sorted(
                        {
                            r["originating_lab"]
                            for r in matching_records
                            if r["originating_lab"]
                        }
                    )

                    if len(historical_originating_labs) == 1:
                        originating_lab = (
                            historical_originating_labs[0]
                        )

                if not submitter_lab_code:

                    historical_submitter_codes = sorted(
                        {
                            r["submitter_lab_code"]
                            for r in matching_records
                            if r["submitter_lab_code"]
                        }
                    )

                    if len(historical_submitter_codes) == 1:
                        submitter_lab_code = (
                            historical_submitter_codes[0]
                        )

    return {
        "originating_lab": originating_lab,
        "submitter_lab_code": submitter_lab_code,
        "lab_code_normalized": lab_metadata[
            "lab_code_normalized"
        ],
        "autonomous_community_code": lab_metadata[
            "autonomous_community_code"
        ],
        "autonomous_community": lab_metadata[
            "autonomous_community"
        ],
        "institution": lab_metadata[
            "institution"
        ],
        "city": lab_metadata[
            "city"
        ],
    }

def build_submitter_lookup(reference):
    """
    Build a historical lookup from submitter laboratory codes
    to submitter laboratory names.

    A name is retained only when the historical relationship
    is unambiguous.
    """

    lookup = {}

    for submitter_code, group in reference.groupby(
        "submitter_lab_code"
    ):

        if pd.isna(submitter_code):
            continue

        submitter_code = str(
            submitter_code
        ).strip().upper()

        if not submitter_code:
            continue

        names = sorted(
            group["submitter_lab_name"]
            .dropna()
            .astype(str)
            .str.strip()
            .replace("", pd.NA)
            .dropna()
            .unique()
        )

        lookup[submitter_code] = (
            names[0]
            if len(names) == 1
            else ""
        )

    return lookup

def registry_update(
    metadata_file,
    reference_file,
    validation_file=None,
    output_file=None,
    review_output_file=None,
    new_records_output_file=None,

):
    """
    Update laboratory metadata using a historical curated reference.

    New accessions are identified by comparing the current GISAID
    metadata against the historical laboratory metadata. Laboratory
    codes are resolved from the Virus name using known laboratory
    codes, and associated metadata is recovered from the historical
    reference when the relationship is unambiguous.

    An optional curated validation file can be used to evaluate
    laboratory metadata predictions.
    """

    # --------------------------------------------------------------
    # Load input data
    # --------------------------------------------------------------

    metadata = load_metadata(metadata_file)
    reference = load_metadata(reference_file)

    # --------------------------------------------------------------
    # Identify known and new accessions
    # --------------------------------------------------------------

    known, new = split_known_and_new(
        metadata,
        reference,
    )

    # --------------------------------------------------------------
    # Extract sample identifiers
    # --------------------------------------------------------------

    new["identifier"] = (
        new["Virus name"]
        .map(extract_identifier)
    )

    # --------------------------------------------------------------
    # Build historical laboratory lookup
    # --------------------------------------------------------------

    lab_lookup = build_lab_lookup(reference)

    known_lab_codes = set(lab_lookup)

    submitter_lookup = build_submitter_lookup(
        reference
    )

    # --------------------------------------------------------------
    # Resolve laboratory codes
    # --------------------------------------------------------------

    new["predicted_lab_code"] = (
        new["identifier"]
        .map(
            lambda x: resolve_lab_code(
                x,
                known_lab_codes,
            )
        )
    )

    # --------------------------------------------------------------
    # Resolve historical laboratory metadata
    # --------------------------------------------------------------

    resolved_metadata = new.apply(
        lambda row: resolve_lab_metadata(
            row["predicted_lab_code"],
            row["identifier"],
            lab_lookup,
        ),
        axis=1,
    )

    new["predicted_originating_lab"] = (
        resolved_metadata.map(
            lambda x: x["originating_lab"]
        )
    )

    new["predicted_submitter_lab_code"] = (
        resolved_metadata.map(
            lambda x: x["submitter_lab_code"]
        )
    )

    new["predicted_lab_code_normalized"] = (
        resolved_metadata.map(
            lambda x: x["lab_code_normalized"]
        )
    )

    new["predicted_autonomous_community_code"] = (
        resolved_metadata.map(
            lambda x: x["autonomous_community_code"]
        )
    )

    new["predicted_autonomous_community"] = (
        resolved_metadata.map(
            lambda x: x["autonomous_community"]
        )
    )

    new["predicted_institution"] = (
        resolved_metadata.map(
            lambda x: x["institution"]
        )
    )

    new["predicted_city"] = (
        resolved_metadata.map(
            lambda x: x["city"]
        )
    )

    new["predicted_submitter_lab_name"] = (
        new["predicted_submitter_lab_code"]
        .map(
            lambda x: submitter_lookup.get(
                str(x).strip().upper(),
                "",
            )
        )
    )

    # --------------------------------------------------------------
    # Build updated laboratory metadata
    # --------------------------------------------------------------

    updated = metadata.copy()

    # Preserve curated metadata for known accessions
    reference_columns = [
        column
        for column in reference.columns
        if column != "Virus name"
    ]

    updated = updated.merge(
        reference[reference_columns],
        on="Accession ID",
        how="left",
    )

    # Add predictions for new accessions
    new_predictions = new[
        [
            "Accession ID",
            "identifier",
            "predicted_originating_lab",
            "predicted_lab_code",
            "predicted_lab_code_normalized",
            "predicted_autonomous_community_code",
            "predicted_autonomous_community",
            "predicted_institution",
            "predicted_city",
            "predicted_submitter_lab_code",
            "predicted_submitter_lab_name",
        ]
    ].copy()

    new_predictions = new_predictions.rename(
        columns={
            "identifier": "predicted_identifier",
        }
    )

    updated = updated.merge(
        new_predictions,
        on="Accession ID",
        how="left",
    )

    updated["identifier"] = (
        updated["identifier"]
        .fillna(updated["predicted_identifier"])
    )

    # Fill laboratory metadata for resolved new accessions
    prediction_fields = {
        "originating_lab": "predicted_originating_lab",
        "lab_code": "predicted_lab_code",
        "lab_code_normalized": "predicted_lab_code_normalized",
        "autonomous_community_code": "predicted_autonomous_community_code",
        "autonomous_community": "predicted_autonomous_community",
        "institution": "predicted_institution",
        "city": "predicted_city",
        "submitter_lab_code": "predicted_submitter_lab_code",
        "submitter_lab_name": "predicted_submitter_lab_name",
    }

    for field, predicted_field in prediction_fields.items():
        updated[field] = (
            updated[field]
            .fillna(updated[predicted_field])
        )

    # Remove temporary prediction columns
    updated = updated.drop(
        columns=[
            "predicted_identifier",
            *prediction_fields.values(),
        ]
    )

    # Final laboratory metadata columns
    output_columns = [
        "Accession ID",
        "Virus name",
        "identifier",
        "originating_lab",
        "lab_code",
        "lab_code_normalized",
        "autonomous_community_code",
        "autonomous_community",
        "institution",
        "city",
        "submitter_lab_code",
        "submitter_lab_name",
        "submitter_name",
        "laboratory_comments",
    ]

    updated = updated[output_columns]

    # --------------------------------------------------------------
    # Build new records and manual review tables
    # --------------------------------------------------------------

    review_fields = [
        "originating_lab",
        "lab_code",
        "lab_code_normalized",
        "autonomous_community_code",
        "autonomous_community",
        "institution",
        "city",
        "submitter_lab_code",
        "submitter_lab_name",
    ]

    new_accessions = set(
        new["Accession ID"]
    )

    new_records = updated[
        updated["Accession ID"].isin(new_accessions)
    ].copy()

    missing_review_fields = (
        new_records[review_fields]
        .fillna("")
        .eq("")
    )

    # Describe which fields require manual review
    new_records["review_fields"] = (
        missing_review_fields
        .apply(
            lambda row: (
                ";".join(
                    field
                    for field, missing in row.items()
                    if missing
                )
                or "no_review"
            ),
            axis=1,
        )
    )

    # Manual review is a subset of the new records
    review = new_records[
        new_records["review_fields"] != "no_review"
    ].copy()

    review_columns = [
        "Accession ID",
        "Virus name",
        "identifier",
        "originating_lab",
        "lab_code",
        "lab_code_normalized",
        "autonomous_community_code",
        "autonomous_community",
        "institution",
        "city",
        "submitter_lab_code",
        "submitter_lab_name",
        "review_fields",
    ]

    new_records = new_records[review_columns]

    review = review[review_columns]

    # --------------------------------------------------------------
    # Validate dataset integrity
    # --------------------------------------------------------------

    if len(updated) != len(metadata):
        raise ValueError(
            "Updated laboratory metadata does not contain "
            "the same number of records as the input metadata."
        )

    if set(updated["Accession ID"]) != set(metadata["Accession ID"]):
        raise ValueError(
            "Updated laboratory metadata does not contain "
            "the same accessions as the input metadata."
        )

    # --------------------------------------------------------------
    # Validate preservation of historical metadata
    # --------------------------------------------------------------

    historical_fields = [
        "originating_lab",
        "lab_code",
        "lab_code_normalized",
        "autonomous_community_code",
        "autonomous_community",
        "institution",
        "city",
        "submitter_lab_code",
        "submitter_lab_name",
        "submitter_name",
        "laboratory_comments",
    ]

    historical_check = updated[
        updated["Accession ID"].isin(
            reference["Accession ID"]
        )
    ][
        ["Accession ID"] + historical_fields
    ].merge(
        reference[
            ["Accession ID"] + historical_fields
        ],
        on="Accession ID",
        suffixes=("_updated", "_reference"),
    )

    changed = pd.Series(
        False,
        index=historical_check.index,
    )

    for field in historical_fields:

        updated_values = (
            historical_check[f"{field}_updated"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        reference_values = (
            historical_check[f"{field}_reference"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        changed |= (
            updated_values != reference_values
        )

    historical_changed = changed.sum()

    # --------------------------------------------------------------
    # Validate dataset integrity
    # --------------------------------------------------------------

    if len(updated) != len(metadata):
        raise ValueError(
            "Updated laboratory metadata does not contain "
            "the same number of records as the input metadata."
        )

    if set(updated["Accession ID"]) != set(metadata["Accession ID"]):
        raise ValueError(
            "Updated laboratory metadata does not contain "
            "the same accessions as the input metadata."
        )

    # --------------------------------------------------------------
    # Summary statistics
    # --------------------------------------------------------------

    resolved = (
        new["predicted_lab_code"] != ""
    ).sum()

    unresolved = (
        new["predicted_lab_code"] == ""
    ).sum()

    originating_resolved = (
        new["predicted_originating_lab"] != ""
    ).sum()

    submitter_resolved = (
        new["predicted_submitter_lab_code"] != ""
    ).sum()

    # --------------------------------------------------------------
    # Report
    # --------------------------------------------------------------

    print("\nGenomeTableTools - Registry update")
    print("=" * 50)

    print("\nDataset")
    print("-" * 50)
    print(
        f"Current metadata        : "
        f"{len(metadata):>8,}"
    )
    print(
        f"Reference records       : "
        f"{len(reference):>8,}"
    )
    print(
        f"Existing accessions     : "
        f"{len(known):>8,}"
    )
    print(
        f"New accessions          : "
        f"{len(new):>8,}"
    )
    print(
        f"Resolved                : "
        f"{resolved:>8,}"
    )
    print(
        f"Unresolved              : "
        f"{unresolved:>8,}"
    )

    no_review_count = (
        new_records["review_fields"]
        .eq("no_review")
        .sum()
    )
    
    resolved_count = (
        new["predicted_lab_code"] != ""
    ).sum()

    unresolved_count = (
        new["predicted_lab_code"] == ""
    ).sum()

    no_review_count = (
        new_records["review_fields"]
        .eq("no_review")
        .sum()
    )

    print("\nNew records")
    print("-" * 50)
    print(
        f"Laboratory resolved     : "
        f"{resolved_count:>8,}"
    )
    print(
        f"Laboratory unresolved   : "
        f"{unresolved_count:>8,}"
    )
    print(
        f"No review required      : "
        f"{no_review_count:>8,}"
    )
    print(
        f"Manual review required  : "
        f"{len(review):>8,}"
    )

    print("\nHistorical metadata resolution")
    print("-" * 50)
    print(
        f"Originating lab  : "
        f"{originating_resolved:>8,} / {len(new):,}"
    )
    print(
        f"Submitter lab    : "
        f"{submitter_resolved:>8,} / {len(new):,}"
    )
    print("\nLaboratory metadata fields")
    print("-" * 50)

    for field in [
        "lab_code_normalized",
        "autonomous_community_code",
        "autonomous_community",
        "institution",
        "city",
    ]:
        resolved_field = (
            new[f"predicted_{field}"] != ""
        ).sum()

        print(
            f"{field:<28}: "
            f"{resolved_field:>4} / {len(new)}"
        )


    submitter_name_resolved = (
        new["predicted_submitter_lab_name"] != ""
    ).sum()

    print(
        f"Submitter lab name: "
        f"{submitter_name_resolved:>8,} / {len(new):,}"
    )

    for field in review_fields:

        missing = (
            review[field]
            .fillna("")
            .eq("")
            .sum()
        )

        if missing:
            print(
                f"{field:<28}: "
                f"{missing:>8,}"
            )

    # --------------------------------------------------------------
    # Optional validation
    # --------------------------------------------------------------

    if validation_file:

        validation = load_metadata(validation_file)

        validation_subset = validation[
            [
                "Accession ID",
                "lab_code",
                "originating_lab",
                "submitter_lab_code",
            ]
        ].copy()

        validation_subset = validation_subset.rename(
            columns={
                "lab_code": "true_lab_code",
                "originating_lab": "true_originating_lab",
                "submitter_lab_code": "true_submitter_lab_code",
            }
        )

        evaluated = new.merge(
            validation_subset,
            on="Accession ID",
            how="inner",
        )

        # ----------------------------------------------------------
        # Normalize validation fields
        # ----------------------------------------------------------

        evaluated["predicted_lab_code"] = (
            evaluated["predicted_lab_code"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
        )

        evaluated["true_lab_code"] = (
            evaluated["true_lab_code"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
        )

        for column in [
            "predicted_originating_lab",
            "true_originating_lab",
            "predicted_submitter_lab_code",
            "true_submitter_lab_code",
        ]:
            evaluated[column] = (
                evaluated[column]
                .fillna("")
                .astype(str)
                .str.strip()
            )

        # ----------------------------------------------------------
        # Laboratory-code validation
        # ----------------------------------------------------------

        resolved_mask = (
            evaluated["predicted_lab_code"] != ""
        )

        correct_mask = (
            resolved_mask
            & (
                evaluated["predicted_lab_code"]
                == evaluated["true_lab_code"]
            )
        )

        incorrect_mask = (
            resolved_mask
            & (
                evaluated["predicted_lab_code"]
                != evaluated["true_lab_code"]
            )
        )

        unresolved_mask = ~resolved_mask

        correct = correct_mask.sum()
        incorrect = incorrect_mask.sum()
        validation_unresolved = unresolved_mask.sum()

        resolved_total = correct + incorrect

        accuracy = (
            100 * correct / resolved_total
            if resolved_total
            else 0
        )

        # ----------------------------------------------------------
        # Originating-laboratory validation
        # ----------------------------------------------------------

        originating_resolved_mask = (
            evaluated["predicted_originating_lab"] != ""
        )

        originating_correct_mask = (
            originating_resolved_mask
            & (
                evaluated["predicted_originating_lab"]
                == evaluated["true_originating_lab"]
            )
        )

        originating_incorrect_mask = (
            originating_resolved_mask
            & (
                evaluated["predicted_originating_lab"]
                != evaluated["true_originating_lab"]
            )
        )

        originating_correct = (
            originating_correct_mask.sum()
        )

        originating_incorrect = (
            originating_incorrect_mask.sum()
        )

        originating_unresolved = (
            ~originating_resolved_mask
        ).sum()

        # ----------------------------------------------------------
        # Submitter-laboratory validation
        # ----------------------------------------------------------

        submitter_resolved_mask = (
            evaluated["predicted_submitter_lab_code"] != ""
        )

        submitter_correct_mask = (
            submitter_resolved_mask
            & (
                evaluated["predicted_submitter_lab_code"]
                == evaluated["true_submitter_lab_code"]
            )
        )

        submitter_incorrect_mask = (
            submitter_resolved_mask
            & (
                evaluated["predicted_submitter_lab_code"]
                != evaluated["true_submitter_lab_code"]
            )
        )

        submitter_correct = (
            submitter_correct_mask.sum()
        )

        submitter_incorrect = (
            submitter_incorrect_mask.sum()
        )

        submitter_unresolved = (
            ~submitter_resolved_mask
        ).sum()

        # ----------------------------------------------------------
        # Validation report
        # ----------------------------------------------------------

        print("\nLaboratory validation")
        print("-" * 50)

        print(
            f"Samples evaluated: {len(evaluated):>8,}"
        )
        print(
            f"Correct          : {correct:>8,}"
        )
        print(
            f"Incorrect        : {incorrect:>8,}"
        )
        print(
            f"Unresolved       : "
            f"{validation_unresolved:>8,}"
        )
        print(
            f"Accuracy         : {accuracy:>7.2f}%"
        )

        print("\nOriginating laboratory validation")
        print("-" * 50)

        print(
            f"Correct          : "
            f"{originating_correct:>8,}"
        )
        print(
            f"Incorrect        : "
            f"{originating_incorrect:>8,}"
        )
        print(
            f"Unresolved       : "
            f"{originating_unresolved:>8,}"
        )

        print("\nSubmitter laboratory validation")
        print("-" * 50)

        print(
            f"Correct          : "
            f"{submitter_correct:>8,}"
        )
        print(
            f"Incorrect        : "
            f"{submitter_incorrect:>8,}"
        )
        print(
            f"Unresolved       : "
            f"{submitter_unresolved:>8,}"
        )

        # ----------------------------------------------------------
        # Incorrect laboratory-code assignments
        # ----------------------------------------------------------

        if incorrect > 0:

            errors = evaluated.loc[
                incorrect_mask,
                [
                    "Accession ID",
                    "Virus name",
                    "identifier",
                    "predicted_lab_code",
                    "true_lab_code",
                ],
            ]

            print(
                "\nIncorrect laboratory assignments"
            )
            print("-" * 50)

            print(
                errors.to_string(
                    index=False
                )
            )

        # ----------------------------------------------------------
        # Incorrect originating-laboratory assignments
        # ----------------------------------------------------------

        if originating_incorrect > 0:

            originating_errors = evaluated.loc[
                originating_incorrect_mask,
                [
                    "Accession ID",
                    "Virus name",
                    "identifier",
                    "predicted_lab_code",
                    "predicted_originating_lab",
                    "true_originating_lab",
                ],
            ]

            print(
                "\nIncorrect originating laboratory assignments"
            )
            print("-" * 50)

            print(
                originating_errors.to_string(
                    index=False
                )
            )

        # ----------------------------------------------------------
        # Incorrect submitter-laboratory assignments
        # ----------------------------------------------------------

        if submitter_incorrect > 0:

            submitter_errors = evaluated.loc[
                submitter_incorrect_mask,
                [
                    "Accession ID",
                    "Virus name",
                    "identifier",
                    "predicted_lab_code",
                    "predicted_submitter_lab_code",
                    "true_submitter_lab_code",
                ],
            ]

            print(
                "\nIncorrect submitter laboratory assignments"
            )
            print("-" * 50)

            print(
                submitter_errors.to_string(
                    index=False
                )
            )

        # ----------------------------------------------------------
        # Unresolved laboratory codes
        # ----------------------------------------------------------

        if validation_unresolved > 0:

            unresolved_cases = evaluated.loc[
                unresolved_mask,
                [
                    "Accession ID",
                    "Virus name",
                    "identifier",
                    "predicted_lab_code",
                    "true_lab_code",
                ],
            ]

            print(
                "\nUnresolved - manual review required"
            )
            print("-" * 50)

            print(
                unresolved_cases.to_string(
                    index=False
                )
            )

    print("=" * 50)

    # --------------------------------------------------------------
    # Write outputs
    # --------------------------------------------------------------

    if output_file:
        updated.to_csv(
            output_file,
            sep="\t",
            index=False,
        )

    if new_records_output_file:
        new_records.to_csv(
            new_records_output_file,
            sep="\t",
            index=False,
        )

    if review_output_file:
        review.to_csv(
            review_output_file,
            sep="\t",
            index=False,
        )

    if (
        output_file
        or new_records_output_file
        or review_output_file
    ):
        print("\nOutput")
        print("-" * 50)

        if output_file:
            print(
                f"Laboratory metadata: "
                f"{output_file}"
            )

        if new_records_output_file:
            print(
                f"New records        : "
                f"{new_records_output_file}"
            )

        if review_output_file:
            print(
                f"Manual review      : "
                f"{review_output_file}"
            )

    return updated
