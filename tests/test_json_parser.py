import os
from src.sboxmgr.subscription.parsers.json_parser import JSONParser

def test_json_parser():
    example_path = os.path.join(os.path.dirname(__file__), '../src/sboxmgr/examples/example_json.json')
    with open(example_path, 'rb') as f:
        raw = f.read()
    parser = JSONParser()
    servers = parser.parse(raw)
    assert isinstance(servers, list) 