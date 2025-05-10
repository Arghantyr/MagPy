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

            self.set_granularities()
            self.load_apimethods_mapping()
        except Exception as e:
            logging.warning(f"Could not initiate WAClient")
            raise Exception(f"{e}")
    
    # Input verification decorators
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

    def set_granularities(self):
        try:
            self.track_gran={
                    'world': 1,
                    'categories': 1,
                    'articles': 1
            }
            logging.info(f"Tracking granularities set:\n{json.dumps(self.track_gran, indent=2)}")

            self.beacon_gran={
                    'world': 0,
                    'categories': 0,
                    'articles': -1
            }
            logging.info(f"Beacon granularities set:\n{json.dumps(self.beacon_gran, indent=2)}")
            assert all([self.beacon_gran[prop] <= self.track_gran[prop] for prop in self.track_gran.keys()]) == True
        except AssertionError:
            raise Exception("Invalid granularity settings. Beacon must be <= than Track.")
        except Exception as e:
            logging.warning(f"Could not set granularities: {e}")
            raise Exception(f"{e}")

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
    
    def load_apimethods_mapping(self):
        try:
            self.apimethods_mapping={
                    'world': self.get_world,
                    'categories': self.get_category,
                    'articles': self.get_article
            }
            logging.info(f"API methods mapping loaded")
        except Exception as e:
            logging.warning(f"Could not load API methods mapping: {e}")
            raise Exception(f"{e}")

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
    
    @wau.endpoint_exceptions_wrapper
    def get_user_worlds_mapping(self, uuid: str = ''):
        user_uuid = self.get_auth_user_id()['id']
        worlds = [world['id'] for world in self.get_user_worlds(user_uuid)]
        if uuid:
            worlds = [uuid] if uuid in worlds else []
        logging.info(f"Fetched worlds mapping for user {user_uuid}: {', '.join(worlds)}")
        return {user_uuid: worlds}
    
    @wau.endpoint_exceptions_wrapper
    def get_mapping(self, uuid: str, _type: str, *args, **kwargs):
        if _type not in ['world', 'categories', 'articles']:
            raise ValueError(f"Invalid type '{_type}'. Supported types are: world, categories, articles")
        
        mapping_methods = {
            'world': lambda: self.get_user_worlds_mapping(uuid, *args, **kwargs),
            'categories': lambda: self.get_world_categories_mapping(uuid, *args, **kwargs),
            'articles': lambda: self.get_category_articles_mapping(uuid, *args, **kwargs)
        }
        logging.info(f"Fetching mapping for type '{_type}' with UUID: {uuid}")
        return mapping_methods[_type]()
