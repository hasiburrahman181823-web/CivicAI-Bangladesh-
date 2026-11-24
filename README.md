# CivicAI Bangladesh · Hardened Model Edition

CivicAI is a citizen complaint decision-support prototype. It accepts Bangla, English and Banglish text, suggests a category and severity, and explains how severity and policy cues contribute to suggested priority. Reviewers confirm all priority and duplicate decisions.

## Project layout

```text
bd-complaint-ai/
  backend/app/           FastAPI, login, tracking, model inference and admin review
  backend/ml_training/   Training scripts, evaluation scripts and release model artifacts
  backend/tests/         API and incident filtering tests
  frontend/src/          React application
  dist/                  Ready-to-serve compiled frontend
  docs/                  Provenance, evaluation and labeling guidance
  scripts/               Local launcher and evaluation helpers
  Dockerfile
  docker-compose.yml
```

## Run on Windows

Install Python 3.11 and Node.js 22, then open PowerShell in the extracted `bd-complaint-ai` folder. Rebuild the frontend so the running site uses the latest source. The full project ZIP includes the trained and pretrained weights.

```powershell
npm.cmd ci
npm.cmd run build
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt -r backend/requirements-ml.txt
.\.venv\Scripts\python.exe scripts/run_local.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) and use the complaint form on the home page. The **বাংলা / EN** switch changes the public interface. Expand the media option to test an audio file or road photo. Save the complaint ID and private key from the receipt to track progress. To create an administrator, run this in another terminal in the same folder.

```powershell
.\.venv\Scripts\python.exe -m backend.scripts.create_admin
```

Sign in as an administrator to open the live review queue. The **বাংলা / EN** switch also appears in the administrator workspace and keeps the current page and filters when changing language. There is no default administrator password. The research page has an NYC closure-time benchmark form.

## Run on Linux or macOS

```bash
npm ci
npm run build
python3.11 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt -r backend/requirements-ml.txt
.venv/bin/python scripts/run_local.py
```

The bundled MiniLM ONNX export targets x86 CPUs with AVX2. The embedding module can alternatively use the original Sentence Transformers checkpoint through `EMBEDDING_MODEL_PATH`. The release was verified on CPU with Python 3.12. Python 3.11 is the Docker and CI target.

## Rebuild and test

```bash
npm ci
npm run build
python -m pytest backend/tests -q
```

Use `python -m scripts.verify_models --image road.jpg --audio voice.wav` with your own appropriately labeled test media to verify local inference across the HTTP routes.

## Thesis reproduction

Read [model provenance](docs/model_provenance.md) and [evaluation](docs/model_evaluation.md). The published workbook is not bundled. Retain exact datasets and the operating environment if reproducing results. For BanglaPSG, begin with the published workbook and retain the SHA-256 recorded in the report. To reproduce the English view, download the pinned Helsinki model in the provenance document, install the training requirements and a PyTorch CPU build, and convert it locally.

```bash
ct2-transformers-converter --model ./opus-bn-en --output_dir ./opus-ct2 --quantization int8 --copy_files source.spm target.spm vocab.json tokenizer_config.json
python -m backend.ml_training.scripts.translate_banglapsg --model ./opus-ct2 --workbook ./BanglaPSG-Grievance-Dataset.xlsx --output ./english-derived.csv
python -m backend.ml_training.scripts.train_text --workbook ./BanglaPSG-Grievance-Dataset.xlsx --english ./english-derived.csv --output ./backend/ml_training/artifacts
python -m backend.ml_training.scripts.evaluate_duplicates --workbook ./BanglaPSG-Grievance-Dataset.xlsx --english ./english-derived.csv --model ./backend/ml_training/artifacts/minilm --output ./backend/ml_training/artifacts/duplicate_proxy_metrics.json
```

For verified duplicate incidents, fill `backend/ml_training/data/reviewed_pairs_template.csv` according to the [annotation guide](docs/annotation_guideline.md). Keep all originals and reports related to any one incident in the same split. Use `--pairs ./reviewed_pairs.csv` instead of `--workbook` and `--english` in the evaluator. Mixed-language original reports require genuine independent annotations.

## Production setup

Use an HTTPS reverse proxy with the same site origin for the frontend and API. The provided Compose configuration binds CivicAI to localhost and runs Redis on its private container network. The production app requires a trusted host, shared throttling, and the release model manifest digest. See [security setup and dataset handling](docs/security.md) for secrets, admin enrollment, backups and upgrades.

The [Render deployment](https://civicai-bangladesh-live-tivv.onrender.com/) uses the verified text and research models in `backend/civicai-models.tar.gz`. This package contains the CivicAI category and severity classifiers based on [BanglaPSG by Rahman et al., CC BY 4.0](https://doi.org/10.17632/w6c4zx5t2s.1) and the closure-time benchmark based on [NYC 311 Open Data](https://data.cityofnewyork.us/d/erm2-nwe9). Media models and multilingual embeddings are optional in the full local release. The deployed duplicate review compares text overlap, incident times and locations.

The citizen dashboard at `/#dashboard` links to public submissions, private tracking, personal reports and research materials. Its statistics show portal-wide counts and display category totals once a category has at least five complaints. Signed-in citizens can view their own submissions. Administrators sign in at `/#admin` with their email and password to review complaints, check duplicate candidates and view the audit log. Citizen login cookies expire after 60 minutes, and administrator sessions expire after 15 minutes. The administrator dashboard filters the latest 500 loaded complaints by area and incident dates in Bangladesh time. The map displays incidents with optional coordinates and uses a Natural Earth boundary.

### Account recovery and administrator setup

Citizens can generate one single-use recovery code from their profile after confirming their current password. The **Forgot password?** page accepts that code. Resetting the password revokes all previous sessions and recovery grants for that account.

For optional email recovery, configure a verified Resend sender, a sending-only `RESEND_API_KEY`, and `RECOVERY_FROM_EMAIL` on Render. Keep email click tracking off for password reset links. CivicAI uses the Render service's HTTPS URL by default. Set `RECOVERY_ORIGIN` when using a separate HTTPS public origin. If email delivery is not configured, the recovery page offers saved codes.

The first administrator can activate the configured `CIVICAI_ADMIN_EMAIL` at `/#admin-setup` using the short-lived `CIVICAI_ADMIN_SETUP_CODE` held in the Render service's private environment. Set its absolute UTC deadline via `CIVICAI_ADMIN_SETUP_EXPIRES`. The operator sets a unique password of at least 15 characters. The page disables first-time enrollment once an administrator exists. The local `backend.scripts.create_admin` command remains available to authorized operators.

Model output supports review. It does not represent an official or emergency service decision.
