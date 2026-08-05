from pathlib import Path
import json
from config import json_files_dir

def load_json_as_dict(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data


def get_data_by_company_name(
    company_name: str,
    #json_files_dir: Path
) -> dict | None:
    """Load JSON file into a Python dict"""
    json_files = list(json_files_dir.glob('*.json'))
    # Find the JSON file corresponding to the company name
    for file_path in json_files:
        data = load_json_as_dict(file_path)
        if data.get('company_name') == company_name:
            return data
