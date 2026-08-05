from enum import Enum

from pydantic import BaseModel, Field

class Currency(str, Enum):
    EUR = "EUR"
    USD = "USD"
    JPY = "JPY"
    SEK = "SEK"
    GBP = "GBP"
    PLN = "PLN"
    CHF = "CHF"
    CAD = "CAD"


class LoanData(BaseModel):

    loan_currency: Currency = Field(
        description="Loan currency"
    )

    loan_value: float = Field(
        gt=0,
        description="Loan amount"
    )

class CurrencyValidationRequest(BaseModel):
    company_name: str
    loan_currency: Currency = Field(
            description="Loan currency"
        )

class LoanAssetValueRequest(BaseModel):
    company_name: str
    loan_value: float = Field(
        gt=0,
        description="Loan amount"
    )
    asset_value: float = Field(
        gt=0,
        description="Asset amount"
    )
    loan_currency: Currency = Field(
                description="Loan currency"
            )

class RuleResult(BaseModel):
    rule_name: str
    passed: bool
    message: str | None = None
    remediation: str | None = None
