import os
import glob
import json

type SchemaDict = dict[str, str]


def get_schemas_dict(path: str) -> dict[str, SchemaDict]:
    schemas_dict: dict[str, SchemaDict] = {}
    for json_file in glob.glob(os.path.join(path, "*.json")):
        filename = os.path.basename(json_file)
        with open(os.path.join(path, json_file), "r") as file:
            file_content = json.load(file)
            schemas_dict[os.path.splitext(filename)[0]] = file_content
    return schemas_dict
