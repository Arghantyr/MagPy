import os
import json
import time
import yaml
from datetime import datetime
from  pywaclient.api import BoromirApiClient
from pywaclient.exceptions import (
        ConnectionException,
        UnexpectedStatusException,
        InternalServerException,
        UnauthorizedRequest,
        AccessForbidden,
        ResourceNotFound,
        UnprocessableDataProvided,
        FailedRequest
        )
import git
from hashlib import sha1
import logging
import sys


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)


NULL_UUID="00000000-0000-0000-0000-000000000000"
SCRIPT_NAME='gitworker.py'
MAGPY_REPO_URL='https://github.com/Arghantyr/MagPy'
VERSION='0.1'
SSH_ID_FILE='/home/gitworker/.ssh/id_rsa'
REPO_PATH='/home/gitworker/repo'
FILE_INDEX_PATH='/home/gitworker/repo/file_index'
QUIT_AT='2038-01-11 11:01'
SECRET_PATH='/run/secrets/secret_config'
PING_INTERVAL_S=60

class Secrets:
    def __init__(self):
        self.load_secret()
    def load_secret(self):
        try:
            with open(SECRET_PATH, mode='rt') as secret_file:
                secrets=yaml.load(secret_file, yaml.Loader)

            self.api_key=secrets['credentials']['api_key']
            self.api_token=secrets['credentials']['api_token']
            self.repo_ssh_url=secrets['remote_repo']['remote_repository_url']
            self.worlds_list=secrets['track']['worlds']
            
            logging.info("Secrets loaded.")
        except Exception as e:
            logging.warning("Unable to process 'secrets' file.")
            raise Exceptions(f"{e}")


class Gitworker:
    def __init__(self, secret_obj:Secrets=None):
        self.load_secret(secret_obj)
        self.load_repo()
        self.validate_repo_settings()
        self.initiate_commit_backend()

        logging.info("Gitworker object initiated.")
    def load_secret(self, secret_obj:Secrets=None):
        try:
            self.repo_ssh_url=secret_obj.repo_ssh_url
            logging.info("Gitworker: secrets loaded...")
        except Exception as e:
            logging.warning("Gitworker: unable to load secrets")
            raise Exceptions(f"{e}")
    def load_repo(self):
        try:
            self.remote_repo_name=self.repo_ssh_url.rstrip('.git').split('/')[-1]
            self.repo=git.Repo(f"{REPO_PATH}/{self.remote_repo_name}")
            logging.info("Gitworker: repository object set...")
        except Exception as e:
            logging.warning("Gitworker: unable to load repository")
            raise Exception(f"{e}")
    def validate_repo_settings(self):
        try:
            remote_repo_set=self.repo.remote('github-repo').exists()
            if remote_repo_set:
                self.remote=self.repo.remote('github-repo')
            self.repo.heads['main'].checkout()
            logging.info("Gitworker: remote repository validated...")
        except Exception as e:
            logging.warning("Gitworker: unable to validate remote repository")
            raise Exception(f"{e}")
    def initiate_commit_backend(self):
        try:
            self.commit_message=""
            self.index_list=['track_hash_reg', 'beacon_hash_reg', 'file_index']
            logging.info("Gitworker: commit message and index initiated...")
        except Exception as e:
            logging.warning("Gitworker: unable to initiate commit message and index")
            raise Exception(f"{e}")

    # Metadata and supporting functions
    def get_uuid_objhash(self, uuid:str=NULL_UUID, content:str="{}"):
        try:
            obj_hash=sha1(json.dumps(content, ensure_ascii=False).encode('utf-8')).hexdigest()
            logging.info(f"Calculated hash for object string. UUID: {uuid}, hash: {obj_hash}")
            return uuid, obj_hash
        except Exception as e:
            logging.warning(f"Unable to calculate hash. UUID: {uuid}.")
            raise Exception(f"{e}")

    # Index list section
    def update_index_list(self, element:str=''):
        try:
            if element != '':
                self.index_list.append(element)
                logging.info(f"Added element to git index: {element}")
            else:
                logging.warning(f"Unable to add element to git index: {element}")
                raise Exception(f"Invalid element value. Index update aborted.")
        except Exception as e:
            logging.warning("Unable to update list of git tracked indexes")
            raise Exception(f"{e}")
    def add_to_index(self):
        try:
            self.repo.index.add(self.index_list)
            logging.info(f"Update git index with the list of tracked objects: {self.index_list}")
        except Exception as e:
            logging.warning(f"Unable to update the git index.")
            raise Exception(f"{e}")

    # Commit section
    def update_commit_message(self, message:str=""):
        try:
            self.commit_message += ''.join([message, '\n'])
            logging.info(f"Updated the commit message")
        except Exception as e:
            logging.warning(f"Unable to update the commit message")
            raise Exception(f"{e}")
    def flush_commit_message(self):
        try:
            self.commit_message=""
            logging.info(f"Commit message reset.")
        except Exception as e:
            raise Exception(f"{e}")
    def post_commit(self, short_commit_message:str="Object update"):
        try:
            self.repo.index.commit(''.join([short_commit_message,
                                            '\n\n',
                                            self.commit_message])
                                   )
            logging.info(f"Commit posted: {short_commit_message} {self.commit_message[:20]}...")
            self.flush_commit_message()
        except Exception as e:
            logging.warning(f"Unable to post commit")
            raise Exception(f"{e}")

    # Stored object section
    def compare_object_hash(self, uuid:str=NULL_UUID, content:str="{}", reg_type:str='track')->bool:
        try:
            match reg_type:
                case 'track' | 'beacon':
                    hash_reg_filepath=f'{REPO_PATH}/{self.remote_repo_name}/{reg_type}_hash_reg'
                    with open(hash_reg_filepath, mode='r') as _hash_reg:
                        hash_reg=json.load(_hash_reg)
                    stored_hash=hash_reg.get(uuid)
                case 'file_index':
                    file_index_filepath=f"{REPO_PATH}/{self.remote_repo_name}/file_index"
                    with open(file_index_filepath, mode='r') as _file_index:
                        file_index=json.load(_file_index)
                        logging.info(f'Fetching file_index object: {file_index}')
                    _, stored_hash=self.get_uuid_objhash(uuid, json.dumps(file_index))
                    logging.info(f'Calculated hash ({stored_hash}) for stringified file index object: {json.dumps(file_index)}')
                case _:
                    raise Exception(f"Invalid registry type.")

            _, current_hash=self.get_uuid_objhash(uuid, content)

            result=None
            if stored_hash==current_hash:
                result=True
            else:
                result=False

            logging.info(f"Comparing {reg_type} hash for uuid {uuid}. Stored: {stored_hash}, current: {current_hash} with result: {result}")
            return result
        except Exception as e:
            logging.warning(f"Unable to compare hash values for uuid: {uuid}")
            raise Exception(f"{e}")
    def update_repo_object(self, uuid:str=NULL_UUID, new_content:str="{}"):
        try:
            with open(f'{REPO_PATH}/{self.remote_repo_name}/{uuid}', mode='w') as file:
                new_content_str=json.dumps(new_content, indent=2)
                
                file.write(new_content_str)
            logging.info(f"Object with uuid: {uuid} updated in the local repository.")
        except Exception as e:
            logging.warning(f"Unable to update local repo for uuid: {uuid}")
            raise Exception(f"{e}") 
    def update_hash_reg(self, uuid:str=NULL_UUID, new_content:str="{}", reg_type:str='track'):
        try:
            _, object_hash=self.get_uuid_objhash(uuid, new_content)
            match reg_type:
                case 'track' | 'beacon':
                    hash_reg_filepath=f'{REPO_PATH}/{self.remote_repo_name}/{reg_type}_hash_reg'
                case _:
                    raise Exception(f"Invalid registry type.")

            with open(hash_reg_filepath, mode='r') as _hash_reg:
                hash_reg=json.load(_hash_reg)

            with open(hash_reg_filepath, mode='w') as _hash_reg:
                hash_reg[uuid]=object_hash
                json.dump(hash_reg, _hash_reg)

            logging.info(f"{reg_type.capitalize()} hash registry updated for {uuid}: {object_hash}.")
        except Exception as e:
            logging.warning(f"Unable to modify {reg_type} hash registry.")
            raise Exception(f"{e}") 
    def get_file_index(self):
        try: 
            with open(f"{REPO_PATH}/{self.remote_repo_name}/file_index", mode='r') as file_index:
                stored_file_index=json.load(file_index)
            return stored_file_index

        except Exception as e:
            raise Exception(f"{e}")
    def update_file_index(self, uuid_type_map:dict[str, str]):
        try:
            stored_file_index=self.get_file_index()
            stored_file_index.update(uuid_type_map)
            with open(f"{REPO_PATH}/{self.remote_repo_name}/file_index", mode='w') as file_index:
                json.dump(stored_file_index, file_index)
            logging.info(f'File index updated and saved to file.')
        except Exception as e:
            raise Exception(f"{e}")
    def push_to_remote_repository(self):
        try:
            with self.repo.git.custom_environment(GIT_SSH_COMMAND=f'ssh -i {SSH_ID_FILE}'):
                self.remote.push()
            logging.info(f"Pushing commits to remote repository")
        except Exception as e:
            logging.warning(f"Unable to push to remote repository")
            raise Exception(f"{e}")


class WAClient:
    def __init__(self, api_key, api_token):
        try:
            self.client=BoromirApiClient(SCRIPT_NAME,
                                         MAGPY_REPO_URL,
                                         VERSION,
                                         api_key,
                                         api_token
                                         )
            logging.info(f"WAClient initiated...")
        except Exception as e:
            logiing.warning(f"Could not initiate WAClient")
            raise Exception(f"{e}")
    def get_auth_user_id(self):
        try:
            logging.info(f"Fetching User identity...")
            return self.client.user.identity()
        except ConnectionException as connection_exception:
            logging.warning(f"Unable to connect to WorldAnvil API. {connection_exception}")
            raise Exception(f"{connection_exception}")
        except InternalServerException as internal_server_exception:
            logging.warning(f"WorldAnvil server unable to process request. {internal_server_exception}")
            raise Exception(f"{internal_server_exception}")
        except UnauthorizedRequest as unauthorized_request:
            logging.warning(f"User unauthorized to process this request. {unauthorized_request}")
            raise Exception(f"{unauthorized_request}")
        except AccessForbidden as access_forbidden:
            logging.warning(f"Invalid permissions to view requested resource. {access_forbidden}")
            raise Exception(f"{access_forbidden}")
        except ResourceNotFound as resource_not_found:
            logging.warning(f"Requested resource not found. {resource_not_found}")
            raise Exception(f"{resource_not_found}")
        except UnprocessableDataProvided as unprocessable_data_provided:
            logging.error(f"Request could not be processed. {unprocessable_data_provided}")
            raise Exception(f"{unprocessable_data_provided}")
        except FailedRequest as failed_request:
            logging.error(f"Request failed. {failed_request}")
        except Exception as e:
            logging.warning(f"Could not fetch user identity")
            raise Exception(f"{e}")
    def get_user_worlds(self, user_id:str=''):
        try:
            logging.info(f"Fetching worlds owned by user {user_id}")
            return self.client.user.worlds(user_id)
        except ConnectionException as connection_exception:
            logging.warning(f"Unable to connect to WorldAnvil API. {connection_exception}")
            raise Exception(f"{connection_exception}")
        except InternalServerException as internal_server_exception:
            logging.warning(f"WorldAnvil server unable to process request. {internal_server_exception}")
            raise Exception(f"{internal_server_exception}")
        except UnauthorizedRequest as unauthorized_request:
            logging.warning(f"User unauthorized to process this request. {unauthorized_request}")
            raise Exception(f"{unauthorized_request}")
        except AccessForbidden as access_forbidden:
            logging.warning(f"Invalid permissions to view requested resource. {access_forbidden}")
            raise Exception(f"{access_forbidden}")
        except ResourceNotFound as resource_not_found:
            logging.warning(f"Requested resource not found. {resource_not_found}")
            raise Exception(f"{resource_not_found}")
        except UnprocessableDataProvided as unprocessable_data_provided:
            logging.error(f"Request could not be processed. {unprocessable_data_provided}")
            raise Exception(f"{unprocessable_data_provided}")
        except FailedRequest as failed_request:
            logging.error(f"Request failed. {failed_request}")
        except Exception as e:
            logging.warning(f"Could not fetch worlds for user {user_id}")
            raise Exception(f"{e}")
    def get_world(self, world_uuid:str='', granularity:int=-1):
        try:
            logging.info(f"World object fetched. UUID: {world_uuid}, GRANULARITY: {granularity}")
            return self.client.world.get(world_uuid, granularity)
        except ConnectionException as connection_exception:
            logging.warning(f"Unable to connect to WorldAnvil API. {connection_exception}")
            raise Exception(f"{connection_exception}")
        except InternalServerException as internal_server_exception:
            logging.warning(f"WorldAnvil server unable to process request. {internal_server_exception}")
            raise Exception(f"{internal_server_exception}")
        except UnauthorizedRequest as unauthorized_request:
            logging.warning(f"User unauthorized to process this request. {unauthorized_request}")
            raise Exception(f"{unauthorized_request}")
        except AccessForbidden as access_forbidden:
            logging.warning(f"Invalid permissions to view requested resource. {access_forbidden}")
            raise Exception(f"{access_forbidden}")
        except ResourceNotFound as resource_not_found:
            logging.warning(f"Requested resource not found. {resource_not_found}")
            raise Exception(f"{resource_not_found}")
        except UnprocessableDataProvided as unprocessable_data_provided:
            logging.error(f"Request could not be processed. {unprocessable_data_provided}")
            raise Exception(f"{unprocessable_data_provided}")
        except FailedRequest as failed_request:
            logging.error(f"Request failed. {failed_request}")
        except Exception as e:
            logging.warning(f"Could not fetch world object. UUID: {world_uuid}, GRANULARITY: {granularity}")
            raise Exception(f"{e}")
    def get_category(self, category_uuid:str='', granularity:int=-1):
        try:
            logging.info(f"Category object fetched. UUID: {category_uuid}, GRANULARITY: {granularity}")
            return self.client.category.get(category_uuid, granularity) 
        except ConnectionException as connection_exception:
            logging.warning(f"Unable to connect to WorldAnvil API. {connection_exception}")
            raise Exception(f"{connection_exception}")
        except InternalServerException as internal_server_exception:
            logging.warning(f"WorldAnvil server unable to process request. {internal_server_exception}")
            raise Exception(f"{internal_server_exception}")
        except UnauthorizedRequest as unauthorized_request:
            logging.warning(f"User unauthorized to process this request. {unauthorized_request}")
            raise Exception(f"{unauthorized_request}")
        except AccessForbidden as access_forbidden:
            logging.warning(f"Invalid permissions to view requested resource. {access_forbidden}")
            raise Exception(f"{access_forbidden}")
        except ResourceNotFound as resource_not_found:
            logging.warning(f"Requested resource not found. {resource_not_found}")
            raise Exception(f"{resource_not_found}")
        except UnprocessableDataProvided as unprocessable_data_provided:
            logging.error(f"Request could not be processed. {unprocessable_data_provided}")
            raise Exception(f"{unprocessable_data_provided}")
        except FailedRequest as failed_request:
            logging.error(f"Request failed. {failed_request}")
        except Exception as e:
            logging.warning(f"Could not fetch category object. UUID: {category_uuid}, GRANULARITY: {granularity}")
            raise Exception(f"{e}")
    def get_article(self, article_uuid:str='', granularity:int=-1):
        try:
            logging.info(f"Article object fetched. UUID: {article_uuid}, GRANULARITY: {granularity}")
            return self.client.article.get(article_uuid, granularity) 
        except ConnectionException as connection_exception:
            logging.warning(f"Unable to connect to WorldAnvil API. {connection_exception}")
            raise Exception(f"{connection_exception}")
        except InternalServerException as internal_server_exception:
            logging.warning(f"WorldAnvil server unable to process request. {internal_server_exception}")
            raise Exception(f"{internal_server_exception}")
        except UnauthorizedRequest as unauthorized_request:
            logging.warning(f"User unauthorized to process this request. {unauthorized_request}")
            raise Exception(f"{unauthorized_request}")
        except AccessForbidden as access_forbidden:
            logging.warning(f"Invalid permissions to view requested resource. {access_forbidden}")
            raise Exception(f"{access_forbidden}")
        except ResourceNotFound as resource_not_found:
            logging.warning(f"Requested resource not found. {resource_not_found}")
            raise Exception(f"{resource_not_found}")
        except UnprocessableDataProvided as unprocessable_data_provided:
            logging.error(f"Request could not be processed. {unprocessable_data_provided}")
            raise Exception(f"{unprocessable_data_provided}")
        except FailedRequest as failed_request:
            logging.error(f"Request failed. {failed_request}")
        except Exception as e:
            logging.warning(f"Could not fetch article object. UUID: {article_uuid}, GRANULARITY: {granularity}")
            raise Exception(f"{e}")
    def get_world_categories_mapping(self, world_uuid:str=''):
        try:
            categories = [category['id'] for category in self.client.world.categories(world_uuid)]
            logging.info(f"Categories fetched for world {world_uuid}: {', '.join(categories)}")
            return {world_uuid: categories}
        except ConnectionException as connection_exception:
            logging.warning(f"Unable to connect to WorldAnvil API. {connection_exception}")
            raise Exception(f"{connection_exception}")
        except InternalServerException as internal_server_exception:
            logging.warning(f"WorldAnvil server unable to process request. {internal_server_exception}")
            raise Exception(f"{internal_server_exception}")
        except UnauthorizedRequest as unauthorized_request:
            logging.warning(f"User unauthorized to process this request. {unauthorized_request}")
            raise Exception(f"{unauthorized_request}")
        except AccessForbidden as access_forbidden:
            logging.warning(f"Invalid permissions to view requested resource. {access_forbidden}")
            raise Exception(f"{access_forbidden}")
        except ResourceNotFound as resource_not_found:
            logging.warning(f"Requested resource not found. {resource_not_found}")
            raise Exception(f"{resource_not_found}")
        except UnprocessableDataProvided as unprocessable_data_provided:
            logging.error(f"Request could not be processed. {unprocessable_data_provided}")
            raise Exception(f"{unprocessable_data_provided}")
        except FailedRequest as failed_request:
            logging.error(f"Request failed. {failed_request}")
        except Exception as e:
            logging.warning(f"Could not fetch categories for world {world_uuid}")
            raise Exception(f"{e}")
    def get_category_articles_mapping(self, world_uuid:str='', category_uuids:list=[]):
        try:
            category_uuids.append('-1') #Account for uncategorized articles
            articles_mapping={cat_uuid: [art['id'] for art in self.client.world.articles(world_uuid, cat_uuid)
                                         ] for cat_uuid in category_uuids}
            logging.info(f"Fetched category-article mapping for world {world_uuid}:\n{json.dumps(articles_mapping, indent=2)}")
            return articles_mapping
        except ConnectionException as connection_exception:
            logging.warning(f"Unable to connect to WorldAnvil API. {connection_exception}")
            raise Exception(f"{connection_exception}")
        except InternalServerException as internal_server_exception:
            logging.warning(f"WorldAnvil server unable to process request. {internal_server_exception}")
            raise Exception(f"{internal_server_exception}")
        except UnauthorizedRequest as unauthorized_request:
            logging.warning(f"User unauthorized to process this request. {unauthorized_request}")
            raise Exception(f"{unauthorized_request}")
        except AccessForbidden as access_forbidden:
            logging.warning(f"Invalid permissions to view requested resource. {access_forbidden}")
            raise Exception(f"{access_forbidden}")
        except ResourceNotFound as resource_not_found:
            logging.warning(f"Requested resource not found. {resource_not_found}")
            raise Exception(f"{resource_not_found}")
        except UnprocessableDataProvided as unprocessable_data_provided:
            logging.error(f"Request could not be processed. {unprocessable_data_provided}")
            raise Exception(f"{unprocessable_data_provided}")
        except FailedRequest as failed_request:
            logging.error(f"Request failed. {failed_request}")
        except Exception as e:
            logging.warning(f"Could not process category-article mapping for world {world_uuid} and categories: {', '.join(category_uuids)}")
            raise Exception(f"{e}")


class TrackWorld:
    def __init__(self,
                 url:str='',
                 track_changes:dict={},
                 client:WAClient=None):
        try:
            self.url=url
            self.track_changes=track_changes
            self.client=client
            self.load_auth_user_id()
            self.load_world_uuid()

            self.load_category_mapping(self.track_changes['categories'])
            self.load_articles_dict(self.track_changes['articles'])

            self.set_track_granularities()
            self.set_beacon_granularities()
            logging.info(f">>> TrackWorld object initiated for world {self.world_uuid} owned by user {self.auth_user_id}. Track changes settings:\n{json.dumps(self.track_changes, indent=2)}")
        except Exception as e:
            logging.warning(f"TrackWorld object could not be created")
            raise Exception(f"{e}")
    def load_auth_user_id(self):
        try:
            self.auth_user_id=self.client.get_auth_user_id()['id']
            logging.info(f"ID fetched for the authenticated user.")
        except ConnectionException as connection_exception:
            logging.warning(f"Unable to connect to WorldAnvil API. {connection_exception}")
            raise Exception(f"{connection_exception}")
        except InternalServerException as internal_server_exception:
            logging.warning(f"WorldAnvil server unable to process request. {internal_server_exception}")
            raise Exception(f"{internal_server_exception}")
        except UnauthorizedRequest as unauthorized_request:
            logging.warning(f"User unauthorized to process this request. {unauthorized_request}")
            raise Exception(f"{unauthorized_request}")
        except AccessForbidden as access_forbidden:
            logging.warning(f"Invalid permissions to view requested resource. {access_forbidden}")
            raise Exception(f"{access_forbidden}")
        except ResourceNotFound as resource_not_found:
            logging.warning(f"Requested resource not found. {resource_not_found}")
            raise Exception(f"{resource_not_found}")
        except UnprocessableDataProvided as unprocessable_data_provided:
            logging.error(f"Request could not be processed. {unprocessable_data_provided}")
            raise Exception(f"{unprocessable_data_provided}")
        except FailedRequest as failed_request:
            logging.error(f"Request failed. {failed_request}")
        except Exception as e:
            logging.warning(f"Could not fetch ID for the authenticated user")
            raise Exception(f"{e}")
    def load_world_uuid(self):
        try:
            worlds={world['url']: world['id'] for world in self.client.get_user_worlds(self.auth_user_id)}
             
            self.world_uuid=worlds[self.url]
            logging.info(f"ID loaded for the selected world: {self.world_uuid}")
        except ConnectionException as connection_exception:
            logging.warning(f"Unable to connect to WorldAnvil API. {connection_exception}")
            raise Exception(f"{connection_exception}")
        except InternalServerException as internal_server_exception:
            logging.warning(f"WorldAnvil server unable to process request. {internal_server_exception}")
            raise Exception(f"{internal_server_exception}")
        except UnauthorizedRequest as unauthorized_request:
            logging.warning(f"User unauthorized to process this request. {unauthorized_request}")
            raise Exception(f"{unauthorized_request}")
        except AccessForbidden as access_forbidden:
            logging.warning(f"Invalid permissions to view requested resource. {access_forbidden}")
            raise Exception(f"{access_forbidden}")
        except ResourceNotFound as resource_not_found:
            logging.warning(f"Requested resource not found. {resource_not_found}")
            raise Exception(f"{resource_not_found}")
        except UnprocessableDataProvided as unprocessable_data_provided:
            logging.error(f"Request could not be processed. {unprocessable_data_provided}")
            raise Exception(f"{unprocessable_data_provided}")
        except FailedRequest as failed_request:
            logging.error(f"Request failed. {failed_request}")
        except Exception as e:
            logging.warning(f"Could not load world id for the selected world")
            raise Exception(f"{e}")
    def load_category_mapping(self, track:bool=False):
        try:
            if track:
                logging.info(f"Category tracking: ON. Fetching category mapping...")
                self.category_mapping=self.client.get_world_categories_mapping(self.world_uuid)
            else:
                logging.info(f"Category tracking: OFF.")
                pass
        except ConnectionException as connection_exception:
            logging.warning(f"Unable to connect to WorldAnvil API. {connection_exception}")
            raise Exception(f"{connection_exception}")
        except InternalServerException as internal_server_exception:
            logging.warning(f"WorldAnvil server unable to process request. {internal_server_exception}")
            raise Exception(f"{internal_server_exception}")
        except UnauthorizedRequest as unauthorized_request:
            logging.warning(f"User unauthorized to process this request. {unauthorized_request}")
            raise Exception(f"{unauthorized_request}")
        except AccessForbidden as access_forbidden:
            logging.warning(f"Invalid permissions to view requested resource. {access_forbidden}")
            raise Exception(f"{access_forbidden}")
        except ResourceNotFound as resource_not_found:
            logging.warning(f"Requested resource not found. {resource_not_found}")
            raise Exception(f"{resource_not_found}")
        except UnprocessableDataProvided as unprocessable_data_provided:
            logging.error(f"Request could not be processed. {unprocessable_data_provided}")
            raise Exception(f"{unprocessable_data_provided}")
        except FailedRequest as failed_request:
            logging.error(f"Request failed. {failed_request}")
        except Exception as e:
            logging.warning(f"Could not load category mapping: {e}")
            raise Exception(f"{e}")
    def load_articles_dict(self, track:bool=False):
        try:
            if track:
                logging.info(f"Articles tracking: ON. Fetching article mapping...")
                
                category_uuids=self.category_mapping[self.world_uuid].copy()
                self.articles_mapping=self.client.get_category_articles_mapping(self.world_uuid, category_uuids)
            else:
                logging.info(f"Articles tracking: OFF.")
                pass
        except ConnectionException as connection_exception:
            logging.warning(f"Unable to connect to WorldAnvil API. {connection_exception}")
            raise Exception(f"{connection_exception}")
        except InternalServerException as internal_server_exception:
            logging.warning(f"WorldAnvil server unable to process request. {internal_server_exception}")
            raise Exception(f"{internal_server_exception}")
        except UnauthorizedRequest as unauthorized_request:
            logging.warning(f"User unauthorized to process this request. {unauthorized_request}")
            raise Exception(f"{unauthorized_request}")
        except AccessForbidden as access_forbidden:
            logging.warning(f"Invalid permissions to view requested resource. {access_forbidden}")
            raise Exception(f"{access_forbidden}")
        except ResourceNotFound as resource_not_found:
            logging.warning(f"Requested resource not found. {resource_not_found}")
            raise Exception(f"{resource_not_found}")
        except UnprocessableDataProvided as unprocessable_data_provided:
            logging.error(f"Request could not be processed. {unprocessable_data_provided}")
            raise Exception(f"{unprocessable_data_provided}")
        except FailedRequest as failed_request:
            logging.error(f"Request failed. {failed_request}")
        except Exception as e:
            logging.warning(f"Could not load article mapping: {e}")
            raise Exception(f"{e}")
    def get_file_index_per_type(self, _type:str='world'):
        try:
            _file_index={}
            match _type:
                case 'world':
                    _file_index={self.world_uuid: 'world'}
                case 'categories':
                    _file_index={category_uuid: 'category' for category_uuid in self.category_mapping[self.world_uuid]}
                case 'articles':
                    for cat in self.articles_mapping.keys():
                        _file_index.update({article_uuid: 'article' for article_uuid in self.articles_mapping[cat]})
                case _:
                    logging.warning(f"Invalid file index type: {_type}")
                    raise Exception(f"Invalid file index type: {_type}")
            return _file_index
        except Exception as e:
            raise Exception(f"{e}")
    def set_track_granularities(self):
        try:
            self.track_gran={
                    'world': 1,
                    'category': 1,
                    'article': 1
            }
            logging.info(f"Tracking granularities set:\n{json.dumps(self.track_gran, indent=2)}")
        except Exception as e:
            logging.warning(f"Could not set tracking granularities: {e}")
            raise Exception(f"{e}")
    def set_beacon_granularities(self):
        try:
            self.beacon_gran={
                    'world': 0,
                    'category': 0,
                    'article': -1
            }
            logging.info(f"Beacon granularities set:\n{json.dumps(self.beacon_gran, indent=2)}")
            assert all([self.beacon_gran[prop] <= self.track_gran[prop] for prop in self.track_gran.keys()]) == True
        except AssertionError:
            raise Exception("Invalid granularity settings. Beacon must be <= than Track.")
        except Exception as e:
            raise Exception(f"{e}")
    def update_file_index(self, gitworker:Gitworker=None):
        try:
            temp_file_index=gitworker.get_file_index()
            world_file_index=self.get_file_index_per_type(_type='world')
            temp_file_index.update(world_file_index)

            for _type in ['categories', 'articles']:
                if self.track_changes[_type]:
                    resolved_file_index=self.get_file_index_per_type(_type=_type)
                    temp_file_index.update(resolved_file_index)

            if not gitworker.compare_object_hash(content=json.dumps(temp_file_index), reg_type='file_index'):
                gitworker.update_file_index(temp_file_index)
                gitworker.add_to_index()
                gitworker.post_commit(short_commit_message='File index updated')
                gitworker.push_to_remote_repository()
            logging.info(f">>>> File index updated <<<<")
        except ConnectionException as connection_exception:
            logging.warning(f"Unable to connect to WorldAnvil API. {connection_exception}")
            raise Exception(f"{connection_exception}")
        except InternalServerException as internal_server_exception:
            logging.warning(f"WorldAnvil server unable to process request. {internal_server_exception}")
            raise Exception(f"{internal_server_exception}")
        except UnauthorizedRequest as unauthorized_request:
            logging.warning(f"User unauthorized to process this request. {unauthorized_request}")
            raise Exception(f"{unauthorized_request}")
        except AccessForbidden as access_forbidden:
            logging.warning(f"Invalid permissions to view requested resource. {access_forbidden}")
            raise Exception(f"{access_forbidden}")
        except ResourceNotFound as resource_not_found:
            logging.warning(f"Requested resource not found. {resource_not_found}")
            raise Exception(f"{resource_not_found}")
        except UnprocessableDataProvided as unprocessable_data_provided:
            logging.error(f"Request could not be processed. {unprocessable_data_provided}")
            raise Exception(f"{unprocessable_data_provided}")
        except FailedRequest as failed_request:
            logging.error(f"Request failed. {failed_request}")

        except Exception as e:
            raise Exception(f"{e}")
    def resolve_world(self, gitworker:Gitworker=None):
        try: 
            uuid=self.world_uuid
            beacon=self.client.get_world(uuid, self.beacon_gran['world'])
            logging.info(f">>> Resolving World Object Tracking <<<")
            if not gitworker.compare_object_hash(uuid, beacon, reg_type='beacon'):
                logging.info(f">> Beacon hash condition satisfied <<")
                gitworker.update_hash_reg(uuid, beacon, reg_type='beacon')
                content=self.client.get_world(uuid, self.track_gran['world'])
                if not gitworker.compare_object_hash(uuid, content, reg_type='track'):
                    logging.info(f"> Content hash condition satisfied <")

                    gitworker.update_repo_object(uuid, content)
                    gitworker.update_hash_reg(uuid, content, reg_type='track')
                    gitworker.update_index_list(uuid)
                    gitworker.add_to_index()
                    gitworker.update_commit_message(f"{uuid}: {content['url']}, beacon gran: {self.beacon_gran['world']}, track_gran: {self.track_gran['world']}")

                    gitworker.post_commit(short_commit_message='World update')
                    gitworker.push_to_remote_repository()
                else:
                    pass
        except ConnectionException as connection_exception:
            logging.warning(f"Unable to connect to WorldAnvil API. {connection_exception}")
            raise Exception(f"{connection_exception}")
        except InternalServerException as internal_server_exception:
            logging.warning(f"WorldAnvil server unable to process request. {internal_server_exception}")
            raise Exception(f"{internal_server_exception}")
        except UnauthorizedRequest as unauthorized_request:
            logging.warning(f"User unauthorized to process this request. {unauthorized_request}")
            raise Exception(f"{unauthorized_request}")
        except AccessForbidden as access_forbidden:
            logging.warning(f"Invalid permissions to view requested resource. {access_forbidden}")
            raise Exception(f"{access_forbidden}")
        except ResourceNotFound as resource_not_found:
            logging.warning(f"Requested resource not found. {resource_not_found}")
            raise Exception(f"{resource_not_found}")
        except UnprocessableDataProvided as unprocessable_data_provided:
            logging.error(f"Request could not be processed. {unprocessable_data_provided}")
            raise Exception(f"{unprocessable_data_provided}")
        except FailedRequest as failed_request:
            logging.error(f"Request failed. {failed_request}")
        except Exception as e:
            logging.warning(f"Could not resolve world object tracking: {e}")
            raise Exception(f"{e}")
    def resolve_categories(self, gitworker:Gitworker=None):
        try:
            if self.track_changes['categories']:
                world_uuid=self.world_uuid
                category_uuids=self.category_mapping[self.world_uuid]

                categories_changed=0
                for uuid in category_uuids:    
                    beacon=self.client.get_category(uuid, self.beacon_gran['category'])
                    logging.info(f">>> Resolving Category Object Tracking <<<")
                    if not gitworker.compare_object_hash(uuid, beacon, reg_type='beacon'):
                        logging.info(f">> Beacon hash condition satisfied <<")
                        gitworker.update_hash_reg(uuid, beacon, reg_type='beacon')
                        content=self.client.get_category(uuid, self.track_gran['category'])
                        if not gitworker.compare_object_hash(uuid, content, reg_type='track'):
                            logging.info(f"> Content hash condition satisfied <")

                            categories_changed += 1

                            gitworker.update_repo_object(uuid, content)
                            gitworker.update_hash_reg(uuid, content, reg_type='track')
                            gitworker.update_index_list(uuid)
                            gitworker.add_to_index()
                            gitworker.update_commit_message(f"{uuid}: {content['url']}, beacon gran: {self.beacon_gran['category']}, track_gran: {self.track_gran['category']}")

                if categories_changed > 0:
                    gitworker.post_commit(short_commit_message='Categories update')
                    gitworker.push_to_remote_repository()
                    categories_changed=0
            else:
                logging.info(f"Categories tracking disabled in configuration file.")
        except ConnectionException as connection_exception:
            logging.warning(f"Unable to connect to WorldAnvil API. {connection_exception}")
            raise Exception(f"{connection_exception}")
        except InternalServerException as internal_server_exception:
            logging.warning(f"WorldAnvil server unable to process request. {internal_server_exception}")
            raise Exception(f"{internal_server_exception}")
        except UnauthorizedRequest as unauthorized_request:
            logging.warning(f"User unauthorized to process this request. {unauthorized_request}")
            raise Exception(f"{unauthorized_request}")
        except AccessForbidden as access_forbidden:
            logging.warning(f"Invalid permissions to view requested resource. {access_forbidden}")
            raise Exception(f"{access_forbidden}")
        except ResourceNotFound as resource_not_found:
            logging.warning(f"Requested resource not found. {resource_not_found}")
            raise Exception(f"{resource_not_found}")
        except UnprocessableDataProvided as unprocessable_data_provided:
            logging.error(f"Request could not be processed. {unprocessable_data_provided}")
            raise Exception(f"{unprocessable_data_provided}")
        except FailedRequest as failed_request:
            logging.error(f"Request failed. {failed_request}")
        except Exception as e:
            logging.warning(f"Could not resolve category objects tracking: {e}")
            raise Exception(f"{e}") 
    def resolve_articles(self, gitworker:Gitworker=None):
        try:
            if self.track_changes['articles']:
                for cat_uuid in self.articles_mapping:
                    logging.info(f">>>> Resolving Articles belonging to Category: {cat_uuid} <<<<")
                    articles_changed=0
                    for uuid in self.articles_mapping[cat_uuid]:
                        beacon=self.client.get_article(uuid, self.beacon_gran['article'])
                        logging.info(f">>> Resolving Article Object Tracking <<<")
                        if not gitworker.compare_object_hash(uuid, beacon, reg_type='beacon'):
                            logging.info(f">> Beacon hash condition satisfied <<")
                            gitworker.update_hash_reg(uuid, beacon, reg_type='beacon')
                            content=self.client.get_article(uuid, self.track_gran['article'])
                            if not gitworker.compare_object_hash(uuid, content, reg_type='track'):
                                logging.info(f"> Content hash condition satisfied <")

                                articles_changed += 1

                                gitworker.update_repo_object(uuid, content)
                                gitworker.update_hash_reg(uuid, content, reg_type='track')
                                gitworker.update_index_list(uuid)
                                gitworker.add_to_index()
                                gitworker.update_commit_message(f"{uuid}: {content['url']}, beacon gran: {self.beacon_gran['article']}, track_gran: {self.track_gran['article']}")

                    if articles_changed > 0:
                        gitworker.post_commit(short_commit_message=f'Articles update for Category {cat_uuid}')
                        gitworker.push_to_remote_repository()
                        articles_changed=0
            else:
                logging.info(f"Articles tracking disabled in configuration file.")
        except ConnectionException as connection_exception:
            logging.warning(f"Unable to connect to WorldAnvil API. {connection_exception}")
            raise Exception(f"{connection_exception}")
        except InternalServerException as internal_server_exception:
            logging.warning(f"WorldAnvil server unable to process request. {internal_server_exception}")
            raise Exception(f"{internal_server_exception}")
        except UnauthorizedRequest as unauthorized_request:
            logging.warning(f"User unauthorized to process this request. {unauthorized_request}")
            raise Exception(f"{unauthorized_request}")
        except AccessForbidden as access_forbidden:
            logging.warning(f"Invalid permissions to view requested resource. {access_forbidden}")
            raise Exception(f"{access_forbidden}")
        except ResourceNotFound as resource_not_found:
            logging.warning(f"Requested resource not found. {resource_not_found}")
            raise Exception(f"{resource_not_found}")
        except UnprocessableDataProvided as unprocessable_data_provided:
            logging.error(f"Request could not be processed. {unprocessable_data_provided}")
            raise Exception(f"{unprocessable_data_provided}")
        except FailedRequest as failed_request:
            logging.error(f"Request failed. {failed_request}")
        except Exception as e:
            logging.warning(f"Could not resolve article objects tracking: {e}")
            raise Exception(f"{e}")




def main():
    secrets=Secrets()
    gitw=Gitworker(secrets)
    wacli=WAClient(secrets.api_key, secrets.api_token)

    while datetime.now() < datetime.strptime(QUIT_AT, '%Y-%m-%d %H:%M' ):
        for _world in secrets.worlds_list:
            tr = TrackWorld(_world['url'],
                            _world['track_changes'],
                            wacli) 
            tr.update_file_index(gitw)
            tr.resolve_world(gitw)
            tr.resolve_categories(gitw)
            tr.resolve_articles(gitw)
        time.sleep(PING_INTERVAL_S)



if __name__=='__main__':
    main()
    print("End of script.")
