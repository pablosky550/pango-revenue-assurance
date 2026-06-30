import re

BEGINNING_BALANCE_PATTERN = re.compile(
    r"Beginning Balance\s+\$?([\d,]+\.\d{2})"
)

TRANSACTION_DATE_PATTERN = re.compile(
    r"^\d{2}/\d{2}/\d{4}"
)

TRANSACTION_PATTERN = re.compile(
    r"""
    ^
    (?P<date>\d{2}/\d{2}/\d{4})
    \s+
    (?P<description>.+?)
    \s+
    \$?(?P<amount>[\d,]+\.\d{2})
    \s+
    \$?(?P<balance>[\d,]+\.\d{2})
    $
    """,
    re.VERBOSE,
)