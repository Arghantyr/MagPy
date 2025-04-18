import Utils
from APIUtils import WorldAnvilUtils as wau #endpoint_exceptions_wrapper


from pywaclient.api import BoromirApiClient
import logging
import json



SCRIPT_NAME='gitworker.py'
MAGPY_REPO_URL='https://github.com/Arghantyr/MagPy'
SCRIPT_VERSION='0.1'



class WAClient():
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
            logiing.warning(f"Could not initiate WAClient")
            raise Exception(f"{e}")

    @wau.endpoint_exceptions_wrapper
    def get_auth_user_id(self):
        result = self.client.user.identity()
        logging.info(f"Fetching user identity object...")
        return result

    @wau.endpoint_exceptions_wrapper
    def get_user_worlds(self, user_id:str=''):
        logging.info(f"Fetching worlds owned by user {user_id}")
        return self.client.user.worlds(user_id)

    @wau.endpoint_exceptions_wrapper
    def get_world(self, world_uuid:str='', granularity:int=-1):
        logging.info(f"World object fetched. UUID: {world_uuid}, GRANULARITY: {granularity}")
        return self.client.world.get(world_uuid, granularity)

    @wau.endpoint_exceptions_wrapper
    def get_category(self, category_uuid:str='', granularity:int=-1):
        logging.info(f"Category object fetched. UUID: {category_uuid}, GRANULARITY: {granularity}")
        return self.client.category.get(category_uuid, granularity)

    @wau.endpoint_exceptions_wrapper
    def get_article(self, article_uuid:str='', granularity:int=-1):
        logging.info(f"Article object fetched. UUID: {article_uuid}, GRANULARITY: {granularity}")
        return self.client.article.get(article_uuid, granularity)

    @wau.endpoint_exceptions_wrapper
    def get_world_categories_mapping(self, world_uuid:str=''):
        categories = [category['id'] for category in self.client.world.categories(world_uuid)]
        logging.info(f"Categories fetched for world {world_uuid}: {', '.join(categories)}")
        return {world_uuid: categories}

    @wau.endpoint_exceptions_wrapper
    def get_category_articles_mapping(self, world_uuid:str='', category_uuids:list=[]):
        category_uuids.append('-1') #Account for uncategorized articles
        articles_mapping={cat_uuid: [art['id'] for art in self.client.world.articles(world_uuid, cat_uuid)
                                    ] for cat_uuid in category_uuids}
        logging.info(f"Fetched category-article mapping for world {world_uuid}:\n{json.dumps(articles_mapping, indent=2)}")
        return articles_mapping


