from typing import Annotated

from fastapi import APIRouter, Depends

from dependencies import get_opa_rule_service, get_exchange_rate_service
from models import LoanData, RuleResult, Currency, CurrencyValidationRequest, LoanAssetValueRequest
from services.opa_rule_service import OpaRuleService
from services.exchange_rate_service import ExchangeRateService
import logging
from utils.helper_functions import get_data_by_company_name, load_json_as_dict
import json

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/rules",
    tags=["rules"],
)


@router.post(
        "/loan-above-threshold",
        response_model=RuleResult
)
def evaluate_loan_above_threshold(
    loan_data: LoanData,
    opa_rule_service: Annotated[
        OpaRuleService,
        Depends(get_opa_rule_service),
    ],
    rate_service: Annotated[
            ExchangeRateService,
            Depends(get_exchange_rate_service)
        ],
):
    
    logger.info("Evaluating loan_above_threshold")

    if loan_data.loan_currency == Currency.EUR:
        payload = loan_data.model_dump(mode='json')
    else:
        #convert loan_value to EUR
        logger.debug(f"Converting {loan_data.loan_value} {loan_data.loan_currency.value} to EUR")
        rate_dict = rate_service.get_rate(loan_data.loan_currency, Currency.EUR)
        loan_value_eur = loan_data.loan_value*rate_dict.rate
        logger.debug(f"{loan_data.loan_value} {loan_data.loan_currency.value} = {loan_value_eur} EUR")
        payload = LoanData(
            loan_currency=Currency.EUR,
            loan_value=loan_value_eur
        ).model_dump(mode='json')
    
            
    logger.debug(f"***payload: {payload}***")

    rule_status = opa_rule_service.evaluate_rule(
        "loan/loan_above_threshold",
        payload,
    )
    message = "passed" if rule_status['result'] else "Loan value should be at least 25,000 EUR"
    return RuleResult(
        rule_name="loan/loan_above_threshold",
        passed=rule_status['result'],
        message=message)




@router.post("/loan-currency-check")
def loan_currency_check(
    request: CurrencyValidationRequest,
    opa_rule_service: Annotated[
        OpaRuleService,
        Depends(get_opa_rule_service),
    ],
):  
    rule_name="loan/valid_currency"
    #logger.debug(f"rule name for OPA: {rule_name}")
    company_data = get_data_by_company_name(request.company_name)
    logger.debug(f"Company data for {request.company_name}: {company_data}")
    country_to_currency = load_json_as_dict('./lookups/country_currency.json').get('country_to_currency', {})
    #logger.debug(f"Country to currency mapping: {country_to_currency}")
    rule_status = {"result": False}
    if company_data is None:
        message = "Please check company name"    
    else:
        country = company_data.get("hq_country") #get headquarter country
        currency = request.loan_currency.value #get the loan currency from request body
        logger.debug(f"Company name: {request.company_name}, HQ Country: {country}, Loan Currency: {currency}")

        payload = {
                "country": country,
                "currency": currency,
        }
        logger.debug(f"rule name for OPA: {rule_name}")
        rule_status = opa_rule_service.evaluate_rule(
                rule_name,
                payload
        )
        message = "passed" if rule_status['result'] else f"Convert loan value to {country_to_currency.get(country)}"

    return {
        "rule_name": rule_name,
        "passed": rule_status["result"],
        "message": message
    }



@router.post("/loan_asset_value")
def loan_asset_value(
    request: LoanAssetValueRequest,
    opa_rule_service: Annotated[
        OpaRuleService,
        Depends(get_opa_rule_service),
    ],
    rate_service: Annotated[
                ExchangeRateService,
                Depends(get_exchange_rate_service)
            ],
):  
    rule_name="loan/loan_asset_value"
    payload = {"loan_value":request.loan_value, "asset_value": request.asset_value}
    rule_status = opa_rule_service.evaluate_rule(
                    rule_name,
                    payload
            )
    message = "passed" if rule_status['result'] else f"Asset value is less than desired"
    remediation = ""
    if not rule_status['result']:
        remediation = f"{get_pledgeable_asset_for_loan(request.company_name, request.loan_value, request.loan_currency.value, opa_rule_service, rate_service)}"
    return {
            "rule_name": rule_name,
            "passed": rule_status["result"],
            "message": message,
            "remediation": remediation
        }



def get_pledgeable_asset_for_loan(company_name:str, loan_value:int, loan_currency:str, opa_rule_service, rate_service):
    # Get company data
    logger.debug(f"Getting pledgeable asset for company: {company_name}")
    company_data = get_data_by_company_name(company_name)
    result = f"No asset found for desired value"
    if company_data is None:
        logger.debug(f"Company data not found for {company_name}")
        result = f"No assets found for {company_name}"
        #return result
    
    # Get pledgeable assets data for this company
    pledgeable_assets = company_data.get("pledgeable_assets", [])

    # Sort pledgeable_assets list by value in ascending order
    pledgeable_assets.sort(key=lambda x: x['value'])

    for asset_data in pledgeable_assets:
        asset_value = asset_data['value']
        # Check if asset value is greater than loan value
        if asset_data['currency'] != loan_currency:
            #convert asset value to loan currency
            #rate_service = get_exchange_rate_service()
            rate_dict = rate_service.get_rate(asset_data['currency'], loan_currency)
            asset_value = asset_data['value']*rate_dict.rate
        #opa_rule_service = get_opa_rule_service()
        payload = {"loan_value":loan_value, "asset_value": asset_value}
        rule_status = opa_rule_service.evaluate_rule(
                                "loan/loan_asset_value",
                                payload
                        )
        if rule_status['result']:
            result = json.dumps(asset_data)
            break
    return result
    
