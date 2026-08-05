package loan

# rule 1
minimum_loan_value := 25000 #loan must exceed threshold
default loan_above_threshold := false

loan_above_threshold if {
    input.loan_value >= minimum_loan_value
    input.loan_currency == "EUR"
}


# rule 2
default valid_currency := false

valid_currency if {
    expected_currency := data.country_to_currency[input.country]
    lower(input.currency) == lower(expected_currency)
}


# rule 3
default loan_asset_value := false

loan_asset_value if {
    minimum_asset_value := 0.5 * input.loan_value
    input.asset_value >= minimum_asset_value
}

