import json
import os
from typing import List, Dict
import boto3

def save_conversations(records: List[Dict], table_name: str = None, local_path: str = None):
    """
    Save conversation records to DynamoDB if table_name is provided, else to local JSON file.
    """
    if table_name:
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(table_name)
        for record in records:
            table.put_item(Item=record)
    elif local_path:
        with open(local_path, "w") as f:
            json.dump(records, f, indent=2)
    else:
        raise ValueError("Must provide table_name or local_path.")

def load_conversations(table_name: str = None, local_path: str = None) -> List[Dict]:
    """
    Load conversation records from DynamoDB if table_name is provided, else from local JSON file.
    """
    if table_name:
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(table_name)
        response = table.scan()
        return response.get("Items", [])
    elif local_path and os.path.exists(local_path):
        with open(local_path) as f:
            return json.load(f)
    else:
        raise ValueError("Must provide table_name or local_path.") 