from hashlib import sha1



def get_hash(content:str)->str:
    try:
        return sha1(content.encode('utf-8')).hexdigest()
    except Exception as e:
        raise Exception(f"{e}")

