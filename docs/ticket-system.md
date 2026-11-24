# CivicAI Bangladesh ticket system

## Architecture

The same-origin React portal serves a bilingual public intake and tracking page, a private citizen dashboard, and an administrator workspace. FastAPI validates requests and checks roles and ticket ownership. PostgreSQL stores complaints and ticket activity. Redis shares request limits between instances. Uvicorn leaves proxy headers unprocessed so the application can enforce explicit trusted-proxy boundaries.

Guests enter a Bangladesh mobile number and receive a UUID and a separate high-entropy secret. Private tracking requires both values. Citizen sign-in links new complaints to the account. The dashboard refreshes ticket details every 12 seconds and recent activity every 20 seconds while visible. Staff can update status, reply to registered owners, review triage signals, download evidence, and export filtered report metadata.

## Database schema

| Table | Purpose and relationships |
|---|---|
| `users`, `login_sessions` | Citizen and administrator roles with expiring, revocable login sessions |
| `complaints` | UUID, optional owner, tracking secret digest, incident and filing times, area, complaint text, triage data, review state, and duplicate linkage |
| `complaint_intake` | One row per new complaint with encrypted mobile, source address and reported device class. Contains masked mobile suffix and a nullable mobile verification timestamp |
| `ticket_events` | Complaint foreign key, status, timestamp and order |
| `ticket_messages` | Complaint and author foreign keys, author role, redacted message and timestamp |
| `ticket_evidence` | Complaint foreign key, sanitized image bytes and timestamp |
| `audits`, `admin_export_audits` | Staff identity and timestamp associated with review, reply, contact access, evidence access, or export |

Startup adds the new tables and the owner timeline index. It keeps existing records readable, including reports filed before the contact fields existed. PostgreSQL serializes schema initialization with a transaction lock. Snapshot the database before rolling out the schema on a production service.

## Model training and inference

1. The existing [category and severity trainer](../backend/ml_training/scripts/train_text.py) fits character n-gram text classifiers using a complaint corpus. The verified release artifact is included in the Docker build. Known hazards can raise the workflow priority for human review.
2. [Train the intake classifier](../backend/ml_training/scripts/train_intake.py) from the [synthetic starter CSV](../backend/ml_training/data/intake_examples.csv). The two TF-IDF/logistic regression heads predict language sentiment and review-worthy promotion or abuse. Exported JSON carries coefficients, vocabulary, and cross-validation metrics. [Runtime inference](../backend/app/ml/intake.py) loads the JSON and abstains when lexical support or class confidence is low.
3. Intake adds an extractive summary, a bilingual service-team suggestion, a suggested action, and transparent patterns such as repeated words and links. Flags prompt case-by-case review and have no effect on submission acceptance or account access. Staff should verify complaints independently.
4. The citizen ETA uses the last year of completed local reports of the same category. It uses up to 200 closure records, requires 20 usable records, and displays the median and the 20th–80th percentile range. The clock starts at submission. The separate public research benchmark has its own source and scope.

Run from the repository root.

```sh
python -m pip install -r backend/requirements.txt
python backend/ml_training/scripts/train_intake.py
npm ci
npm run build
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Starter cross-validation reflects 47 synthetic examples. Validate both heads on independently reviewed Bangla, English, and Banglish complaints before relying on their signal quality. Use authorized, de-identified examples for retraining. Keep private datasets outside version control.

## Production configuration

- Configure PostgreSQL, shared Redis, TLS, the allowed host, and a strong JWT secret. Use a dedicated persistent `INTAKE_ENCRYPTION_KEY` produced with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. Store the key in the deployment secret manager and back it up separately from the database. Preserve it across restarts and backups. Re-encrypt existing intake rows during a planned rotation.
- `CONTACT_REVIEWER_EMAILS` lists the existing admin accounts permitted to reveal encrypted intake data. Every successful reveal requires a reason and records an audit entry. The ordinary admin view and CSV export show only a masked mobile. Keep this setting empty until the organization names authorized reviewers.
- Enter only verified reverse-proxy addresses or CIDRs in `TRUSTED_PROXY_NETWORKS`. With no trusted proxy configured, the address is the direct network peer. Test the actual proxy chain and sharing of IP-based limits in staging.
- Intake performs number format validation, and the schema can record a later ownership check. SMS sending and OTP verification require an SMS provider and are currently inactive. A submitted phone number and IP address are limited indicators and require independent verification.
- Evidence accepts up to five JPEG, PNG or WebP images per account-linked ticket. The API decodes and re-encodes each photo, limits dimensions and bytes, strips metadata, and requires an authorized download. Set a data retention period for contact records, complaint evidence, and backups before collecting public data.
- Set `CIVICAI_ARTIFACTS` to an empty temporary directory for deterministic rule-mode API tests. Run `python -m pytest -q backend/tests`, `npm run build`, then validate PostgreSQL locking, Redis, model startup, account recovery and the contact access permissions against a staging service.
