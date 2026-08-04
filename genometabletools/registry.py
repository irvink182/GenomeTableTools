#!/usr/bin/env python3

"""
Generate laboratories.tsv and submitters.tsv from a GISAID submitters file.

GenomeTableTools
"""

from pathlib import Path
from datetime import datetime
import re
import pandas as pd
import csv


###############################################################################
# CONSTANT VARIABLES
###############################################################################

# 1. Communities

COMMUNITIES = {
    "AN": "Andalucia",
    "AR": "Aragon",
    "AS": "Asturias",
    "CB": "Cantabria",
    "CL": "Castilla y Leon",
    "CM": "Castilla-La Mancha",
    "CN": "Canarias",
    "CT": "Catalunya",
    "CV": "Comunitat Valenciana",
    "EX": "Extremadura",
    "GA": "Galicia",
    "IB": "Illes Balears",
    "MC": "Region de Murcia",
    "MD": "Comunidad de Madrid",
    "NA": "Navarra",
    "PV": "Pais Vasco",
    "RI": "La Rioja",
    "CE": "Ceuta",
    "ML": "Melilla",
    "UN": "Unknown",
}

# 2. Communities aliases

COMMUNITY_ALIASES = {
    "NC" : "NA",   # Navarra
    "PVA": "PV",  # si alguna vez aparece
    "BC" : "PV", #Basque country = pais vasco
    "CAT": "CT",  # si apareciera Cataluña en otro formato
}

###############################################################################
# REGISTRY I/O
###############################################################################

# 1. Load curated metadata tables

def load_registry(registry_dir):

    labs = pd.read_csv(
        registry_dir / "laboratories.tsv",
        sep="\t",
        keep_default_na=False,
        dtype=str,
    )

    submitters = pd.read_csv(
        registry_dir / "submitters.tsv",
        sep="\t",
        keep_default_na=False,
        dtype=str,
    )

    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------

    lab_metadata = (
        labs[
            [
                "lab_code",
                "lab_code_normalized",
                "autonomous_community",
                "autonomous_community_code",
                "institution",
                "originating_lab",
                "city",
                "submitter_lab_code",
                "laboratory_comments",
            ]
        ]
        .drop_duplicates("lab_code")
    )

    laboratories_lookup = (
        lab_metadata
        .set_index("lab_code")
        .to_dict("index")
    )

    submitter_metadata = (
        submitters[
            [
                "submitter_lab_code",
                "submitter_lab_name",
                "submitter_name",
            ]
        ]
        .drop_duplicates("submitter_lab_code")
    )

    submitters_lookup = (
        submitter_metadata
        .set_index("submitter_lab_code")
        .to_dict("index")
    )

    return (
        labs,
        submitters,
        {
            "laboratories": laboratories_lookup,
            "submitters": submitters_lookup,
        },
    )


def load_lab_aliases(path):
    """
    Load curated laboratory aliases.

    Returns
    -------
    dict
        Mapping:
            identifier -> lab_code
    """

    identifier_aliases = {}

    with open(path, newline="", encoding="utf-8") as fh:

        reader = csv.DictReader(fh, delimiter="\t")

        for row in reader:

            identifier = row["identifier"].strip().upper()
            lab_code = row["lab_code"].strip().upper()

            if identifier and lab_code:
                identifier_aliases[identifier] = lab_code

    return identifier_aliases

###############################################################################
# PARSER
###############################################################################

# 1. Extract identifier

def extract_identifier(virus_name):

    if pd.isna(virus_name):
        return ""

    parts = str(virus_name).split("/")

    if len(parts) < 4:
        return ""

    return parts[3]

# 2. Extract community
def extract_community(identifier):

    if not identifier:
        return ""

    identifier = identifier.upper()

    # Unknown community
    if identifier.startswith("UN-"):
        return "UN"

    # Special prefixes
    if identifier.startswith("CVA_"):
        return "CV"

    if identifier.startswith("VC"):
        return "CV"

    if identifier.startswith("MAD"):
        return "MD"

    if identifier.startswith("PVA-"):
        return "PV"

    m = re.match(r"^([A-Z]{2})-", identifier)
    if m:
        community = m.group(1)
        return COMMUNITY_ALIASES.get(community, community)

    return ""

# 3. Extract lab_code
def extract_lab_code(
    identifier,
    identifier_aliases,
):
    """
    Extract laboratory code.

    Priority
    --------
    1. Exact identifier aliases (lab_aliases.tsv)
    2. Prefix aliases
    3. Regex inference from identifier
    4. Unknown ("")
    """

    # ------------------------------------------------------------
    # 1. Curated originating laboratory (highest priority)
    # ------------------------------------------------------------

    if identifier in identifier_aliases:
        return identifier_aliases[identifier]

    ####identifier####
    ident = identifier.strip().upper()

    if ident in identifier_aliases:
        return identifier_aliases[ident]

    if not identifier:
        return ""

    x = identifier.upper()

    # ------------------------------------------------------------
    # Normalization
    # ------------------------------------------------------------

    if x.startswith("UN-"):
        x = x[3:]

    m = re.match(r"^[A-Z]{2}-(.+)$", x)
    if m:
        x = m.group(1)

    # ------------------------------------------------------------
    # 2. Identifier aliases
    # ------------------------------------------------------------

    for prefix, lab_code in identifier_aliases.items():
        if x.startswith(prefix.upper()):
            return lab_code

    # ------------------------------------------------------------
    # 3. Regex inference
    # ------------------------------------------------------------

    regex_patterns = [
        r"^CVA_([A-Z0-9]+)-",
        r"^(MAD)\d+-",
        r"^([A-Z0-9_]+)_\d+(?:REP)?(?:_[A-Z]+)?$",
        r"^([A-Z]+)\d+$",
        r"^([A-Z0-9]+)-\d+$",
        r"^([A-Z0-9]+)-",
        r"^([A-Z]+)\d+",
    ]

    for pattern in regex_patterns:
        m = re.match(pattern, x)
        if m:
            return m.group(1)

    # ------------------------------------------------------------
    # Unknown
    # ------------------------------------------------------------

    return ""

# 4. Infer community
def resolve_community(
    identifier,
    lab_code,
    laboratories_lookup,
):
    """
    Resolve autonomous community.

    Priority
    --------
    1. laboratories.tsv
    2. Virus name
    """

    lab = laboratories_lookup.get(lab_code, {})

    community = lab.get("autonomous_community_code", "")
    if community:
        return community

    return extract_community(identifier)

# 5. Parse metadata
def parse_metadata(df, registry_dir):

    registry_labs, registry_submitters, lookups = load_registry(registry_dir)

    laboratories_lookup = lookups["laboratories"]
    submitters_lookup = lookups["submitters"]

    identifier_aliases = load_lab_aliases(
        registry_dir / "lab_aliases.tsv"
    )

    df["identifier"] = df["Virus name"].apply(extract_identifier)

    df["lab_code"] = df["identifier"].map(
        lambda x: extract_lab_code(
           x,
            identifier_aliases,
        )
    )

    def get_lab_info(lab_code):
        return laboratories_lookup.get(lab_code, {})

    df["lab_code_normalized"] = df.apply(
        lambda row: (
            get_lab_info(row["lab_code"]).get("lab_code_normalized")
            if row["lab_code"] in laboratories_lookup
            else row["lab_code"]
        ),
        axis=1,
    )

    df["autonomous_community_code"] = df.apply(
        lambda row: resolve_community(
            row["identifier"],
            row["lab_code"],
            laboratories_lookup,
        ),
        axis=1,
    )
    
    df["institution"] = df["lab_code"].map(
        lambda x: get_lab_info(x).get("institution", "")
    )

    df["originating_lab"] = df["lab_code"].map(
        lambda x: get_lab_info(x).get("originating_lab", "")
    )

    df["city"] = df["lab_code"].map(
        lambda x: get_lab_info(x).get("city", "")
    )

    df["submitter_lab_code"] = df["lab_code"].map(
        lambda x: get_lab_info(x).get("submitter_lab_code", "")
    )

    df["laboratory_comments"] = df["lab_code"].map(
        lambda x: get_lab_info(x).get("laboratory_comments", "")
    )

    def get_submitter(code):
        return submitters_lookup.get(code, {})

    df["submitter_lab_name"] = df["submitter_lab_code"].map(
        lambda x: get_submitter(x).get("submitter_lab_name", "")
    )

    df["submitter_name"] = df["submitter_lab_code"].map(
        lambda x: get_submitter(x).get("submitter_name", "")
    )

    df["autonomous_community"] = (
        df["autonomous_community_code"]
        .map(COMMUNITIES)
        .fillna("")
    )

    return df


###############################################################################
# Candidata builders
###############################################################################
# 1. laboratory candidates
def build_laboratory_candidates(df, registry_labs):

    known = set(registry_labs["lab_code"])

    candidate_labs = (
        df.loc[
            (~df["lab_code"].isin(known))
            & (df["lab_code"] != ""),
            [
                "lab_code",
                "lab_code_normalized",
                "autonomous_community_code",
                "autonomous_community",
                "institution",
                "originating_lab",
            ],
        ]
        .drop_duplicates()
        .sort_values("lab_code")
    )

    candidate_labs["submitter_lab_code"] = ""
    candidate_labs["city"] = ""
    candidate_labs["laboratory_comments"] = ""

    return candidate_labs

###############################################################################
# Reporting
###############################################################################

def print_report(input_file, stats, title):

    today = datetime.now().strftime("%Y-%m-%d")

    print("\n" + "=" * 65)
    print(f"GenomeTableTools - {title}")
    print("=" * 65)

    print(f"Date       : {today}")
    print(f"Input file : {Path(input_file).name}")

    print("\nParser summary")
    print("-" * 65)

    print(f"{'Samples                   :':30s} {stats['samples']:>8,}")
    
    if "identifiers" in stats:
        print(f"{'Identifiers               :':30s} {stats['identifiers']:>8}")
    
    if "unique_lab_codes" in stats:
        print(f"{'Unique laboratory codes   :':30s} {stats['unique_lab_codes']:>8}")

    if "unique_submitters" in stats:
        print(f"{'Unique submitters         :':30s} {stats['unique_submitters']:>8}")

    print("\nResolved")
    print("-" * 65)

    if "known_laboratories" in stats:
        print(f"{'Known laboratories        :':30s} {stats['known_laboratories']:>8}")

    if "unknown_identifiers" in stats:
        print(f"{'Unknown identifiers       :':30s} {stats['unknown_identifiers']:>8}")

    print("\nCommunities")
    print("-" * 65)

    if "known_communities" in stats:
        print(f"{'Known communities         :':30s} {stats['known_communities']:>8}")

    if "unknown_communities" in stats:
        print(f"{'Unknown communities       :':30s} {stats['unknown_communities']:>8}")

    print("\nRegistry")
    print("-" * 65)

    if "registry_laboratories" in stats:
        print(f"{'Laboratories in registry  :':30s} {stats['registry_laboratories']:>8}")
    
    if "registry_submitters" in stats:
        print(f"{'Submitters in registry    :':30s} {stats['registry_submitters']:>8}")

    if "registry_aliases" in stats:
        print(f"{'Aliases in registry       :':30s} {stats['registry_aliases']:>8}")

    print("\nQC warnings")
    print("-" * 65)

    warnings = False

    if stats.get("unknown_labs", 0):
        print(f"Unknown laboratories : {stats['unknown_labs']}")
        warnings = True

    if stats.get("unknown_communities", 0):
        print(f"Unknown communities  : {stats['unknown_communities']}")
        warnings = True

    if stats.get("new_laboratories", 0):
        print(f"New laboratories     : {stats['new_laboratories']}")
        warnings = True

    if stats.get("registry_conflicts", 0):
        print(f"Registry conflicts   : {stats['registry_conflicts']}")
        warnings = True

    if not warnings:
        print("None ✓")

    print("\n" + "=" * 65)

    if warnings:
        print("\nSTATUS : REVIEW REQUIRED\n")
    else:
        print("\nSTATUS : PASS ✓\n")

    print("=" * 65)

###############################################################################
# Commands
###############################################################################
# 1. load metadata
def load_metadata(metadata_file):

    return pd.read_csv(
        metadata_file,
        sep="\t",
        keep_default_na=False,
        dtype=str,
    )

# 2. build new candidates
def registry_build(metadata_file, registry_dir):

    # Load registry
    registry_labs, registry_submitters, _ = load_registry(registry_dir)

    # Read metadata
    df = load_metadata(metadata_file)

    # Parse metadata
    df = parse_metadata(df, registry_dir)

    # Build labratory candidates
    candidate_labs = build_laboratory_candidates(
        df,
        registry_labs,
    )

    # Build alias candidates
    new_labs = candidate_labs
    lab_conflicts = pd.DataFrame()
    
    ###############################################################################
    # Stats to print in Report
    ###############################################################################

    unknown_labs = (df["lab_code"] == "").sum()
    unknown_comm = (df["autonomous_community_code"] == "").sum()

    stats = {
        "samples": len(df),
        "identifiers": df["identifier"].nunique(),

        "unique_lab_codes": (
            df["lab_code"].replace("", pd.NA).nunique()
        ),

        "unique_submitters": (
            df["submitter_lab_code"]
                .replace("", pd.NA)
                .nunique()
        ),

        "known_laboratories": (
            df["originating_lab"] != ""
        ).sum(),

        "unknown_identifiers": (
            df["lab_code"] == ""
        ).sum(),

        "known_communities": (
            df["autonomous_community_code"] != ""
        ).sum(),

        "unknown_communities": (
            df["autonomous_community_code"] == ""
        ).sum(),

        "registry_laboratories": len(registry_labs),
        "registry_submitters": len(registry_submitters),
    }
    
    print_report(metadata_file, stats, title="Registry Builder",)

    ###########################################################################
    # Save outputs
    ###########################################################################

    outdir = registry_dir

    outdir.mkdir(exist_ok=True)

    generated = outdir / "generated"
    generated.mkdir(exist_ok=True)

    new_labs.to_csv(
        generated / "laboratories_candidates.tsv",
        sep="\t",
        index=False,
    )

    lab_conflicts.to_csv(
        generated / "laboratories_conflicts.tsv",
        sep="\t",
        index=False,
    )

    validation = (
        df[
            [
                "Virus name",
                "identifier",
                "autonomous_community_code",
                "lab_code",
            ]
        ]
        .drop_duplicates()
    )

    unparsed = validation[
        validation["lab_code"] == ""
    ]

    validation.to_csv(
        registry_dir / "parser_validation.tsv",
        sep="\t",
        index=False,
    )

    summary = (
        df.groupby("lab_code")
        .agg(
            n=("lab_code","size"),
            example=("identifier","first")
        )
        .reset_index()
        .sort_values("n", ascending=False)
    )

    summary.to_csv(
        outdir/"lab_codes_summary.tsv",
        sep="\t",
        index=False
    )

    alias_candidates = (
        df.loc[
            df["lab_code"] == "",
            [
               "Virus name",
               "identifier",
           ]
        ]
        .drop_duplicates()
    )

    alias_candidates["lab_code"] = ""

    alias_candidates = alias_candidates[
        [
            "identifier",
            "lab_code",
            "Virus name",
        ]
    ]

    alias_candidates.to_csv(
        generated / "lab_aliases_candidates.tsv",
        sep="\t",
        index=False,
    )

# 3. build new candidates
def registry_parse(
    metadata_file, 
    registry_dir, 
    output_file=None
):

    if output_file is None:
        output_file = Path(metadata_file).with_suffix(".parsed.tsv")

    # Read metadata
    df = load_metadata(metadata_file)
    
    # Parse metadata
    df = parse_metadata(df, registry_dir)

    registry_labs, registry_submitters, lookups = load_registry(registry_dir)

    identifier_aliases = load_lab_aliases(
        registry_dir / "lab_aliases.tsv"
    )

    stats = {
        "samples": len(df),
        "identifiers": df["identifier"].nunique(),
        "unique_lab_codes": df["lab_code"].nunique(),
        "unknown_labs": (df["lab_code"] == "").sum(),
        "unknown_communities": (
            df["autonomous_community_code"] == ""
        ).sum(),
        "registry_laboratories": len(registry_labs),
        "registry_submitters": len(registry_submitters),
    }

    print_report(
        metadata_file,
        stats,
        title="Registry Parser",
    )

    laboratories_metadata = df[
        [
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
    ]

    # export table
    laboratories_metadata.to_csv(output_file, sep="\t", index=False)
