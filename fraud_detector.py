from falkordb import FalkorDB
import math


class FraudDetector:
    """
    Rule-based fraud investigation with statistical anomaly detection.

    Features:
    - Transaction retrieval from FalkorDB.
    - Account-device relationship analysis.
    - IQR-based transaction amount anomaly detection.
    - Explainable risk scoring.
    - Recommended investigation actions.
    - Evidence limitations.

    Important:
    These rules are illustrative and do not prove fraud.
    Risk scores are not validated fraud probabilities.
    """

    # Configuration
    HIGH_AMOUNT_THRESHOLD = 9000

    HIGH_RISK_THRESHOLD = 70
    MEDIUM_RISK_THRESHOLD = 30

    SHARED_DEVICE_POINTS = 40
    HIGH_AMOUNT_POINTS = 30
    INCOMPLETE_STATUS_POINTS = 10
    ANOMALY_POINTS = 20

    def __init__(self):
        self.db = FalkorDB(host="localhost", port=6379)
        self.graph = self.db.select_graph("traceguard")

    # --------------------------------------------------
    # 1. Retrieve transactions
    # --------------------------------------------------

    def get_transactions(self):
        query = """
        MATCH (t:Transaction)
        RETURN
            t.id AS transaction_id,
            t.account_id AS account_id,
            t.amount AS amount,
            t.status AS status,
            t.timestamp AS timestamp
        ORDER BY t.id
        """

        result = self.graph.query(query)

        transactions = []

        for row in result.result_set:
            transactions.append({
                "transaction_id": row[0],
                "account_id": row[1],
                "amount": row[2],
                "status": row[3],
                "timestamp": row[4],
            })

        return transactions

    # --------------------------------------------------
    # 2. Retrieve graph data
    # --------------------------------------------------

    def get_graph_data(self):
        query = """
        MATCH (a:Account)-[:USES_DEVICE]->(d:Device)
        RETURN
            a.id AS account_id,
            d.id AS device_id
        ORDER BY a.id, d.id
        """

        result = self.graph.query(query)

        account_device_links = [
            {
                "account_id": row[0],
                "device_id": row[1],
            }
            for row in result.result_set
        ]

        return {
            "account_device_links": account_device_links,
            "transactions": self.get_transactions(),
        }

    # --------------------------------------------------
    # 3. Find shared devices
    # --------------------------------------------------

    def get_shared_devices(self):
        query = """
        MATCH (a1:Account)-[:USES_DEVICE]->(d:Device)
              <-[:USES_DEVICE]-(a2:Account)
        WHERE a1.id < a2.id
        RETURN
            a1.id AS account_1,
            a2.id AS account_2,
            d.id AS device_id
        ORDER BY a1.id, a2.id, d.id
        """

        result = self.graph.query(query)

        return [
            {
                "account_1": row[0],
                "account_2": row[1],
                "device_id": row[2],
            }
            for row in result.result_set
        ]

    # --------------------------------------------------
    # 4. Validate transaction amount
    # --------------------------------------------------

    @staticmethod
    def _valid_amount(transaction):
        """
        Return a valid, finite, non-negative amount.
        Return None if the amount is invalid.
        """

        if not isinstance(transaction, dict):
            return None

        try:
            amount = float(transaction.get("amount"))
        except (TypeError, ValueError):
            return None

        if not math.isfinite(amount) or amount < 0:
            return None

        return amount

    # --------------------------------------------------
    # 5. Calculate IQR anomaly bounds
    # --------------------------------------------------

    @staticmethod
    def _calculate_iqr_bounds(amounts):
        """
        Calculate statistical bounds using the
        Interquartile Range (IQR) method.

        At least four valid amounts are required.
        """

        values = sorted(amounts)

        if len(values) < 4:
            return None

        def percentile(sorted_values, fraction):
            position = (len(sorted_values) - 1) * fraction

            lower = int(position)
            upper = min(
                lower + 1,
                len(sorted_values) - 1,
            )

            weight = position - lower

            return (
                sorted_values[lower] * (1 - weight)
                + sorted_values[upper] * weight
            )

        q1 = percentile(values, 0.25)
        q3 = percentile(values, 0.75)

        iqr = q3 - q1

        lower_bound = max(
            0.0,
            q1 - 1.5 * iqr,
        )

        upper_bound = q3 + 1.5 * iqr

        return {
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "q1": q1,
            "q3": q3,
            "iqr": iqr,
        }

    # --------------------------------------------------
    # 6. Detect unusual transaction amounts
    # --------------------------------------------------

    def detect_amount_anomalies(self, transactions=None):
        """
        Detect amounts outside IQR bounds.

        Returns a dictionary keyed by transaction ID.
        Insufficient data produces no anomaly flags.
        """

        if transactions is None:
            transactions = self.get_transactions()

        valid_amounts = [
            self._valid_amount(transaction)
            for transaction in transactions
        ]

        usable_amounts = [
            amount
            for amount in valid_amounts
            if amount is not None
        ]

        bounds = self._calculate_iqr_bounds(
            usable_amounts
        )

        anomalies = {}

        if bounds is None:
            return anomalies

        lower = bounds["lower_bound"]
        upper = bounds["upper_bound"]

        for transaction, amount in zip(
            transactions,
            valid_amounts,
        ):
            transaction_id = transaction.get(
                "transaction_id"
            )

            if transaction_id is None or amount is None:
                continue

            if amount < lower or amount > upper:
                anomalies[str(transaction_id)] = {
                    "is_anomaly": True,
                    "amount": amount,
                    "lower_bound": round(lower, 2),
                    "upper_bound": round(upper, 2),
                    "method": "IQR",
                    "explanation": (
                        f"Amount {amount:g} is outside the "
                        f"observed IQR bounds "
                        f"({lower:.2f} to {upper:.2f})."
                    ),
                }

        return anomalies

    # --------------------------------------------------
    # 7. Calculate explainable risk score
    # --------------------------------------------------

    def calculate_risk(
        self,
        transaction,
        shared_device=False,
        amount_anomaly=None,
    ):
        """
        Calculate a transparent, rule-based risk score.

        The score is an investigation-priority indicator,
        not a validated probability of fraud.
        """

        if not isinstance(transaction, dict):
            raise ValueError(
                "transaction must be a dictionary"
            )

        score = 0
        reasons = []
        evidence_limitations = []

        amount = self._valid_amount(transaction)

        status = str(
            transaction.get("status") or ""
        ).strip().lower()

        # Indicator 1: High transaction amount
        if amount is None:
            reasons.append(
                "Transaction amount is missing or invalid"
            )

            evidence_limitations.append(
                "A valid amount is required for reliable "
                "amount-based scoring."
            )

        elif amount >= self.HIGH_AMOUNT_THRESHOLD:
            score += self.HIGH_AMOUNT_POINTS

            reasons.append(
                f"High transaction amount: {amount:g}"
            )

        # Indicator 2: Shared-device relationship
        if shared_device:
            score += self.SHARED_DEVICE_POINTS

            reasons.append(
                "Account is associated with a device "
                "shared by multiple accounts"
            )

            evidence_limitations.append(
                "A shared device does not prove that the "
                "transaction was fraudulent or that the "
                "device was used for this transaction."
            )

        # Indicator 3: Transaction status
        if status != "completed":
            score += self.INCOMPLETE_STATUS_POINTS

            reasons.append(
                f"Transaction status is "
                f"'{status or 'unknown'}', not 'completed'"
            )

        # Indicator 4: Statistical amount anomaly
        if amount_anomaly:
            score += self.ANOMALY_POINTS

            explanation = amount_anomaly.get(
                "explanation",
                "Unusual transaction amount detected",
            )

            reasons.append(explanation)

            evidence_limitations.append(
                "A statistical outlier is unusual relative "
                "to the available dataset but is not proof "
                "of fraud."
            )

        # Keep score between 0 and 100
        score = min(max(score, 0), 100)

        # Classify risk
        if score >= self.HIGH_RISK_THRESHOLD:
            level = "HIGH"

            action = (
                "Prioritize manual investigation"
            )

        elif score >= self.MEDIUM_RISK_THRESHOLD:
            level = "MEDIUM"

            action = (
                "Review transaction details"
            )

        else:
            level = "LOW"

            action = (
                "No configured alert triggered; "
                "continue routine monitoring"
            )

        if not reasons:
            reasons.append(
                "No configured risk indicators were triggered"
            )

        # Summarize the available evidence
        evidence_summary = (
            f"{len(reasons)} indicator(s) recorded; "
            f"risk score {score}/100; "
            f"classification {level}."
        )

        if not evidence_limitations:
            evidence_limitations.append(
                "This score uses configured rules and "
                "available transaction data. It is not a "
                "validated fraud probability."
            )

        return {
            "transaction_id": transaction.get(
                "transaction_id"
            ),
            "risk_score": score,
            "risk_level": level,
            "reasons": reasons,
            "amount_anomaly": bool(amount_anomaly),
            "evidence_summary": evidence_summary,
            "evidence_limitations": evidence_limitations,
            "recommended_action": action,
        }

    # --------------------------------------------------
    # 8. Investigate all transactions
    # --------------------------------------------------

    def investigate(self):
        """
        Investigate all available transactions.

        Uses:
        - Rule-based risk scoring.
        - Shared-device relationships.
        - Statistical amount anomalies.
        - Explainable investigation recommendations.
        """

        transactions = self.get_transactions()

        shared_devices = self.get_shared_devices()

        anomalies = self.detect_amount_anomalies(
            transactions
        )

        # Collect accounts involved in shared-device links
        shared_accounts = set()

        for relationship in shared_devices:
            account_1 = relationship.get("account_1")
            account_2 = relationship.get("account_2")

            if account_1 is not None:
                shared_accounts.add(str(account_1))

            if account_2 is not None:
                shared_accounts.add(str(account_2))

        investigations = []

        for transaction in transactions:
            account_id = transaction.get("account_id")

            transaction_id = transaction.get(
                "transaction_id"
            )

            # This is account-level evidence, not proof
            # that this transaction used the shared device.
            shared_device = (
                account_id is not None
                and str(account_id) in shared_accounts
            )

            anomaly = (
                anomalies.get(str(transaction_id))
                if transaction_id is not None
                else None
            )

            report = self.calculate_risk(
                transaction=transaction,
                shared_device=shared_device,
                amount_anomaly=anomaly,
            )

            # Preserve the fields used by the dashboard
            report.update({
                "account_id": account_id,
                "amount": transaction.get("amount"),
                "status": transaction.get("status"),
                "timestamp": transaction.get("timestamp"),
            })

            investigations.append(report)

        return investigations