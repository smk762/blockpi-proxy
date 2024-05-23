import json
from logger import logger

def get_jsonfile_data(filename):
    try:
        with open(filename, 'r') as json_file:
            return json.load(json_file)
    except Exception as e:
        logger.warning(f"Failed to read {filename}: {e}")

def write_jsonfile_data(filename, data):
    try:
        with open(filename, 'w+') as json_file:
            json.dump(data, json_file, indent=2)
        logger.info(f"Updated {filename}!")
    except Exception as e:
        logger.warning(f"Failed to write {filename}: {e}")
