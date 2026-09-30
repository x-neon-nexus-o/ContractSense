# LexIntel AI 🇮🇳

> **India-Specific AI Contract Intelligence Platform**

LexIntel AI is an AI-assisted contract analysis platform designed for Indian **startups, freelancers, MSMEs, and individuals**. It analyzes uploaded **NDA, Employment, and Vendor Agreements**, classifies clauses, identifies potential contractual and compliance risks, checks selected Indian legal provisions using a rule engine, and uses Retrieval-Augmented Generation (RAG) to provide contract-grounded explanations, AI chat, and negotiation suggestions.

> **Important:** LexIntel AI is a decision-support and educational system, not a substitute for a qualified lawyer or formal legal advice. Its legal checks are limited to the laws and provisions explicitly implemented in the project.

---

## 1. Project Overview

### Problem

Many Indian startups, freelancers, and small businesses sign contracts without fully understanding complex clauses involving payment, liability, termination, confidentiality, intellectual property, data protection, dispute resolution, and other obligations.

Most existing contract-analysis products are designed primarily around foreign legal frameworks and are not specifically optimized for Indian users and selected Indian statutory requirements.

### Proposed Solution

LexIntel AI combines:

- **NLP and LegalBERT** for clause classification
- **Rule-based legal reasoning** for selected Indian legal provisions
- **Risk scoring** for clause-level and contract-level assessment
- **OCR** for scanned contracts
- **Embeddings + ChromaDB** for semantic retrieval
- **RAG + LangChain** for contract-grounded question answering
- **Gemini/Groq/Ollama-compatible LLM layer** for explanations and generation
- **SHAP** for ML explainability
- **FastAPI** for backend services
- **Flutter** for the mobile client
- **MongoDB** for application data
- **Render or another suitable cloud platform** for backend deployment

---

# 2. Core Differentiator

LexIntel AI is not intended to be just an LLM wrapper.

The system follows a hybrid architecture:

```text
                Uploaded Contract
                       │
                       ▼
              PDF/DOCX/OCR Processing
                       │
                       ▼
                Clause Segmentation
                       │
                       ▼
              Fine-tuned LegalBERT
                       │
                       ▼
               Clause Classification
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
       Risk Prediction      Legal Rule Engine
             │                   │
             └─────────┬─────────┘
                       ▼
                Risk Assessment
                       │
                       ▼
              Embeddings / ChromaDB
                       │
                       ▼
                  RAG Retrieval
                       │
                       ▼
                Gemini / Groq / LLM
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
     AI Chat       Explanation    Suggestions
                       │
                       ▼
                  PDF Report
```

### Main research/technical contribution

The project combines:

> **Fine-tuned legal NLP + India-specific rule-based analysis + semantic retrieval + RAG + Generative AI**

rather than depending on a single general-purpose LLM.

---

# 3. Project Objectives

### PRO1 — Clause Classification

Develop a **LegalBERT-based NLP model** capable of classifying clauses in:

- NDA
- Employment Agreements
- Vendor Agreements

Possible categories include:

- Payment
- Liability
- Termination
- Confidentiality
- Intellectual Property
- Data Protection
- Dispute Resolution
- Governing Law
- Non-Compete / Restrictive Covenants
- Indemnification
- Warranty
- Other

### PRO2 — Indian Legal Compliance

Develop an **India-specific rule engine** that performs selected compliance/risk checks based on implemented provisions of:

- Indian Contract Act, 1872
- MSMED Act, 2006
- Digital Personal Data Protection Act, 2023
- Arbitration and Conciliation Act, 1996
- Applicable Stamp Duty provisions

The system should clearly distinguish:

- deterministic rule results
- model predictions
- LLM-generated explanations

### PRO3 — Contract-Grounded Generative AI

Implement:

- embeddings
- ChromaDB
- LangChain
- RAG
- Gemini/Groq/Ollama-compatible LLM layer

to provide:

- contract-aware AI chat
- clause explanations
- summaries
- contextual answers
- negotiation/rewrite suggestions

---

# 4. Project Scope

## In Scope

### Contract Types

Initial release:

1. NDA
2. Employment Agreement
3. Vendor Agreement

### Input Formats

- PDF
- DOCX
- scanned PDF
- image-based documents where supported

### Main Functions

- User authentication
- Contract upload
- Text extraction
- OCR
- Clause segmentation
- Clause classification
- Risk detection
- Legal rule checks
- Overall risk score
- Clause-level risk score
- Explainability
- Semantic retrieval
- RAG-based AI chat
- Negotiation suggestions
- Contract summary
- PDF report generation
- Analysis history

## Out of Scope

The initial version will not:

- provide formal legal advice
- replace a lawyer
- guarantee that a contract is legally valid/invalid
- cover every Indian statute
- cover every possible contract type
- automatically file legal cases
- represent a user in court
- guarantee enforceability
- independently determine the final legal interpretation of a disputed provision

---

# 5. Target Users

### Primary Users

- Indian freelancers
- Startups
- MSMEs
- Small businesses
- Independent professionals
- Students/researchers studying LegalTech

### Potential Secondary Users

- Legal teams
- HR teams
- Procurement teams
- Consultants
- Contract managers

---

# 6. Technology Stack

| Layer | Technology |
|---|---|
| Mobile UI | Flutter |
| State Management | Riverpod |
| HTTP Client | Dio |
| Local Storage | Hive/secure local storage as required |
| Backend | Python + FastAPI |
| ML | PyTorch + Hugging Face Transformers |
| NLP Model | LegalBERT |
| OCR | Tesseract OCR |
| PDF Extraction | PyMuPDF |
| DOCX Extraction | python-docx |
| RAG Framework | LangChain |
| Vector DB | ChromaDB |
| Application DB | MongoDB |
| LLM | Gemini / Groq / Ollama-compatible provider |
| Explainability | SHAP |
| Dataset | CUAD + curated Indian contract dataset |
| Development | VS Code / PyCharm / Jupyter / Google Colab |
| Version Control | Git + GitHub |
| Backend Deployment | Render or another suitable cloud platform |
| API Documentation | FastAPI / OpenAPI |

---

# 7. High-Level System Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER                     │
│                                                             │
│                     Flutter Mobile App                      │
│   Login • Upload • Dashboard • Clause View • AI Chat       │
│                       PDF Report                            │
└─────────────────────────────┬───────────────────────────────┘
                              │ HTTPS
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       API / BACKEND                         │
│                         FastAPI                             │
│                                                             │
│ Authentication • Upload Management • Analysis APIs         │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    DOCUMENT PROCESSING                       │
│                                                             │
│ PDF Parser • DOCX Parser • Tesseract OCR • Preprocessing   │
│                      Clause Segmentation                    │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     AI / NLP LAYER                          │
│                                                             │
│ LegalBERT → Clause Classification → Risk Prediction        │
│                    ↓                                        │
│             Indian Legal Rule Engine                        │
│                    ↓                                        │
│             Explainability / SHAP                           │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       RAG LAYER                             │
│                                                             │
│ Embeddings → ChromaDB → Semantic Retrieval → LangChain     │
│                              ↓                              │
│                     Gemini / Groq / LLM                     │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         DATA LAYER                          │
│                                                             │
│ MongoDB: users • contracts • analyses • reports • history  │
│ ChromaDB: embeddings • chunks • metadata                    │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         OUTPUT                              │
│                                                             │
│ Risk Dashboard • AI Chat • Explanations • Suggestions      │
│                    Downloadable PDF Report                   │
└─────────────────────────────────────────────────────────────┘
```

---

# 8. Data Flow

```text
INPUT
  │
  ├── Contract PDF/DOCX/Scanned PDF
  ├── User Profile
  └── User Questions
  │
  ▼
DOCUMENT INGESTION
  │
  ├── PDF/DOCX parser
  └── Tesseract OCR
  │
  ▼
TEXT PROCESSING
  │
  └── Clause segmentation
  │
  ▼
AI ANALYSIS
  │
  ├── LegalBERT classification
  ├── Risk prediction
  └── Indian legal rule checks
  │
  ▼
RAG STORAGE
  │
  ├── Generate embeddings
  └── Store/search in ChromaDB
  │
  ▼
GENERATION
  │
  └── Gemini/Groq/LLM
  │
  ▼
OUTPUT
  │
  ├── Risk dashboard
  ├── Clause explanations
  ├── AI chat
  ├── Negotiation suggestions
  └── PDF report
  │
  ▼
FEEDBACK
  │
  └── User asks follow-up questions
      → RAG retrieval
      → LLM response
```

---

# 9. Functional Requirements

1. User registration and authentication.
2. Contract upload.
3. PDF/DOCX/scanned document processing.
4. OCR for image-based contracts.
5. Clause segmentation.
6. Clause classification.
7. Risk detection.
8. Indian legal rule checking.
9. Contract-level risk scoring.
10. Clause-level risk scoring.
11. Plain-language explanations.
12. RAG-based contract Q&A.
13. Negotiation/rewrite suggestions.
14. Contract summary.
15. Analysis history.
16. PDF report generation.

---

# 10. Non-Functional Requirements

### Performance

- Normal text PDFs should be processed efficiently.
- API responses should be asynchronous for long-running analysis.
- Large contracts should not block the entire server.

### Security

- HTTPS for communication.
- Password hashing.
- Secure authentication tokens.
- API keys stored only on the backend.
- Uploaded documents must not expose secrets.
- Validate uploaded file types and sizes.
- Avoid logging contract contents unnecessarily.

### Reliability

- Handle OCR failures gracefully.
- Handle LLM/API failures.
- Provide meaningful error messages.
- Preserve completed analysis results.

### Scalability

- Modular FastAPI services.
- Separate ML inference from API logic where appropriate.
- Vector storage independent from application database.
- LLM provider abstraction.

### Maintainability

- Modular repository structure.
- Environment-based configuration.
- Type hints.
- Tests.
- API documentation.
- Git-based version control.

---

# 11. Database Design

## MongoDB

MongoDB stores application-level data.

### Suggested Collections

```text
users
contracts
analyses
clauses
chat_sessions
chat_messages
reports
audit_logs
```

### Example User

```json
{
  "_id": "...",
  "name": "User Name",
  "email": "user@example.com",
  "password_hash": "...",
  "created_at": "..."
}
```

### Example Contract

```json
{
  "_id": "...",
  "user_id": "...",
  "filename": "vendor_agreement.pdf",
  "contract_type": "vendor",
  "status": "completed",
  "overall_risk": 72,
  "created_at": "..."
}
```

---

# 12. ChromaDB Design

ChromaDB stores vector representations of contract chunks/clauses.

Each vector should contain metadata such as:

```json
{
  "contract_id": "...",
  "clause_id": "...",
  "clause_type": "payment",
  "page": 4,
  "source": "uploaded_contract"
}
```

### Purpose

ChromaDB enables:

- semantic search
- relevant clause retrieval
- RAG
- contract-aware chat
- contextual explanations

### Important distinction

```text
MongoDB
→ application data

ChromaDB
→ vector embeddings + retrieval metadata
```

---

# 13. LegalBERT

LegalBERT is the core NLP model for clause classification.

### Training flow

```text
CUAD
  +
Curated Indian Contract Data
  ↓
Data Cleaning
  ↓
Label Mapping
  ↓
Train / Validation / Test Split
  ↓
LegalBERT Fine-Tuning
  ↓
Evaluation
  ↓
Saved Model
```

### Example

Input:

> "The employee shall not disclose confidential information during or after employment."

Output:

```text
Category: Confidentiality
Confidence: 0.96
```

The exact confidence threshold must be determined experimentally rather than hard-coded without evaluation.

---

# 14. Dataset Strategy

## Primary Dataset

### CUAD

Use CUAD as the primary public dataset for contract clause understanding and classification.

Possible categories should be mapped to the project's own taxonomy.

## Indian Contract Dataset

Create a curated dataset containing:

- NDA clauses
- Employment clauses
- Vendor clauses

Each record should ideally include:

```text
contract_id
contract_type
clause_text
clause_category
risk_level
applicable_rule
source
annotation_notes
```

### Important

Do not present a manually collected dataset as an official public dataset. Clearly document:

- source
- collection date
- licensing/permission status
- annotation process
- annotator agreement where possible

---

# 15. Indian Legal Rule Engine

The rule engine should be deterministic and versioned.

## Rule Categories

### Indian Contract Act

Possible checks:

- contractual obligations
- potentially one-sided provisions
- ambiguity indicators
- selected enforceability-related conditions

### MSMED Act

Possible checks:

- payment-related provisions
- applicable delayed-payment conditions for eligible MSME suppliers

### DPDP Act

Possible checks:

- personal-data processing clauses
- purpose/responsibility indicators
- data protection obligations

### Arbitration and Conciliation Act

Possible checks:

- dispute resolution clause
- arbitration mechanism
- selected arbitration-related terms

### Stamp Duty

Possible checks:

- identify agreement/document types that may require stamp-duty verification
- provide a verification warning rather than pretending to calculate every state-specific duty

## Rule Format

Use a structured configuration rather than scattering legal rules through Python code.

Example:

```yaml
rule_id: MSMED_PAYMENT_001
law: MSMED Act
category: payment
condition: applicable_msmse_supplier
check: payment_period
severity: high
message: "Review payment terms against applicable MSMED requirements."
version: "1.0"
source: "official legal source"
```

**Legal rules must be validated against authoritative sources before production use.**

---

# 16. Risk Engine

The risk engine combines signals from:

```text
LegalBERT classification
        +
Rule violations
        +
Clause characteristics
        +
Configured severity
        ↓
Clause Risk
        ↓
Overall Contract Risk
```

Avoid presenting an arbitrary score as a legally meaningful probability.

The UI should explain:

> "Risk score is an AI-assisted prioritization indicator, not a legal determination."

---

# 17. RAG Architecture

```text
Contract
   ↓
Chunk / Clause
   ↓
Embedding Model
   ↓
ChromaDB
   ↓
User Question
   ↓
Question Embedding
   ↓
Similarity Search
   ↓
Top Relevant Clauses
   ↓
Prompt Construction
   ↓
Gemini / Groq / LLM
   ↓
Grounded Response
```

### RAG should provide

- retrieved context
- source clause/page reference where possible
- answer
- confidence/limitations where appropriate

The LLM should not be allowed to silently invent legal provisions.

---

# 18. LangChain's Role

LangChain is the orchestration layer for the RAG workflow.

It can manage:

- document loaders
- text splitters
- embedding integrations
- vector-store retrieval
- prompt templates
- LLM calls
- retrieval chains
- conversational context

LangChain is **not the LLM**.

---

# 19. Tesseract OCR

Tesseract is used for scanned/image-based documents.

```text
Scanned PDF
    ↓
Render pages
    ↓
Tesseract OCR
    ↓
Machine-readable text
    ↓
Clause segmentation
```

For normal text PDFs, use direct extraction first and use OCR only where necessary.

---

# 20. LLM Layer

The LLM is responsible primarily for generative tasks.

### Suitable tasks

- plain-language explanation
- contract summary
- AI chat
- negotiation suggestions
- rewriting suggestions
- structured report narrative

### The LLM should NOT be the sole source of:

- legal compliance decisions
- clause classification
- deterministic rule violations

Those should be supported by the ML classifier and rule engine.

---

# 21. API Design

Suggested FastAPI endpoints:

```text
POST   /api/v1/auth/register
POST   /api/v1/auth/login

POST   /api/v1/contracts/upload
GET    /api/v1/contracts
GET    /api/v1/contracts/{contract_id}
DELETE /api/v1/contracts/{contract_id}

POST   /api/v1/contracts/{contract_id}/analyze
GET    /api/v1/contracts/{contract_id}/analysis

GET    /api/v1/contracts/{contract_id}/clauses
GET    /api/v1/contracts/{contract_id}/risks

POST   /api/v1/contracts/{contract_id}/chat
POST   /api/v1/contracts/{contract_id}/suggestions

GET    /api/v1/contracts/{contract_id}/report
GET    /api/v1/health
```

Actual endpoint naming may be adjusted during implementation, but maintain consistent REST conventions.

---

# 22. Suggested Backend Structure

```text
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── contracts.py
│   │   │   ├── analysis.py
│   │   │   ├── chat.py
│   │   │   └── reports.py
│   │
│   ├── core/
│   │   ├── security.py
│   │   ├── exceptions.py
│   │   └── logging.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── contract.py
│   │   └── analysis.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── contract.py
│   │   └── analysis.py
│   │
│   ├── services/
│   │   ├── document_service.py
│   │   ├── ocr_service.py
│   │   ├── clause_service.py
│   │   ├── classifier_service.py
│   │   ├── risk_service.py
│   │   ├── rule_engine.py
│   │   ├── embedding_service.py
│   │   ├── rag_service.py
│   │   ├── llm_service.py
│   │   └── report_service.py
│   │
│   ├── db/
│   │   ├── mongodb.py
│   │   └── chromadb.py
│   │
│   └── prompts/
│       ├── explanation.txt
│       ├── chat.txt
│       └── negotiation.txt
│
├── ml/
│   ├── training/
│   ├── evaluation/
│   ├── inference/
│   └── models/
│
├── legal_rules/
│   ├── contract_act.yaml
│   ├── msmed.yaml
│   ├── dpdp.yaml
│   ├── arbitration.yaml
│   └── stamp_duty.yaml
│
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

---

# 23. Suggested Flutter Structure

```text
frontend/
├── lib/
│   ├── main.dart
│   │
│   ├── core/
│   │   ├── constants/
│   │   ├── theme/
│   │   ├── network/
│   │   └── utils/
│   │
│   ├── models/
│   │   ├── user.dart
│   │   ├── contract.dart
│   │   ├── clause.dart
│   │   └── analysis.dart
│   │
│   ├── services/
│   │   ├── api_service.dart
│   │   ├── auth_service.dart
│   │   └── storage_service.dart
│   │
│   ├── providers/
│   │   ├── auth_provider.dart
│   │   ├── contract_provider.dart
│   │   └── analysis_provider.dart
│   │
│   └── screens/
│       ├── auth/
│       ├── home/
│       ├── upload/
│       ├── contract/
│       ├── dashboard/
│       ├── chat/
│       └── report/
│
├── test/
└── pubspec.yaml
```

---

# 24. UI Screens

## Authentication

- Splash
- Login
- Register

## Home

- Recent contracts
- Risk overview
- Upload button

## Upload

- File picker
- Contract type selection
- Processing status

## Analysis Dashboard

Display:

- Overall risk
- Risk distribution
- Compliance alerts
- Clause categories
- High-risk clauses

## Clause Viewer

Each clause should show:

```text
Clause
Category
Risk Level
Reason
Applicable Rule
Source
Suggested Action
```

## AI Chat

User can ask:

> "What does the termination clause mean?"

The response should cite/refer to the relevant contract clause when available.

## Report

Include:

- Contract details
- Overall risk
- Clause findings
- Legal checks
- Explanations
- Recommendations
- Limitations/disclaimer

---

# 25. Development Roadmap

## Phase 1 — Research & Requirements

- Finalize contract types
- Finalize clause taxonomy
- Finalize selected legal rules
- Review literature
- Define evaluation metrics

**Deliverable:** System specification

---

## Phase 2 — Dataset

- Download CUAD
- Analyze labels
- Map labels to project categories
- Collect permitted Indian contract samples
- Annotate selected Indian clauses
- Split data

**Deliverable:** Training/validation/test datasets

---

## Phase 3 — LegalBERT

- Tokenization
- Data loaders
- Fine-tuning
- Validation
- Hyperparameter experiments
- Evaluation
- Save model

**Deliverable:** Fine-tuned clause classifier

---

## Phase 4 — Document Processing

Implement:

- PDF extraction
- DOCX extraction
- OCR fallback
- text normalization
- page tracking
- clause segmentation

**Deliverable:** Document processing pipeline

---

## Phase 5 — Legal Rule Engine

Implement versioned rules for the selected legal areas.

Each finding should include:

```text
rule_id
law
clause_id
trigger
severity
explanation
source
version
```

**Deliverable:** Indian legal compliance module

---

## Phase 6 — RAG

Implement:

- chunking
- embeddings
- ChromaDB
- retrieval
- LangChain
- prompt templates
- LLM provider abstraction

**Deliverable:** Contract-aware AI chat

---

## Phase 7 — Risk Engine

Combine:

- classifier results
- rule results
- configured severity

Create:

- clause risk
- overall risk
- risk explanation

**Deliverable:** Risk analysis engine

---

## Phase 8 — FastAPI

Build:

- authentication
- upload API
- analysis API
- chat API
- report API
- database integration

**Deliverable:** Backend service

---

## Phase 9 — Flutter

Build:

- authentication
- upload
- dashboard
- clause viewer
- AI chat
- report screen

**Deliverable:** Mobile application

---

## Phase 10 — Testing

### Unit Tests

- OCR
- parsing
- clause segmentation
- rule engine
- classifier
- risk calculation

### Integration Tests

```text
Upload
 → Parse
 → Classify
 → Rules
 → RAG
 → LLM
 → Report
```

### Evaluation

- Accuracy
- Precision
- Recall
- F1
- Retrieval quality
- latency
- failure rate

---

# 26. Testing Strategy

## ML Evaluation

Use a held-out test set.

Report:

```text
Accuracy
Precision
Recall
F1-score
Confusion Matrix
```

Do not evaluate only on training data.

## RAG Evaluation

Evaluate:

- retrieval relevance
- answer faithfulness
- context coverage
- citation/source correctness

## Rule Engine

Create manually verified test cases:

```text
Input clause
Expected rule
Expected severity
Actual rule
Actual severity
Pass/Fail
```

---

# 27. Explainability

SHAP can be used for the ML component where the model and explanation method are technically compatible.

The system should expose understandable information such as:

```text
Clause Category:
Payment

Prediction:
Payment Clause

Confidence:
0.94

Risk:
High

Reason:
Applicable rule triggered.
```

Do not claim that SHAP proves legal correctness.

---

# 28. Security Requirements

The project handles potentially sensitive contracts.

Minimum requirements:

- HTTPS
- secure password hashing
- authentication tokens
- authorization checks
- file-type validation
- file-size limits
- secure temporary files
- API-key protection
- access control by user ID
- minimal logging of contract contents
- safe error handling
- dependency updates
- secret management through environment variables

### Never commit:

```text
.env
API keys
passwords
JWT secrets
private contracts
user documents
database credentials
```

---

# 29. Environment Variables

Create:

```text
.env.example
```

Example:

```env
APP_ENV=development
SECRET_KEY=change_me

MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=lexintel

CHROMA_PERSIST_DIRECTORY=./storage/chroma

LLM_PROVIDER=gemini
GEMINI_API_KEY=
GROQ_API_KEY=

MODEL_PATH=./ml/models/legalbert

MAX_UPLOAD_MB=25
```

Use different environment variables for development and production.

---

# 30. Local Development

## Backend

```bash
cd backend

python -m venv .venv
```

### Windows

```bash
.venv\Scripts\activate
```

### Linux/macOS

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
uvicorn app.main:app --reload
```

---

# 31. Frontend

```bash
cd frontend
flutter pub get
flutter run
```

Configure the backend URL through an environment/configuration layer rather than hard-coding it.

Example:

```text
API_BASE_URL=https://your-backend-domain
```

---

# 32. Model Training

Training should be separated from production inference.

Example:

```bash
cd backend

python ml/training/prepare_dataset.py
python ml/training/train.py
python ml/evaluation/evaluate.py
```

The final model should be saved under:

```text
ml/models/
```

Large model artifacts should normally not be committed directly to GitHub. Use an appropriate model registry/storage solution if necessary.

---

# 33. Git Workflow

Recommended branches:

```text
main
develop
feature/auth
feature/document-processing
feature/legalbert
feature/rag
feature/rule-engine
feature/flutter-ui
```

Commit examples:

```text
feat: add contract upload API
feat: implement clause segmentation
feat: add LegalBERT inference
feat: implement MSMED rule checks
feat: add ChromaDB retrieval
fix: handle OCR failure
test: add rule engine tests
docs: update architecture
```

---

# 34. Recommended Repository Layout

```text
LexIntel-AI/
│
├── backend/
├── frontend/
├── ml/
├── datasets/
├── legal_rules/
├── docs/
│   ├── architecture/
│   ├── research/
│   └── diagrams/
├── tests/
├── scripts/
├── .github/
│   └── workflows/
├── .gitignore
├── LICENSE
├── README.md
└── CONTRIBUTING.md
```

---

# 35. API/LLM Provider Abstraction

Do not tightly couple the application to one LLM provider.

Recommended interface:

```python
class LLMProvider:
    def generate(self, prompt: str, context: list[str]) -> str:
        raise NotImplementedError
```

Implement providers such as:

```text
GeminiProvider
GroqProvider
OllamaProvider
```

This allows the project to switch providers without rewriting the RAG system.

---

# 36. Important AI Design Rules

### Rule 1 — Retrieval Before Generation

For contract-specific questions:

```text
Question
 → Retrieve
 → Context
 → LLM
```

### Rule 2 — Don't Let the LLM Decide Everything

Use:

```text
ML
+
Rule Engine
+
RAG
+
LLM
```

instead of:

```text
Contract → LLM → Legal Decision
```

### Rule 3 — Preserve Evidence

Every important finding should ideally retain:

```text
contract_id
page
clause_id
clause_text
rule_id
model_prediction
risk
```

This makes the result auditable.

---

# 37. Example End-to-End Scenario

User uploads:

```text
vendor_agreement.pdf
```

The system performs:

```text
1. Validate file
2. Extract text
3. OCR pages if required
4. Segment clauses
5. Classify clauses using LegalBERT
6. Run Indian legal rules
7. Calculate risk indicators
8. Generate embeddings
9. Store embeddings in ChromaDB
10. Store analysis metadata in MongoDB
11. Generate explanations using RAG + LLM
12. Display dashboard
13. Allow AI chat
14. Generate PDF report
```

Example output:

```text
Contract Type: Vendor Agreement

Overall Risk: High

High-Risk Findings:
1. Payment Clause
2. Unlimited Liability
3. Data Processing Clause

Medium-Risk Findings:
1. Termination
2. Dispute Resolution
```

The actual risk classification must come from the implemented model/rules and evaluation, not from arbitrary hard-coded examples.

---

# 38. Example AI Chat

### User

> What is the payment deadline?

### Retrieval

```text
Clause 7:
"Payment shall be made within 90 days..."
```

### LLM

> "According to Clause 7, payment is due within 90 days. The system has flagged this clause for review based on the applicable configured legal rules."

The response should identify the source clause whenever possible.

---

# 39. Example Negotiation Suggestion

### Original

> "The vendor shall be liable for all losses without limitation."

### System

```text
Category: Liability
Risk: High
```

### Suggested wording

> "The parties may consider defining a reasonable liability cap and specifying exclusions for indirect or consequential losses."

The system should present this as a **suggestion for review**, not guaranteed legally valid wording.

---

# 40. Legal Safety

LexIntel AI must clearly communicate:

> **This system provides AI-assisted contract analysis for informational and decision-support purposes. It does not constitute legal advice and does not determine the final legal validity or enforceability of any contract or clause. Users should consult a qualified legal professional for decisions requiring legal advice.**

For legal rules, record:

- source
- law name
- provision/reference
- effective date/version where applicable
- last verification date

Do not silently rely on outdated legal rules.

---

# 41. Known Limitations

1. LegalBERT may misclassify unusual clauses.
2. CUAD is not an Indian-law dataset.
3. Curated Indian data may initially be small.
4. Legal language is highly context-dependent.
5. OCR may introduce extraction errors.
6. RAG retrieval can return incomplete context.
7. LLMs can hallucinate.
8. Indian legal requirements can vary by facts, document type, and applicable state provisions.
9. Stamp duty is especially context/state dependent and should be treated as a verification workflow rather than a universal calculation.
10. The project is not a substitute for legal professionals.

---

# 42. Future Enhancements

- Larger Indian legal dataset
- More Indian contract types
- Multilingual Indian-language support
- Legal knowledge graph
- More advanced consistency checking
- Better long-document models
- Human-in-the-loop lawyer review
- Versioned legal-rule updates
- Web application
- Desktop application
- Enterprise document management
- Advanced citation/evidence tracking
- Optional multi-agent architecture
- Lawyer feedback loop for model improvement

---

# 43. Research Evaluation

The project should compare:

### Baseline 1

Traditional ML classifier

### Baseline 2

Zero-shot/general LLM classification

### Proposed

Fine-tuned LegalBERT

Compare:

```text
Accuracy
Precision
Recall
F1
```

For RAG:

```text
Retrieval Relevance
Answer Faithfulness
Context Coverage
```

This makes the project more academically meaningful than simply demonstrating a working application.

---

# 44. Research Gap

Existing research demonstrates:

- legal NLP
- contract clause classification
- abusive clause detection
- legal document retrieval
- RAG-based legal Q&A
- formal contract reasoning

However, LexIntel AI focuses on combining these approaches for:

> **India-specific contract intelligence covering selected Indian legal provisions and NDA, Employment, and Vendor contracts.**

The project therefore emphasizes the integration of:

```text
LegalBERT
    +
Indian Rule Engine
    +
RAG
    +
ChromaDB
    +
Generative AI
    +
Risk Analysis
```

---

# 45. Research References

Core references for the project include:

1. Dadas et al., "A Support System for the Detection of Abusive Clauses in B2C Contracts," *Artificial Intelligence and Law*, Springer.
2. Singh et al., "A Survey of Classification Tasks and Approaches for Legal Contracts," *Artificial Intelligence Review*, Springer.
3. Khoja et al., "Automated Consistency Analysis for Legal Contracts," *Artificial Intelligence and Law*, Springer.
4. Wardas and Matthes, "AI-assisted German Employment Contract Review: A Benchmark Dataset," 2025.
5. Raptopoulos et al., "PAKTON: A Multi-Agent Framework for Question Answering in Long Legal Agreements," EMNLP, 2025.
6. Bommarito et al., "LexNLP: Natural Language Processing and Information Extraction for Legal and Regulatory Texts," 2018.
7. Chalkidis et al., "LEGAL-BERT: The Muppets straight out of Law School," EMNLP Findings, 2020.
8. Hendrycks et al., "CUAD: An Expert-Annotated NLP Dataset for Legal Contract Review," 2021.
9. Koreeda and Manning, "ContractNLI: A Dataset for Document-level Natural Language Inference for Contracts," EMNLP Findings, 2021.
10. Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks," NeurIPS, 2020.
11. Reimers and Gurevych, "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks," EMNLP-IJCNLP, 2019.
12. Lundberg and Lee, "A Unified Approach to Interpreting Model Predictions," NeurIPS, 2017.

The final repository should include the complete verified bibliography in `docs/references.md` or the project's required citation format.

---

# 46. Coding Agent Instructions

This section can be provided directly to an AI coding agent.

## Role

You are the lead software engineer implementing **LexIntel AI**, an India-specific AI contract intelligence platform.

Build a production-quality academic prototype using the architecture and requirements in this README.

## Non-Negotiable Requirements

1. Use **Flutter** for the client.
2. Use **FastAPI + Python** for the backend.
3. Use **LegalBERT** for clause classification.
4. Use **Tesseract OCR** as the scanned-document OCR fallback.
5. Use **PyMuPDF** for normal PDF text extraction.
6. Use **MongoDB** for application data.
7. Use **ChromaDB** for vector embeddings/retrieval.
8. Use **LangChain** for the RAG orchestration layer.
9. Support an LLM abstraction for **Gemini, Groq, and optionally Ollama**.
10. Implement a separate **Indian legal rule engine**.
11. Keep ML inference, legal rules, RAG, LLM, database, and API logic modular.
12. Never hard-code API keys.
13. Never expose LLM API keys to Flutter.
14. Add tests for critical services.
15. Add structured logging without logging sensitive contract contents.
16. Do not claim legal certainty.
17. Show source/evidence metadata for important findings whenever available.
18. Make the system runnable locally before cloud deployment.
19. Do not fabricate legal rules, datasets, legal provisions, citations, or model performance.
20. Do not claim a model is accurate until it has actually been evaluated.

## Implementation Order

Implement in this order:

```text
1. Repository structure
2. Environment/configuration
3. MongoDB connection
4. Authentication
5. Contract upload
6. PDF/DOCX extraction
7. OCR fallback
8. Clause segmentation
9. LegalBERT inference
10. Legal rule engine
11. Risk engine
12. Embedding pipeline
13. ChromaDB
14. RAG
15. LLM provider abstraction
16. AI chat
17. Report generation
18. FastAPI integration
19. Flutter UI
20. Testing
21. Docker/deployment
22. Documentation
```

## Coding Standards

- Python type hints
- Pydantic schemas
- async FastAPI endpoints where appropriate
- service/repository separation
- configuration through environment variables
- meaningful exception handling
- unit tests
- integration tests
- clean naming
- no duplicated business logic
- no hard-coded secrets
- no unnecessary dependencies
- clear README/documentation

## Error Handling

The system must gracefully handle:

- unsupported file
- corrupt PDF
- OCR failure
- empty extracted text
- unsupported contract type
- model unavailable
- ChromaDB failure
- MongoDB failure
- LLM timeout
- LLM quota error
- malformed LLM output
- unauthorized request

Never expose stack traces or secrets to end users.

## LLM Output

Prefer structured JSON for internal LLM tasks where possible:

```json
{
  "summary": "...",
  "risk_explanation": "...",
  "suggestion": "...",
  "limitations": "..."
}
```

Validate generated JSON before using it.

## RAG Requirements

For every RAG response:

1. retrieve relevant chunks
2. preserve contract ID
3. preserve clause/page metadata
4. construct context
5. call LLM
6. validate response
7. return answer + evidence metadata

If no relevant context is found, the system should say that sufficient contract evidence was not retrieved rather than inventing an answer.

## Rule Engine Requirements

Legal rules must be configuration-driven.

Do not implement legal logic as:

```python
if x:
    print("illegal")
```

Instead use versioned rule definitions and return:

```text
rule_id
law
condition
severity
explanation
source
version
```

The engine should report:

> "Potential issue detected; review against applicable provision."

rather than automatically declaring a clause illegal.

---

# 47. Definition of Done

The project is considered complete when:

- [ ] User can register/login.
- [ ] User can upload PDF/DOCX/scanned contract.
- [ ] System extracts text.
- [ ] OCR works for scanned pages.
- [ ] Contract is segmented into clauses.
- [ ] LegalBERT classifies supported clause types.
- [ ] Rule engine executes configured Indian legal checks.
- [ ] Risk results are generated.
- [ ] Contract embeddings are stored in ChromaDB.
- [ ] User can ask questions about the uploaded contract.
- [ ] RAG retrieves relevant clauses.
- [ ] LLM generates contextual responses.
- [ ] AI suggestions are generated.
- [ ] Dashboard displays analysis.
- [ ] PDF report can be generated.
- [ ] MongoDB stores application data.
- [ ] API authentication/authorization works.
- [ ] Tests cover critical components.
- [ ] Secrets are protected.
- [ ] README and setup instructions are complete.
- [ ] The application can run locally from a clean setup.
- [ ] Deployment configuration is documented.

---

# 48. Final Product Vision

```text
                 LEXINTEL AI
        India-Specific Contract Intelligence
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
   CLASSIFY          CHECK          EXPLAIN
   LegalBERT       Rule Engine       RAG + LLM
        │              │              │
        └──────────────┼──────────────┘
                       ▼
                  RISK ANALYSIS
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
    AI CHAT       SUGGESTIONS       REPORT
```

**Core principle:**

> **Use ML to understand the contract, deterministic rules to perform explicit legal checks, RAG to retrieve evidence, and Generative AI to explain the results in simple language.**
