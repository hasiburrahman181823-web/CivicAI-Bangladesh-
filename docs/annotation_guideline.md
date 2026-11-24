# Incident annotation

An incident is a specific problem affecting a particular service asset or bounded area during a coherent time interval. Same category is not sufficient. Nearby reports can refer to separate assets. A resolved issue followed by a new occurrence can be a separate incident.

Two independent annotators should label same-incident, different-incident or insufficient-evidence. Record rationale, temporal context, location precision and adjudication. Do not force uncertain pairs into a binary label. Public maps must not expose personal home coordinates or reporter identities.

Preserve original_id for every translated/transliterated version, label its source_type derived, and retain natural for naturally authored records. Split connected original/incident groups before feature fitting, augmentation, threshold tuning or calibration. Use separate grouped validation and test sets. Establish incident timing and location through evidence, never inferred synthetic coordinates labeled as real.

## Independent evaluation checklist

Each evaluator records one anonymous original ID per source text, a verified incident ID, a language, and an evidence reference. Human adjudication determines same, different, or insufficient evidence. Use the provided CSV header and keep the evidence reference out of public releases if it can identify a reporter. Leave distance and incident time missing when they cannot be verified. Collect difficult negatives such as nearby work on different assets, and different occurrences on the same asset. Get model thresholds from the validation split. Hold out natural Banglish and English separately from derived translations.

For native Banglish evaluation, collect independently written Banglish civic reports from consenting reporters, preserve the original wording, and have reviewers confirm language, category and severity. The natural-holdout evaluator accepts aggregate research labels from this frozen test set. Its template is `backend/ml_training/data/natural_complaints_template.csv`. Do not use translations or generated examples in this cohort. Cross-language incident pairs need independent reports plus corroboration by the same public asset, event timeline or an authority's reference. A matching topic or shared landmark alone is insufficient. Store item provenance and contact details separately with restricted access.
