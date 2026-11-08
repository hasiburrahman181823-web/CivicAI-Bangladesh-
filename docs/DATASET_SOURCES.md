# CivicAI Bangladesh - Dataset Provenance & Attribution

## 1. Dataset Overview

- **Dataset Identifier:** `CivicAI-Bangladesh-Multilingual-Corpus-v1.0`
- **Total Records:** 2,100 samples
- **Splits:** 70% Training (1,470 samples), 15% Validation (315 samples), 15% Test (315 samples)
- **Target Domains:** 10 Civic Sectors
- **Target Severity Tiers:** Critical, High, Medium, Low
- **Language Distributions:**
  - English (EN): 748 samples (35.6%)
  - Bangla (বাংলা): 695 samples (33.1%)
  - Banglish (Phonetic Roman Bangla): 657 samples (31.3%)

---

## 2. BanglaPSG Corpus Alignment

The dataset adheres to the schema and taxonomy of the **BanglaPSG** (Bangla Public & Social Governance) benchmark:
1. Grounded in actual administrative divisions of Bangladesh (Dhaka, Chattogram, Rajshahi, Khulna, Barishal, Sylhet, Rangpur, Mymensingh).
2. Uses standard civic domain categories recognized by Bangladesh City Corporations, Municipalities, and Directorate Authorities (RHD, WASA, BPDB/DPDC/DESCO, DoE, DGHS, Police, BRTA, ACC).
3. Captures authentic colloquial expressions and syntax variations across Bengali dialects and phonetic English transcriptions.

---

## 3. Data Integrity & Ethical Compliance

- **No Scraping of Private Identifiable Information (PII):** All geographic names reflect public wards, avenues, and landmarks.
- **Attribution & Licensing:** CC BY-SA 4.0 Open Access for academic and public service governance.
- **Data Leakage Prevention:** The train, validation, and test splits were partitioned using deterministic pseudo-random seeds ($S=42$) prior to feature extraction to guarantee zero cross-contamination.
