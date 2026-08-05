# Test EUR loan, OPA passes
def test_loan_above_threshold_eur_pass(
    client,
    mock_opa_service,
):
    mock_opa_service.evaluate_rule.return_value = {
        "result": True
    }

    response = client.post(
        "/rules/loan-above-threshold",
        json={
            "loan_currency": "EUR",
            "loan_value": 30000,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["passed"] is True
    assert body["message"] == "passed"
    assert body["remediation"] == ""

    mock_opa_service.evaluate_rule.assert_called_once_with(
        "loan/loan_above_threshold",
        {
            "loan_currency": "EUR",
            "loan_value": 30000,
        },
    )

# EUR loan, OPA fails
def test_loan_above_threshold_eur_fail(
    client,
    mock_opa_service,
):

    mock_opa_service.evaluate_rule.return_value = {
        "result": False
    }

    response = client.post(
        "/rules/loan-above-threshold",
        json={
            "loan_currency": "EUR",
            "loan_value": 1000,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["passed"] is False

    assert (
        body["message"]
        == "Loan value should be at least 25,000 EUR"
    )

    assert (
        body["remediation"]
        == "Remove this loan from report"
    )

