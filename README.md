# TraceGuard AI
### Graph-Powered Financial Fraud Investigation Assistant

TraceGuard AI is a prototype that helps investigators examine potentially suspicious financial activity by combining graph-based relationship analysis, configurable risk scoring, and locally generated AI investigation reports.

## Problem Statement

Financial fraud investigations can involve many transactions, accounts, and shared devices. Examining each record independently can make potentially relevant relationships difficult to identify.

TraceGuard AI uses FalkorDB to examine account-device relationships and combines the graph evidence with transparent risk-scoring rules to prioritize records for human review.

## Key Features

- Graph-based account and device relationship analysis using FalkorDB.
- Rule-based transaction risk scoring.
- Shared-device relationship detection.
- Transaction amount anomaly checks using the Interquartile Range (IQR) method.
- AI-generated investigation summaries using Ollama and a local language model.
- Investigation history stored in SQLite.
- Dashboard visualization and CSV export.
- Evidence summaries and limitations to support human review.

## Technology Stack

- Python
- Streamlit
- FalkorDB
- Ollama
- Llama 3.2
- SQLite
- Pandas
- Streamlit-Agraph

## Architecture

1. **Data layer:** Transaction records and account-device relationships provide the investigation evidence.
2. **Graph layer:** FalkorDB represents connections between accounts and devices.
3. **Risk analysis:** Python applies configurable rules and amount-anomaly checks.
4. **AI assistance:** Ollama generates an investigation summary from the supplied evidence.
5. **History:** SQLite stores investigation history.
6. **User interface:** Streamlit presents results, graph information, reports, and export options.

## Graph Data Model

The current graph model uses:

- `(Account)` — an account identifier.
- `(Device)` — a device identifier.
- `(Account)-[:USES_DEVICE]->(Device)` — an account-to-device relationship.
- `(Transaction)` — transaction properties such as transaction ID, account ID, amount, status, and timestamp, depending on the data loaded.

### Example graph pattern

```text
(Account A) ──USES_DEVICE──> (Device X) <──USES_DEVICE── (Account B)
```

A device associated with multiple accounts may be relevant to an investigation. This relationship alone does not prove fraud or establish that a particular transaction used that device.

## Example Cypher Queries

### 1. Inspect account-device relationships

```cypher
MATCH (a:Account)-[:USES_DEVICE]->(d:Device)
RETURN a.id AS account_id, d.id AS device_id
ORDER BY a.id, d.id;
```

### 2. Find accounts sharing a device

```cypher
MATCH (a1:Account)-[:USES_DEVICE]->(d:Device)<-[:USES_DEVICE]-(a2:Account)
WHERE a1.id < a2.id
RETURN
    a1.id AS account_1,
    a2.id AS account_2,
    d.id AS shared_device
ORDER BY a1.id, a2.id;
```

### 3. Inspect transaction nodes

Use this query if transactions are stored as nodes with the listed properties:

```cypher
MATCH (t:Transaction)
RETURN
    t.id AS transaction_id,
    t.account_id AS account_id,
    t.amount AS amount,
    t.status AS status,
    t.timestamp AS timestamp
ORDER BY t.id;
```

**Note:** These queries document the expected graph pattern. Confirm that node labels, relationship types, and property names match the graph created by your current implementation before relying on them.

## Risk-Scoring Rules

The current prototype uses configurable example rules:

| Rule | Example score contribution |
|---|---:|
| Transaction amount >= 9,000 | +30 |
| Account associated with a shared device | +40 |
| Transaction status is not completed | +10 |
| Amount anomaly detected | +20 |

The score is capped at 100.

| Risk score | Risk level |
|---|---|
| 0–29 | Low |
| 30–69 | Medium |
| 70–100 | High |

These values are illustrative rules for a prototype, not a validated financial fraud model. The score is a prioritization aid, not a probability that fraud occurred.

## AI Investigation Reports

TraceGuard AI can use a locally running Ollama model to generate an investigation summary from the evidence supplied by the application.

AI-generated summaries may be inaccurate. Investigators should verify the underlying records and graph relationships before making decisions.

## Prerequisites

- Python 3.12 recommended.
- Git.
- FalkorDB running locally or at an accessible endpoint.
- Ollama installed with the `llama3.2` model.
- A compatible browser.

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/sjc210142-alt/traceguard-ai.git
cd traceguard-ai
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If dependencies are missing, install the packages listed in `requirements.txt` rather than assuming that this list is complete.

### 4. Start FalkorDB

Start a FalkorDB instance and confirm that the endpoint and port match the application's configuration. The default local port used during development is `6379`.

Load or create the graph data required by the application before running an investigation.

### 5. Start Ollama

Ensure Ollama is running, then download the model if necessary:

```powershell
ollama pull llama3.2
```

Check the installed model:

```powershell
ollama list
```

The application expects the configured Ollama endpoint to be reachable, normally at `http://localhost:11434`.

### 6. Run the dashboard

```powershell
python -m streamlit run app.py --server.port 8505
```

Open the local URL printed by Streamlit in your terminal.

## Run Tests

Run the individual tests:

```powershell
python .\test_graph.py
python .\test_fraud_detector.py
python .\test_ai_assistant.py
```

Run the configured test suite:

```powershell
python .\run_all_tests.py
```

Check Python syntax:

```powershell
python -m py_compile app.py fraud_detector.py ai_assistant.py investigation_history.py
```

## Limitations and Responsible Use

- This project is a prototype, not a production-grade fraud detection system.
- Risk scores depend on configurable rules and the quality of the available data.
- A shared device is an investigative signal, not proof of fraud.
- Amount anomalies can produce false positives and false negatives.
- AI-generated text must be checked against the underlying evidence.
- Do not use private customer data in a public demonstration.
- Final decisions must be made by qualified human investigators.

## AI-Assistance Disclosure

AI coding assistance was used during development for explanation, debugging, code review, and documentation. The project author is responsible for reviewing the implementation, understanding the graph model and queries, and verifying the submitted work.

## Hackathon

Project: TraceGuard AI  
Graph database: FalkorDB  
Track: Agents That Act on Connected Data

## Future Improvements

- Add richer account-transaction graph relationships.
- Add configurable risk rules through the interface.
- Evaluate the scoring system against labelled synthetic data.
- Add investigation audit trails and evidence provenance.
- Improve graph exploration and report reproducibility.

## License

Add a license file if you intend to distribute the project under an open-source license.