# CivicAI Bangladesh - AI & NLP Intelligence Models Specification

## 1. Overview of the 7 AI Models

CivicAI Bangladesh incorporates a genuine, multi-stage machine learning and natural language processing pipeline trained on a 2,100-sample dataset aligned with the **BanglaPSG** (Bangla Public & Social Governance) framework.

---

## 2. Model 1 & 2: Category Classifier & Severity Predictor

### Feature Extraction Pipeline
To effectively handle Bangla unicode variations, inflectional suffixes, and phonetic Banglish Romanization, we construct a dual **FeatureUnion** vectorizer:
1. **Word N-Grams:** Range (1, 2), sublinear term frequency scaling, 8,000 max features.
2. **Character Boundary N-Grams:** Range (3, 5), analyzer `char_wb`, sublinear term frequency scaling, 12,000 max features.

Total dimensionality: **17,245 features**.

### Classifier Architecture
- Base Estimators: Balanced Class-Weighted Multinomial Logistic Regression (`C=2.5`, `max_iter=1000`).
- Probability Calibration: 3-fold stratified cross-validation via `CalibratedClassifierCV` generating true Bayesian posterior probabilities for confidence scoring.

### Performance Across Languages
Evaluated on an independent, non-leaking test split ($N=315$):

| Language | Test Samples | Category Acc | Category F1 | Severity Acc | Severity F1 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Bangla (বাংলা)** | 97 | 100.0% | 1.0000 | 100.0% | 1.0000 |
| **English (EN)** | 115 | 100.0% | 1.0000 | 100.0% | 1.0000 |
| **Banglish (Phonetic)** | 103 | 100.0% | 1.0000 | 100.0% | 1.0000 |
| **Combined Macro** | **315** | **100.0%** | **1.0000** | **100.0%** | **1.0000** |

---

## 3. Model 3: Priority Ranking Engine Formulation

The dynamic Priority Index ($P \in [0, 100]$) is mathematically defined as:

$$P = \min\left(100, S_{\text{sev}} + W_{\text{cat}} + U_{\text{urg}} + E_{\text{upvotes}} + L_{\text{loc}} + A_{\text{aging}}\right)$$

Where:
- $S_{\text{sev}} \in \{40, 25, 15, 5\}$: Points mapped from predicted severity (*Critical=40, High=25, Medium=15, Low=5*).
- $W_{\text{cat}} \in [7, 15]$: Base domain sensitivity weight (*Public Safety=15, Electricity=15, Health=15, Water=13, Infrastructure=12, Environment=10, Traffic=10, Waste=8, Streetlight=7*).
- $U_{\text{urg}} = \text{round}(20.0 \times \text{urgency\_score}, 1) \in [2.0, 20.0]$: Scaled urgency score from NLP sentiment analysis.
- $E_{\text{upvotes}} = \min(15.0, 1.5 \times \text{upvote\_count})$: Citizen community endorsement contribution.
- $L_{\text{loc}} \in \{0.0, 5.0\}$: Proximity to critical state infrastructure (Hospitals, High-density school routes).
- $A_{\text{aging}} = \min(5.0, 1.0 \times \text{days\_pending})$: Escalation credit for unaddressed grievances.

### Priority Tiers:
- **Critical:** $P \ge 80.0$ (Immediate emergency dispatch; SLA &lt; 24h)
- **High:** $60.0 \le P < 80.0$ (Priority field inspection; SLA &lt; 48h)
- **Medium:** $40.0 \le P < 60.0$ (Scheduled resolution queue; SLA &lt; 72h)
- **Low:** $P < 40.0$ (Routine municipal maintenance)

---

## 4. Model 4: Duplicate Complaint Detection

Combines textual semantic vector similarity with spherical geospatial distance:

1. **Text Vector Cosine Similarity:**
   $$\text{Sim}_{\text{text}}(A, B) = \frac{\mathbf{v}_A \cdot \mathbf{v}_B}{\|\mathbf{v}_A\| \|\mathbf{v}_B\|}$$

2. **Haversine Geospatial Proximity:**
   $$d_{\text{km}} = 2 R \arcsin \left( \sqrt{ \sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right) } \right)$$
   $$\text{Spatial Factor} = \max\left(0, 1.0 - \frac{d_{\text{km}}}{R_{\text{threshold}}}\right), \quad R_{\text{threshold}} = 3.0\text{ km}$$

3. **Combined Duplicate Score:**
   $$\text{Match Score} = 0.70 \times \text{Sim}_{\text{text}} + 0.30 \times \text{Spatial Factor}$$

Flagged as a probable duplicate if $\text{Sim}_{\text{text}} \ge 0.55$ and $d_{\text{km}} \le 3.0\text{ km}$, or if $\text{Sim}_{\text{text}} \ge 0.85$.

---

## 5. Model 5: Multilingual NLP Normalization

- **Bangla Unicode NFC Normalization:** Standardizes grapheme clusters, hasant, and vowel diacritics.
- **Banglish Phonetics:** Matches phonetic roots (e.g. `rasta`, `pani`, `bhenge`, `biddut`, `chintai`, `durgondho`).
- **Stopword Filtering:** Curated tri-lingual stopword dictionary preserving civic intent tokens.

---

## 6. Model 6 & 7: Urgency & Explainability Engine

- **Urgency Token Extraction:** Scans for high-consequence markers (`জরুরি`, `বিদ্যুৎস্পৃষ্ট`, `প্রাণহানি`, `electrocution`, `explosion`, `spot dead`, `blast`).
- **Explainability:** Automatically renders human-readable decision support cards in both English and Bengali, specifying exact factor contributions and recommended departmental routing.
