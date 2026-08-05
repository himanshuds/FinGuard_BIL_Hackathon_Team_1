import requests

class OpaRuleService:
    def __init__(self, opa_url: str = "http://localhost:8181"):
        self.opa_url = opa_url.rstrip("/")
        self._session = requests.Session()
        self.rules_dict = {
             "rule1":"loan/loan_above_threshold", 
             "rule2":"loan/valid_currency", 
             "rule3": "loan/loan_asset_value"
            }

    def evaluate_rule(self, rule_path:str, input_data: dict):
        """Evaluate an OPA rule with given input data."""
        url = f"{self.opa_url}/v1/data/{rule_path}"
        #print(f"***input data***{input_data}")
        response = self._session.post(url, json={"input": input_data})
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"OPA evaluation failed: {response.status_code} - {response.text}")
