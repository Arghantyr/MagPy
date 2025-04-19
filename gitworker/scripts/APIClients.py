import Utils
from APIUtils import WorldAnvilUtils as wau
from pywaclient.api import BoromirApiClient
import logging
import json
from functools import wraps
from string import hexdigits




SCRIPT_NAME='gitworker.py'
MAGPY_REPO_URL='https://github.com/Arghantyr/MagPy'
SCRIPT_VERSION='0.1'



class WAClient(object):
    def __init__(self, application_key: str, authentication_token: str):
        try:
            self.client=BoromirApiClient(
                    SCRIPT_NAME,
                    MAGPY_REPO_URL,
                    SCRIPT_VERSION,
                    application_key,
                    authentication_token
                    )
            logging.info(f"WAClient object initiated...")
        except Exception as e:
            logging.warning(f"Could not initiate WAClient")
            raise Exception(f"{e}")

    def verify_uuid(func):
        @wraps(func)
        def inner(self, uuid, *args, **kwargs):
            try:
                if uuid is None:
                    raise Exception(f"UUID field cannot be empty.")
                if not isinstance(uuid, str):
                    raise TypeError(f"Invalid type. UUID can only be of type 'string'")
                if len(uuid) != 36:
                    raise Exception(f"Invalid UUID length.")
                if set(uuid).difference(set(''.join(['-', hexdigits]))) != set():
                    raise Exception(f"Forbidden characters in UUID.")
                if [len(sub) for sub in uuid.split('-')] != [8,4,4,4,12]:
                    raise Exception(f"Invalid UUID structure.")

                return func(self, uuid, *args, **kwargs)
            except Exception as e:
                raise Exception(f"{e}")
        return inner
        
    def verify_granularity(func):
        @wraps(func)
        def inner(self, uuid, granularity, *args, **kwargs):
            try:
                if granularity is None:
                    raise Exception(f"Granularity field cannot be empty.")
                if not isinstance(granularity, int):
                    raise TypeError(f"Invalid type. Granularity can only be of type 'int'")
                if int(granularity) not in range(-1, 10, 1):
                    raise ValueError(f"Granularity value out of range.")

                return func(self, uuid, granularity, *args, **kwargs)
            except Exception as e:
                raise Exception(f"{e}")
        return inner

    @wau.endpoint_exceptions_wrapper
    def get_auth_user_id(self):
        result = self.client.user.identity()
        logging.info(f"Fetching user identity object...")
        return result

    @wau.endpoint_exceptions_wrapper
    @verify_uuid
    def get_user_worlds(self, uuid:str=''):
        logging.info(f"Fetching worlds owned by user {uuid}")
        return self.client.user.worlds(uuid)

    @wau.endpoint_exceptions_wrapper
    @verify_granularity
    @verify_uuid
    def get_world(self, uuid:str='', granularity:int=-1):
        logging.info(f"World object fetched. UUID: {uuid}, GRANULARITY: {granularity}")
        return self.client.world.get(uuid, granularity)

    @wau.endpoint_exceptions_wrapper
    @verify_granularity
    @verify_uuid
    def get_category(self, uuid:str='', granularity:int=-1):
        logging.info(f"Category object fetched. UUID: {uuid}, GRANULARITY: {granularity}")
        return self.client.category.get(uuid, granularity)

    @wau.endpoint_exceptions_wrapper
    @verify_granularity
    @verify_uuid
    def get_article(self, uuid:str='', granularity:int=-1):
        logging.info(f"Article object fetched. UUID: {uuid}, GRANULARITY: {granularity}")
        return self.client.article.get(uuid, granularity)

    @wau.endpoint_exceptions_wrapper
    @verify_uuid
    def get_world_categories_mapping(self, uuid:str=''):
        categories = [category['id'] for category in self.client.world.categories(uuid)]
        logging.info(f"Categories fetched for world {uuid}: {', '.join(categories)}")
        return {uuid: categories}

    @wau.endpoint_exceptions_wrapper
    @verify_uuid
    def get_category_articles_mapping(self, uuid:str='', category_uuids:list=[]):
        category_uuids.append('-1') #Account for uncategorized articles
        articles_mapping={cat_uuid: [art['id'] for art in self.client.world.articles(uuid, cat_uuid)
                                    ] for cat_uuid in category_uuids}
        logging.info(f"Fetched category-article mapping for world {uuid}:\n{json.dumps(articles_mapping, indent=2)}")
        return articles_mapping


