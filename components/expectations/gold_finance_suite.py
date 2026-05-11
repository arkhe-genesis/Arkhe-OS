# expectations/gold_finance_suite.py
import great_expectations as gx
from great_expectations.core.expectation_suite import ExpectationSuite
from great_expectations.expectations import (
    ExpectColumnValuesToBeUnique,
    ExpectColumnValuesToNotBeNull,
    ExpectColumnValuesToBeBetween,
    ExpectColumnValuesToMatchRegex,
    ExpectColumnValuesToBeInSet,
    ExpectTableRowCountToBeBetween
)

def create_gold_finance_suite():
    suite = ExpectationSuite(
        expectation_suite_name="gold_finance_transactions_suite",
        meta={
            "version": "2.1.0",
            "coherence_target": 0.95,
            "domain": "finance",
            "layer": "gold"
        }
    )

    # 1. Unicidade (Critical)
    suite.add_expectation(
        ExpectColumnValuesToBeUnique(
            column="transaction_id",
            meta={"priority": "P0", "coherence_weight": 0.3}
        )
    )

    # 2. Integridade Referencial
    suite.add_expectation(
        ExpectColumnValuesToNotBeNull(
            column="account_id",
            meta={"priority": "P0"}
        )
    )

    # 3. Validade de Negócio
    suite.add_expectation(
        ExpectColumnValuesToBeBetween(
            column="amount_usd",
            min_value=0,
            max_value=10000000,
            meta={"business_rule": "anti_fraud_limit"}
        )
    )

    # 4. Formato Padronizado
    suite.add_expectation(
        ExpectColumnValuesToMatchRegex(
            column="account_id",
            regex=r"^ACC-\d{8}$",
            meta={"standardization": "account_id_format"}
        )
    )

    # 5. Enumeração de Status
    suite.add_expectation(
        ExpectColumnValuesToBeInSet(
            column="status",
            value_set=["PENDING", "SETTLED", "FAILED", "REVERSED"],
            meta={"state_machine": "transaction_lifecycle"}
        )
    )

    return suite

if __name__ == "__main__":
    suite = create_gold_finance_suite()
    print(f"Created expectation suite: {suite.expectation_suite_name}")
