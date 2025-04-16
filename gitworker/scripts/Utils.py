from hashlib import sha1
import json


NULL_IDENTIFIER="00000000-0000-0000-0000-000000000000"


def get_hash(content:str)->str:
    try:
        return sha1(content.encode('utf-8')).hexdigest()
    except Exception as e:
        raise Exception(f"{e}")

def bind_values_to_map(identifier:str=NULL_IDENTIFIER, value:dict={})->dict:
    try:
        return { identifier: get_hash(json.dumps(value, ensure_ascii=False)) }
    except Exception as e:
        raise Exception(f"{e}")

