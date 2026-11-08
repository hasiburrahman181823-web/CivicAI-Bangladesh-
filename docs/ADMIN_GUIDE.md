# CivicAI Bangladesh - Municipal Administrator Operational Manual

## 1. Access & Role Management

Authorized officials log in through the **Sign In** modal using department credentials or demo credentials:
- **Central Administrator:** `admin@civicai.gov.bd` (Password: `Admin@CivicAI2026!`)
- **Department Officers:**
  - `officer.rhd@civicai.gov.bd` (Roads & Highways Department)
  - `officer.wasa@civicai.gov.bd` (WASA Water & Drainage)
  - `officer.power@civicai.gov.bd` (Electricity & Power)

---

## 2. Complaint Processing Lifecycle

```
[Submitted] 
    │
    ▼ (Automated NLP Processing)
[AI_Analyzed] 
    │
    ▼ (Officer Verification: Accept or Override with Justification)
[Verified] 
    │
    ▼ (Departmental Assignment & SLA Deadline Setting)
[Assigned] 
    │
    ▼ (Field Team Dispatched)
[In_Progress] 
    │
    ▼ (Upload Resolution Notes & After-Work Photos)
[Resolved] ──► [Citizen Verification & Satisfaction Feedback]
```

---

## 3. Key Administrative Procedures

### A. Verifying AI Predictions & Overriding
1. Click **Admin Panel** in the top navigation bar.
2. In the **AI-Prioritized Complaint Queue**, click **Verify / Override** on any pending issue.
3. Review the AI-predicted category and severity.
4. If correct, click **Confirm Verification**.
5. If an override is required (e.g. citizen underreported severity), select the new category or severity, document the mandatory **Officer Override Reason**, and confirm. The system will automatically recalculate the priority score and log the action to the immutable audit trail.

### B. Updating Status & Uploading Resolution Evidence
1. Once field repair work commences, update status to **In Progress**.
2. Upon completion, select **Resolved**, input detailed **Resolution Notes**, and attach photographic proof. This publishes the after-resolution evidence on the citizen's public tracking page.

### C. Merging Duplicate Complaints
1. When multiple citizens report the same sinkhole or transformer blowout, locate the primary complaint in the queue.
2. Click the **Merge (GitMerge)** icon.
3. Input the Complaint ID of the secondary report and click **Execute Merge**.
4. Citizen upvotes will be transferred to the primary complaint, boosting its priority score, and the duplicate will be linked and set to `Duplicate_Merged`.
