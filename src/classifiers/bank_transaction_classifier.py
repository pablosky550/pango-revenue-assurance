from dataclasses import dataclass


@dataclass(frozen=True)
class ClassificationRule:
    """
    Bank transaction classification rule.
    """

    keyword: str
    transaction_type: str


class BankTransactionClassifier:
    """
    Classify raw bank transaction descriptions.
    """

    RULES = [

        ClassificationRule(
            "PAYPAL TRANSFER",
            "PAYPAL_SETTLEMENT",
        ),

        ClassificationRule(
            "BRAINTREE FUNDING",
            "BRAINTREE_SETTLEMENT",
        ),

        ClassificationRule(
            "CHECK #",
            "CHECK",
        ),

        ClassificationRule(
            "PRINCIPAL",
            "LOAN_PAYMENT",
        ),

        ClassificationRule(
            "Mobile Smart Cit",
            "CITY_PAYMENT",
        ),

    ]

    def classify(self, line: str) -> str:

        line = line.upper()

        for rule in self.RULES:

            if rule.keyword.upper() in line:
                return rule.transaction_type

        return "UNKNOWN"
    
if __name__ == "__main__":

    classifier = BankTransactionClassifier()

    samples = [

        "03/02/2026 PAYPAL TRANSFER 1048615785827 $1,069.86 $47,169.27",

        "03/02/2026 BRAINTREE FUNDING 6KGFF4 $23,703.11 $73,270.56",

        "03/02/2026 CHECK # 1861 $6,123.50 $67,146.91",

        "03/10/2026 PRINCIPAL-CCAPNL PRIN FINAN 476945600200003 $1,393.07 $75,227.83",

        "03/03/2026 Mobile Smart Cit Cleveland 267089712 $1,459.98 $81,991.10",

    ]

    for sample in samples:

        print(classifier.classify(sample))