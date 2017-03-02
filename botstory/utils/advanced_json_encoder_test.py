from botstory.utils import advanced_json_encoder
from bson import ObjectId
import json


def test_encode_objectid():
    assert advanced_json_encoder.AdvancedJSONEncoder().encode({
        'id': ObjectId('51948e86c25f4b1d1c0d303c'),
        'message': 'hello world!',
    }) == json.dumps({
        'id': '51948e86c25f4b1d1c0d303c',
        'message': 'hello world!',
    })
