from fraud_detector import FraudDetector


def main():
    print("=" * 50)
    print("TRACEGUARD AI - FRAUD DETECTOR TEST")
    print("=" * 50)

    detector = FraudDetector()

    # Test transaction retrieval
    transactions = detector.get_transactions()

    print("\n1. TRANSACTION RETRIEVAL")
    print("Total transactions:", len(transactions))

    for transaction in transactions[:3]:
        print(transaction)

    # Test shared-device relationships
    shared_devices = detector.get_shared_devices()

    print("\n2. SHARED-DEVICE RELATIONSHIPS")
    print("Total relationships:", len(shared_devices))

    for relationship in shared_devices:
        print(relationship)

    # Test graph data
    graph_data = detector.get_graph_data()

    print("\n3. GRAPH DATA")
    print(
        "Account-device links:",
        len(graph_data["account_device_links"])
    )
    print(
        "Transactions in graph data:",
        len(graph_data["transactions"])
    )

    # Test risk scoring
    sample_transaction = {
        "transaction_id": "TEST001",
        "account_id": "TEST_ACC",
        "amount": 10000,
        "status": "completed",
        "timestamp": "2026-10-17"
    }

    risk_report = detector.calculate_risk(
        sample_transaction,
        shared_device=True
    )

    print("\n4. RISK SCORING")
    print(risk_report)

    assert risk_report["risk_score"] == 70
    assert risk_report["risk_level"] == "HIGH"

    print("\nPASS: Fraud detector checks completed.")


if __name__ == "__main__":
    main()