from ai_assistant import generate_investigation_report

sample_transaction = {
    "transaction_id": "TXN001",
    "risk_score": 30,
    "risk_level": "MEDIUM",
    "reasons": ["High transaction amount"],
}

sample_shared_devices = [
    {
        "accounts": ["ACC001", "ACC002"],
        "device_id": "DEV001",
        "observation": "Both accounts are connected to the same device.",
    }
]

report = generate_investigation_report(
    sample_transaction,
    sample_shared_devices,
)

print("\n=== TRACEGUARD AI INVESTIGATION REPORT ===\n")
print(report)
