import json
import os

def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, filepath):
    with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, sort_keys=True, separators=(',', ': '), indent=2)
