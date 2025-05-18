import json
import os
from pathlib import Path

CONFIG_FILE = "swot_config.json"

def save_config(config):
    """Save configuration to file"""
    # with open(CONFIG_FILE, 'w') as f:
    #     json.dump(config, f)

def load_config():
    """Load configuration from file"""
    # if os.path.exists(CONFIG_FILE):
    #     with open(CONFIG_FILE, 'r') as f:
    #         return json.load(f)
    return {
        'api_key': '',
        'endpoint': '',
        'deployment_name': '',
        'api_version': '2025-01-01-preview'
    } 