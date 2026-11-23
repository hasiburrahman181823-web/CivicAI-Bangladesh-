# Evaluation and verification

## Text models

BanglaPSG workbook SHA-256 matches the publisher's download metadata. The release used 6,105 source rows. Train/calibration/test contain 3,662/1,223/1,220 original rows. Groups use exact normalized original text and were separated before building features. Each translation or romanization inherits the source row's split. Unknown incident relationships and near-paraphrases remain threats to validity.

| Held-out source | Category macro F1 | Severity macro F1 | Category ECE before | Category ECE after |
| --- | ---: | ---: | ---: | ---: |
| Natural Bangla | 0.939 | 0.390 | 0.112 | 0.014 |
| Derived English | 0.838 | 0.365 | 0.087 | 0.019 |
| Derived Banglish | 0.931 | 0.388 | 0.112 | 0.013 |

Values are rounded from `backend/ml_training/artifacts/text_metrics.json`. ECE is top-label expected calibration error with 10 equal-width bins. A small ECE measures agreement between probability and observed correctness for that cohort. It does not measure accuracy. Temperature was fit on the separate calibration split. Natural-language confidence is presented for BanglaPSG only. Scores for English and Banglish are not treated as calibrated evidence for naturally written English or Banglish.

Severity performance is weak across all cohorts. The system displays it as a suggestion. Priority combines learned severity and explicit decision rules. We did not train on independent expert priority scores. Use the expert priority template and evaluator to compare the hybrid rule against the rule baseline with held-out expert assessments. Evaluation scripts do not create ground-truth labels.

## Natural English and Banglish

An independent external category check used one public page from [SeeClickFix.com](https://dev.seeclickfix.com/v2/). The 100 New Haven reports yielded 24 unique natural descriptions with a supported source category and at least five words. The city platform service-type tags were mapped to Waste (19), Road (3) and Electricity (2), with no category words inserted into model input. The trained model gave 15/24 correct (62.5%) with macro F1 0.362 over the three observed reference categories. A majority-Waste baseline would score 19/24 (79.2%). This small research-only cohort has no severity labels, no examples of the other three categories and no geographic representation of Bangladesh. Source snapshot hash, class support and metrics are recorded in `natural_english_metrics.json`. Raw descriptions are excluded. SeeClickFix data attribution and terms are in that report.

The BanglaPSG sheet contains zero Latin-only descriptions meeting the 20-Latin-character screen. Banglish corpora found during review do not supply compatible verified complaint categories and incident annotations. Natural Banglish remains unmeasured. Use `evaluate_natural_holdout` and the provided template with independently collected and labeled data; keep all natural evaluation originals and related incidents outside training and calibration.

## MiniLM duplicate benchmark

| Derived source pair | Pairs | F1 at validation-selected threshold 0.05 | ROC AUC | Recall at deployed threshold 0.65 | F1 at deployed threshold 0.65 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Bangla and translated English | 500 | 0.661 | 0.647 | 0.008 | 0.016 |
| Bangla and transliterated Banglish | 500 | 0.665 | 0.607 | 0.024 | 0.046 |

Training-source groups were kept separate. Negatives use different normalized source texts from the same service category; distinct source rows can still describe the same incident. At 0.05 the fraction of reference negatives flagged was 77.6% and 100%, respectively. This threshold is not appropriate for automatic linking. The deployed system retains its conservative starting threshold and sends candidates to an administrator, though the text-only benchmark shows that it misses most positives. Public text analysis does not run a search against the private incident corpus.

BanglaPSG lacks verified incident links, locations and times. These numbers measure derived text matching. Independently verified natural multilingual incident accuracy remains unmeasured. The evaluator accepts adjudicated pairs, checks separation of incident and original IDs across validation and test, and can report context-gated results for pairs with verified dates and areas.

## Media and forecast

| Component | Measured result | Limit |
| --- | --- | --- |
| Vision | 25 genuine labeled RDD2022 images from the checkpoint publisher's held-out split. At score ≥0.30 and IoU ≥0.50, precision was 0.600 and recall 0.375. | Small result with multiple countries and sparse support. Independent Bangladesh evaluation remains open. The model detects four types of road damage. |
| Voice | FLEURS test sample, 16 clips per language. US English WER **13.33%** (48 edits / 360 words). Bangla WER **116.31%** (385 edits / 331 words). | Small non-civic test subset. Insertions can push WER above 100%. Whisper tiny produced poor Bangla transcripts. Banglish speech is unmeasured. |
| Closure forecast | 14,258 training outcomes and 3,719 later cases. Median MAE was 113.91 hours; the category-median baseline was better at 113.14 hours. Empirical 10th–90th interval coverage was 83.0%. | External NYC 311 closure benchmark on observed closed requests. It cannot substantiate a Bangladesh response estimate or a service-level promise. |

See the JSON artifacts for exact values and data boundaries. Raw complaints, images, audio and translated texts are excluded from the release.

## Software checks in the original evaluation release

Frontend production build succeeded. Nine API, security and duplicate-context tests passed. A second local smoke test exercised actual trained classification and confidence, guest submission, private tracking, image inference, Whisper transcription and the NYC benchmark route. The uploaded road photo yielded two detections and the audio produced a nonempty transcript. These smoke tests confirm wiring, while the experiments above describe observed model performance. The current Render deployment serves the text classifier and NYC research benchmark. The media and MiniLM results above describe the full local release.

## Thesis wording

Describe the system as a trained multilingual complaint classification and severity prototype with calibrated BanglaPSG category estimates, hybrid priority decision support, pretrained road-image and speech components, and a separately scoped closure-time benchmark. The main thesis claim about real Bangla–English–Banglish incident matching requires independent cross-language incident annotations, natural test reports, and final held-out results.

The initially blocked Voice and MiniLM tests were rerun inside a Linux network namespace with no route to external services. An OS-level route check failed as intended before the model runs. Both bench runs completed and wrote aggregate output; no text or audio left the environment.
