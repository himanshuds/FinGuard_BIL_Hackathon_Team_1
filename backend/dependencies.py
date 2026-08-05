from fastapi import Request

from services.opa_rule_service import OpaRuleService
from services.exchange_rate_service import ExchangeRateService


def get_exchange_rate_service(
    request: Request,
) -> ExchangeRateService:
    return request.app.state.exchange_rate_service


def get_opa_rule_service(
    request: Request,
) -> OpaRuleService:
    return request.app.state.opa_rule_service
