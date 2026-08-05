from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from typing import Annotated
from dependencies import get_exchange_rate_service, get_opa_rule_service
from services.opa_rule_service import OpaRuleService
from services.exchange_rate_service import ExchangeRateService
from models import LoanData, RuleResult
from routers.rules import router as rules_router
from utils.logging import setup_logging
from config import opa_server_url

setup_logging()

import logging
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):

    
    logger.info("Starting OPA Rule Service")

    er_service = ExchangeRateService(
        ttl_seconds=3600,
        cache_size=1000,
        max_retries=3,
    )
    
    opa_rule_service = OpaRuleService(opa_url = opa_server_url)

    app.state.exchange_rate_service = er_service
    app.state.opa_rule_service = opa_rule_service

    yield

    er_service.close()
    logger.info("Shutting down OPA Rule Service")


app = FastAPI(lifespan=lifespan)
app.include_router(rules_router)


@app.get("/rate")
def get_rate(
    source: str,
    target: str,
    service: Annotated[
        ExchangeRateService,
        Depends(get_exchange_rate_service)
    ],
):
    # One unit of source is how many units of target currency
    return service.get_rate(source, target)
