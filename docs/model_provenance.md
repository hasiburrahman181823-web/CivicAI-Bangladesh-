# Model and data provenance

| Component | Evidence and distribution |
| --- | --- |
| Category and severity | CivicAI TF-IDF and logistic regression fitted on BanglaPSG. [BanglaPSG, Rahman et al.](https://doi.org/10.17632/w6c4zx5t2s.1), CC BY 4.0. The workbook is excluded. English translations and Banglish-style romanizations inherit their source row's labels and split. |
| English augmentation | [Helsinki-NLP OPUS-MT bn-en](https://huggingface.co/Helsinki-NLP/opus-mt-bn-en/tree/098d427088fba65d683639e91742c783cc7c1434), Apache-2.0, converted to CTranslate2 INT8 for training preprocessing. Translation outputs and weights used only for augmenting training are excluded. |
| Embeddings | [Sentence Transformers multilingual MiniLM](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2/tree/e8f8c211226b894fcb81acc59f3b34ba3efd5f42), Apache-2.0. Packaged publisher ONNX INT8 AVX2 export and tokenizer. |
| Voice | [Systran faster-whisper-tiny](https://huggingface.co/Systran/faster-whisper-tiny/tree/d90ca5fe260221311c53c58e660288d3deb8d356), MIT, a conversion of OpenAI Whisper tiny. Evaluation used an early archive sample of the [FLEURS](https://huggingface.co/datasets/google/fleurs) Bengali and US English test sets. Samples and transcripts excluded. |
| Image | [dronefreak YOLOv8n RDD2022](https://huggingface.co/dronefreak/rdd2022-yolov8n/tree/8f55222cb7a3e4a9945f6f7543d0583032c60a43), AGPL-3.0. The bundled observer model is an ONNX conversion of the publisher's safetensors checkpoint. Vision weights in artifacts/road are covered by the upstream license. Source weights, matching export script and upstream provenance are included. Test images from the [publisher's RDD2022 split](https://huggingface.co/datasets/dronefreak/RDD2022) are excluded. |
| Closure time | CivicAI gradient-boosted quantile regressors trained on [NYC 311 Open Data](https://data.cityofnewyork.us/d/erm2-nwe9). Samples are from the 5th and 6th days of each month in 2025, restricted to selected complaint types. Close times observed before model training cutoff were used in training. External benchmark only. |

Project source license covers project-authored code. Upstream weights retain their own licenses. Treat the project-authored joblib model artifacts as trusted files from this release; do not substitute unsigned or untrusted pickle-based files.
