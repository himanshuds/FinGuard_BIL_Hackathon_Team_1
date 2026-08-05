"""
predictor_agent.py  (STRETCH GOAL)
----------------------------------
Wraps the trained asset-value model as an agent: given a loan's details, it
returns a predicted "suitable" asset value. Two uses, as the brief suggests:
  - standalone check: does the pledged asset look reasonable vs the prediction?
  - an extra signal for the rule 3 suggestion agent.

IMPORTANT BOUNDARY (consistent with the rest of the system):
  This is a PREDICTION (probabilistic), never a compliance VERDICT. It does not
  decide pass/fail -- OPA still owns that. The predictor only estimates what an
  asset value would typically be, as advisory context for a human reviewer.

RUN:  python predictor_agent.py     (after train_predictor.py has saved the model)
"""

import numpy as np
import pandas as pd
import joblib

MODEL_PATH = "asset_predictor.joblib"


class AssetPredictor:
    def __init__(self, model_path: str = MODEL_PATH):
        self._model = joblib.load(model_path)

    def predict(self, loan: dict) -> float:
        """
        loan needs: company_name, hq_country, loan_value, loan_currency,
                    and either asset_type or asset_description.
        Returns the predicted asset value in the loan's currency.
        """
        asset_type = loan.get("asset_type")
        if asset_type is None and loan.get("asset_description"):
            asset_type = loan["asset_description"].split()[-1]

        row = pd.DataFrame([{
            "loan_value": float(loan["loan_value"]),
            "loan_currency": loan["loan_currency"],
            "hq_country": loan["hq_country"],
            "asset_type": asset_type,
            "company_name": loan["company_name"],
        }])
        pred_log = self._model.predict(row)[0]
        return float(np.expm1(pred_log))   # invert the log target

    def assess(self, loan: dict) -> dict:
        """
        Standalone check: compare the ACTUAL pledged asset value against the
        prediction. Returns advisory context, not a verdict.
        """
        predicted = self.predict(loan)
        actual = float(loan["asset_value"])
        ratio = actual / predicted if predicted else None
        return {
            "predicted_asset_value": round(predicted),
            "actual_asset_value": actual,
            "ratio_actual_to_predicted": round(ratio, 2) if ratio else None,
            "note": "Advisory only. Compliance verdicts come from OPA, not this model.",
        }


if __name__ == "__main__":
    agent = AssetPredictor()

    loan = {
        "company_name": "Yarrow Auto Parts",
        "hq_country": "Germany",
        "loan_value": "1000000",
        "loan_currency": "EUR",
        "asset_description": "Stuttgart Freight Hub",
        "asset_value": "400000",
    }
    import json
    print("predicted:", round(agent.predict(loan)))
    print(json.dumps(agent.assess(loan), indent=2))
