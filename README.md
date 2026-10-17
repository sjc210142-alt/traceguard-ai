# 🛡️ TraceGuard AI

### AI-Assisted Financial Fraud Investigation Dashboard

TraceGuard AI is a Python-based investigation dashboard that
combines transaction risk indicators, graph relationships,
and locally generated AI reports to support financial fraud
investigations.

## Features

- Transaction risk scoring and risk-level classification
- Transaction search and risk filtering
- Shared-device relationship investigation
- Interactive account-device-transaction graph
- Local AI investigation reports using Ollama
- CSV export for investigation results
- Downloadable AI investigation reports
- SQLite-based investigation history
- Evidence-focused reporting and investigation limitations

## Technology Stack

- Python
- Streamlit
- Pandas
- FalkorDB
- Graph query language (Cypher-compatible)
- Ollama
- Llama 3.2
- SQLite
- streamlit-agraph

## Architecture

1. FalkorDB stores transaction, account, and device relationships.
2. The fraud detection module retrieves transactions and applies
   configurable risk-scoring rules.
3. Streamlit presents transaction results and graph relationships.
4. Ollama generates structured investigation reports locally.
5. SQLite stores investigation history and generated reports.
6. CSV and text downloads support reviewing and sharing results.

## Risk Scoring

The current demonstration rules are:

- Transaction amount of at least 9,000: +30 points
- Account associated with a shared device: +40 points
- Transaction status other than completed: +10 points
- Maximum risk score: 100

Risk levels:

- LOW: 0–29
- MEDIUM: 30–69
- HIGH: 70–100

These rules are illustrative and have not been statistically
validated against a labeled fraud dataset.

## Installation

Install the required Python packages in your environment:

```bash
python -m pip install streamlit pandas falkordb streamlit-agraph