from falkordb import FalkorDB


class FraudDetector:
    """
    TraceGuard AI fraud investigation engine.

    Features:
    - Retrieves unique transactions.
    - Recovers account IDs through graph relationships.
    - Identifies accounts sharing devices.
    - Calculates explainable rule-based risk scores.
    - Produces investigation results for the dashboard.
    """

    def __init__(self, host="localhost", port=6379, graph_name="traceguard"):
        """Connect to FalkorDB and select the project graph."""
        self.db = FalkorDB(host=host, port=port)
        self.graph = self.db.select_graph(graph_name)

    # --------------------------------------------------
    # GET UNIQUE TRANSACTIONS
    # --------------------------------------------------

    def get_transactions(self):
        """
        Return one transaction record per transaction ID.

        Account IDs are recovered from INITIATED relationships
        when the transaction's account_id property is missing.

        Duplicate transaction nodes are not deleted.
        """

        query = """
        MATCH (t:Transaction)
        WHERE t.id IS NOT NULL

        WITH t.id AS transaction_id,
             collect(t) AS transaction_nodes

        WITH transaction_id,
             transaction_nodes[0] AS t

        OPTIONAL MATCH (a:Account)-[:INITIATED]->(t)

        WITH transaction_id,
             t,
             collect(DISTINCT a.id) AS account_ids

        RETURN
            transaction_id AS transaction_id,
            CASE
                WHEN t.account_id IS NOT NULL
                THEN t.account_id
                ELSE account_ids[0]
            END AS account_id,
            t.amount AS amount,
            t.status AS status,
            t.timestamp AS timestamp

        ORDER BY transaction_id
        """

        result = self.graph.query(query)

        transactions = []

        for row in result.result_set:
            transactions.append({
                "transaction_id": row[0],
                "account_id": row[1],
                "amount": row[2],
                "status": row[3],
                "timestamp": row[4]
            })

        return transactions

    # --------------------------------------------------
    # GET ACCOUNT-DEVICE RELATIONSHIPS
    # --------------------------------------------------

    def get_graph_data(self):
        """
        Return account-device relationships and unique transactions.
        """

        query = """
        MATCH (a:Account)-[:USES_DEVICE]->(d:Device)

        RETURN DISTINCT
            a.id AS account_id,
            d.id AS device_id

        ORDER BY account_id, device_id
        """

        result = self.graph.query(query)

        account_device_links = []

        for row in result.result_set:
            account_device_links.append({
                "account_id": row[0],
                "device_id": row[1]
            })

        return {
            "account_device_links": account_device_links,
            "transactions": self.get_transactions()
        }

    # --------------------------------------------------
    # FIND ACCOUNTS SHARING DEVICES
    # --------------------------------------------------

    def get_shared_devices(self):
        """
        Identify pairs of accounts connected to the same device.

        A shared device is an investigation indicator, not proof
        of fraud.
        """

        query = """
        MATCH (a1:Account)-[:USES_DEVICE]->(d:Device)
              <-[:USES_DEVICE]-(a2:Account)

        WHERE a1.id < a2.id

        RETURN DISTINCT
            a1.id AS account_1,
            a2.id AS account_2,
            d.id AS device_id

        ORDER BY account_1, account_2, device_id
        """

        result = self.graph.query(query)

        shared_devices = []

        for row in result.result_set:
            shared_devices.append({
                "account_1": row[0],
                "account_2": row[1],
                "device_id": row[2]
            })

        return shared_devices

    # --------------------------------------------------
    # CALCULATE TRANSACTION RISK
    # --------------------------------------------------

    def calculate_risk(self, transaction, shared_device=False):
        """
        Calculate an illustrative rule-based risk score.

        Rules:
        - Amount >= 9000: +30 points.
        - Account participates in a shared-device relationship: +40.
        - Status is not completed: +10.

        These thresholds are configurable examples, not a
        statistically validated fraud prediction model.
        """

        score = 0
        reasons = []

        # Safely parse the transaction amount.
        try:
            amount = float(transaction.get("amount") or 0)
        except (TypeError, ValueError):
            amount = 0.0

        status = str(
            transaction.get("status") or ""
        ).strip().lower()

        # Rule 1: High transaction amount.
        if amount >= 9000:
            score += 30
            reasons.append(
                f"High transaction amount: {amount:g}"
            )

        # Rule 2: Account has a shared-device relationship.
        if shared_device:
            score += 40
            reasons.append(
                "Account participates in a shared-device "
                "relationship"
            )

        # Rule 3: Transaction is not completed.
        if status != "completed":
            score += 10
            reasons.append(
                f"Transaction status is "
                f"'{status or 'unknown'}', not 'completed'"
            )

        # Restrict score to the range 0-100.
        score = min(max(score, 0), 100)

        # Assign the risk category.
        if score >= 70:
            level = "HIGH"
        elif score >= 30:
            level = "MEDIUM"
        else:
            level = "LOW"

        if not reasons:
            reasons.append(
                "No configured risk indicators were triggered"
            )

        return {
            "transaction_id": transaction.get("transaction_id"),
            "risk_score": score,
            "risk_level": level,
            "reasons": reasons
        }

    # --------------------------------------------------
    # INVESTIGATE ALL TRANSACTIONS
    # --------------------------------------------------

    def investigate(self):
        """
        Investigate each unique transaction and return its
        risk assessment, transaction details, and shared-device
        relationship evidence.
        """

        transactions = self.get_transactions()
        shared_devices = self.get_shared_devices()

        # Build a mapping of account IDs to their shared devices.
        shared_devices_by_account = {}

        for relationship in shared_devices:
            account_1 = relationship.get("account_1")
            account_2 = relationship.get("account_2")

            device_id = relationship.get("device_id")

            if account_1 is not None:
                key = str(account_1)

                shared_devices_by_account.setdefault(key, []).append(
                    relationship
                )

            if account_2 is not None:
                key = str(account_2)

                shared_devices_by_account.setdefault(key, []).append(
                    relationship
                )

        investigations = []

        for transaction in transactions:
            account_id = transaction.get("account_id")

            account_key = (
                str(account_id)
                if account_id is not None
                else None
            )

            # Retrieve the relationships involving this account.
            account_relationships = (
                shared_devices_by_account.get(account_key, [])
                if account_key is not None
                else []
            )

            shared_device = len(account_relationships) > 0

            # Calculate the risk assessment.
            risk_report = self.calculate_risk(
                transaction,
                shared_device=shared_device
            )

            # Preserve the fields expected by the dashboard
            # and AI assistant.
            risk_report.update({
                "account_id": account_id,
                "amount": transaction.get("amount"),
                "status": transaction.get("status"),
                "timestamp": transaction.get("timestamp"),
                "shared_device_relationships": account_relationships
            })

            investigations.append(risk_report)

        return investigations