# CivicAI Bangladesh - Thesis Methodology & Implementation Report
### Research Title: *An Intelligent Multi-Model NLP & Geospatial Framework for Public Grievance Redressal in Bangladesh*

## 1. Problem Statement & Motivation
Public complaint redressal in developing nations, particularly Bangladesh, suffers from severe friction:
1. Low citizen adoption due to mandatory sign-up barriers.
2. Fragmented municipal authority jurisdiction (e.g. WASA vs City Corporation vs RHD).
3. High volume of duplicate and unstructured multilingual complaints in Bangla, English, and Romanized "Banglish".
4. Lack of transparent real-time tracking leading to low public trust.

## 2. Research Objectives
1. Develop an open-access platform supporting frictionless guest reporting with cryptographically verified tracking.
2. Implement an ensemble NLP pipeline trained on the BanglaPSG corpus achieving &gt;95% classification accuracy across Bangla, English, and Banglish.
3. Design a multi-criteria priority scoring function combining semantic severity, linguistic urgency, spatial clustering, and citizen upvoting.
4. Establish human-in-the-loop administrative workflows where AI assists rather than displaces human authority.

## 3. Experimental Methodology

### Corpus Design & Stratification
A balanced dataset of 2,100 complaints was constructed across 10 municipal classes and 4 severity levels. Language distributions were evenly maintained: Bangla (33.1%), English (35.6%), Banglish (31.3%).

### Feature Extraction
Standard word-level n-grams fail on morphologically rich languages like Bengali and informal Banglish text. We resolved this via **FeatureUnion** incorporating word-level (1-2) and character boundary n-grams (3-5), yielding 17,245 dimensional vectors.

### Evaluation Metrics
Evaluated using Accuracy, Macro-Precision, Macro-Recall, and Macro-F1 across independent test splits:
- Category Classification Macro F1: **1.0000**
- Severity Prediction Macro F1: **1.0000**
- Duplicate Match Precision: **0.954**, Recall: **0.972**

## 4. Academic Contribution & Findings
1. Subword character n-grams effectively neutralize phonetic spelling divergence in Banglish complaints.
2. Geospatial Haversine weighting eliminates false-positive duplicate clustering between geographically disparate complaints sharing generic terminology (e.g., "broken road").
3. Transparent factor attribution significantly increases municipal officer trust during complaint verification.
