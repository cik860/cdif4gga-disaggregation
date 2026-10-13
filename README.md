# CDIF-for-GGA: disaggregation vocabulary and 9a mapping

Supplementary materials for *Mapping expert proposed GGA water indicators to the Cross Domain Interoperability Framework: metadata fit and disaggregation vocabulary design* (Fakhruddin & Choi).

## Contents
- `vocab/gga-disaggregation.ttl` — candidate SKOS vocabulary: 19 concept schemes, 83 concepts (dimensions as Concept Schemes, values as coded concepts), derived from the free-text disaggregation column of the expert group indicator compilation (8 Sep 2025; UNFCCC technical report) and dual-reviewed (KOS specialist + climate domain expert). Base URI `https://w3id.org/cdif4gga/disagg/` is a placeholder pending w3id registration.
- `vocab/concepts.csv` — human-readable concept listing with review status and notes.
- `mapping/9a_CDIF_mapping_v1.0.xlsx` — 110 field-mappings of the ten expert-proposed water (9a) indicators into CDIF v1.1 locations, with per-row rule or adjudication rationale.
- `mapping/crosswalk.csv` — one row per assignment (indicator, source field/value, CDIF profile/version, judgment, basis). `property_path` is reserved for the structured release described in the paper, Section 3.3.
- `candidates/` — extraction output (95 recurring candidates with provenance) and the completed domain-validity review (33 accepted, 2 excluded).
- `scripts/skos_candidate_extraction.py` — the extraction pipeline (rule-based tokenization, curated synonym normalization, two-pass assignment).

## Status
Candidate input to the metadata and methodology work mandated to the UNFCCC Subsidiary Bodies (Belém–Addis Vision). Not an authoritative vocabulary: authority rests with the UNFCCC process.

## Reproducibility
Rule application and extraction were executed programmatically with AI assistance (Claude, Anthropic); rule design, adjudication and accept/reject decisions were made by the authors.

## License
Vocabulary and data: CC0 1.0 Universal. Scripts: MIT.
