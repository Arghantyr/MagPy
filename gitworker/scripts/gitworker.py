import Utils
import BackendUtils
from APIClients import WAClient
from APIUtils import WorldAnvilUtils as wau
from Secrets import WorldAnvilSecrets
from Schemas import WORLDANVIL_SECRET_SCHEMA

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

class Gitworker:
    def __init__(self, secret_obj=None):
        self.load_secret(secret_obj)
        self.load_repo()
        self.load_registries()
        self.validate_repo_settings()
        self.initiate_commit_backend()

        logging.info("Gitworker object initiated.")
    def load_secret(self, secret_obj=None):
        try:
            self.repo_ssh_url=secret_obj.repo_ssh_url
            logging.info("Gitworker: secrets loaded...")
        except Exception as e:
            logging.warning("Gitworker: unable to load secrets")
            raise Exceptions(f"{e}")
    def load_repo(self):
        try:
            self.remote_repo_name=self.repo_ssh_url.rstrip('.git').split('/')[-1]
            self.repo_path=f"{REPO_PATH}/{self.remote_repo_name}"
            self.repo=git.Repo(self.repo_path)
            logging.info("Gitworker: repository object set...")
        except Exception as e:
            logging.warning("Gitworker: unable to load repository")
            raise Exception(f"{e}") 
    def load_registries(self):
        try:
            self.registries={
                'beacon_hash_reg': BackendUtils.Registry(reg_dir_filepath=self.repo_path, reg_name='beacon_hash_reg'),
                'track_hash_reg': BackendUtils.Registry(reg_dir_filepath=self.repo_path, reg_name='track_hash_reg'),
                'file_index': BackendUtils.Registry(reg_dir_filepath=self.repo_path, reg_name='file_index')
            }
        except Exception as e:
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
            self.index_list=[reg_name for reg_name in self.registries.keys()]
            logging.info("Gitworker: commit message and index initiated...")
        except Exception as e:
            logging.warning("Gitworker: unable to initiate commit message and index")
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
    
    def update_repo_object(self, uuid:str=NULL_UUID, new_content:dict|list={}):
        try:
            with open(f'{REPO_PATH}/{self.remote_repo_name}/{uuid}', mode='w') as file:
                new_content_str=json.dumps(new_content, indent=2)
                
                file.write(new_content_str)
            logging.info(f"Object with uuid: {uuid} updated in the local repository.")
        except Exception as e:
            logging.warning(f"Unable to update local repo for uuid: {uuid}")
            raise Exception(f"{e}")

    def push_to_remote_repository(self):
        try:
            with self.repo.git.custom_environment(GIT_SSH_COMMAND=f'ssh -i {SSH_ID_FILE}'):
                self.remote.push()
            logging.info(f"Pushing commits to remote repository")
        except Exception as e:
            logging.warning(f"Unable to push to remote repository")
            raise Exception(f"{e}")


class TrackWorld:
    def __init__(self,
                 url:str='',
                 track_changes:dict={},
                 client:WAClient=WAClient('', '')):
        try:
            self.url=url
            self.track_changes=track_changes
            self.client=client
            self.load_auth_user_id()
            self.load_world_uuid()
            self.load_user_world_mapping(self.track_changes['world'])
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
        except Exception as e:
            raise Exception(f"Could not load user id. {e}")
    def load_world_uuid(self):
        try:
            logging.info(f"User id: {self.auth_user_id}")
            worlds={world['url']: world['id'] for world in self.client.get_user_worlds(self.auth_user_id)}
             
            self.world_uuid=worlds[self.url]
            logging.info(f"ID loaded for the selected world: {self.world_uuid}")
        except Exception as e:
            raise Exception(f"Could not load world uuid. {e}")
    def load_user_world_mapping(self, track:bool=False): 
        try:
            if track:
                logging.info(f"World tracking: ON. Fetching user-world mapping...")
                self.world_mapping={ self.auth_user_id: [world['id'] for world in self.client.get_user_worlds(self.auth_user_id) if world['id'] == self.world_uuid] }
            else:
                logging.info(f"World tracking: OFF.")
        except Exception as e:
            raise Exception(f"Could not load user-world mapping. {e}")
    def load_category_mapping(self, track:bool=False):
        try:
            if track:
                logging.info(f"Category tracking: ON. Fetching category mapping...")
                self.category_mapping=self.client.get_world_categories_mapping(self.world_uuid)
            else:
                logging.info(f"Category tracking: OFF.")
        except Exception as e:
            raise Exception(f"Could not load category mapping. {e}")
    def load_articles_dict(self, track:bool=False):
        try:
            if track:
                logging.info(f"Articles tracking: ON. Fetching article mapping...")
                
                category_uuids=self.category_mapping[self.world_uuid].copy()
                self.articles_mapping=self.client.get_category_articles_mapping(self.world_uuid, category_uuids)
            else:
                logging.info(f"Articles tracking: OFF.")
        except Exception as e:
            raise Exception(f"Could not load articles mapping. {e}")
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
            temp_file_index=gitworker.registries['file_index'].get_registry()
            world_file_index=self.get_file_index_per_type(_type='world')
            temp_file_index.update(world_file_index)

            for _type in ['categories', 'articles']:
                if self.track_changes[_type]:
                    resolved_file_index=self.get_file_index_per_type(_type=_type)
                    temp_file_index.update(resolved_file_index)

            if not gitworker.registries['file_index'].compare_against_registry(value=temp_file_index):
                gitworker.registries['file_index'].update_registry(value=temp_file_index)
                gitworker.add_to_index()
                gitworker.post_commit(short_commit_message='File index updated')
                gitworker.push_to_remote_repository()
            logging.info(f">>>> File index updated <<<<")
        except Exception as e:
            raise Exception(f"File index could not be updated. {e}")
    def resolve_world(self, gitworker:Gitworker=None):
        try:
            #uuid=self.world_uuid
            if self.track_changes['world']:
                for user_uuid in self.world_mapping:
                    logging.info(f">>>> Resolving World belonging to User: {user_uuid} <<<<")
                    worlds_changed=0
                    for uuid in self.world_mapping[user_uuid]: 
                        beacon=self.client.get_world(uuid, self.beacon_gran['world'])
                        logging.info(f">>> Resolving World Object Tracking <<<")
                        if not gitworker.registries['beacon_hash_reg'].compare_against_entry(identifier=uuid, value=beacon):
                            logging.info(f">> Beacon hash condition satisfied <<")
                            gitworker.registries['beacon_hash_reg'].update_entry(identifier=uuid, value=beacon)
                            content=self.client.get_world(uuid, self.track_gran['world'])
                            if not gitworker.registries['track_hash_reg'].compare_against_entry(identifier=uuid, value=content):
                                logging.info(f"> Content hash condition satisfied <")

                                worlds_changed += 1

                                gitworker.update_repo_object(uuid, content)
                                gitworker.registries['track_hash_reg'].update_entry(identifier=uuid, value=content)
                                gitworker.update_index_list(uuid)
                                gitworker.add_to_index()
                                gitworker.update_commit_message(f"{uuid}: {content['url']}, beacon gran: {self.beacon_gran['world']}, track_gran: {self.track_gran['world']}")
                if worlds_changed > 0:
                    gitworker.post_commit(short_commit_message='World update')
                    gitworker.push_to_remote_repository()
                    worlds_changed=0
            else:
                logging.info(f"World tracking disabled in configuration file.")
        except Exception as e:
            raise Exception(f">>> Cannot resolve world. {e}")
    def resolve_categories(self, gitworker:Gitworker=None):
        try:
            if self.track_changes['categories']:
                #world_uuid=self.world_uuid
                #category_uuids=self.category_mapping[self.world_uuid]
                for world_uuid in self.category_mapping:
                    logging.info(f">>>> Resolving Categories belonging to World: {world_uuid} <<<<")
                    categories_changed=0
                    for uuid in self.category_mapping[world_uuid]: 
                        beacon=self.client.get_category(uuid, self.beacon_gran['category'])
                        logging.info(f">>> Resolving Category Object Tracking <<<")
                        if not gitworker.registries['beacon_hash_reg'].compare_against_entry(identifier=uuid, value=beacon):
                            logging.info(f">> Beacon hash condition satisfied <<")
                            gitworker.registries['beacon_hash_reg'].update_entry(identifier=uuid, value=beacon)
                            content=self.client.get_category(uuid, self.track_gran['category'])
                            if not gitworker.registries['track_hash_reg'].compare_against_entry(identifier=uuid, value=content):
                                logging.info(f"> Content hash condition satisfied <")

                                categories_changed += 1

                                gitworker.update_repo_object(uuid, content)
                                gitworker.registries['track_hash_reg'].update_entry(identifier=uuid, value=content)
                                gitworker.update_index_list(uuid)
                                gitworker.add_to_index()
                                gitworker.update_commit_message(f"{uuid}: {content['url']}, beacon gran: {self.beacon_gran['category']}, track_gran: {self.track_gran['category']}")

                    if categories_changed > 0:
                        gitworker.post_commit(short_commit_message='Categories update')
                        gitworker.push_to_remote_repository()
                        categories_changed=0
            else:
                logging.info(f"Categories tracking disabled in configuration file.")
        except Exception as e:
            raise Exception(f">>> Cannot resolve categories. {e}")
    def resolve_articles(self, gitworker:Gitworker=None):
        try:
            if self.track_changes['articles']:
                for cat_uuid in self.articles_mapping:
                    logging.info(f">>>> Resolving Articles belonging to Category: {cat_uuid} <<<<")
                    articles_changed=0
                    for uuid in self.articles_mapping[cat_uuid]:
                        beacon=self.client.get_article(uuid, self.beacon_gran['article'])
                        logging.info(f">>> Resolving Article Object Tracking <<<")
                        if not gitworker.registries['beacon_hash_reg'].compare_against_entry(identifier=uuid, value=beacon):
                            logging.info(f">> Beacon hash condition satisfied <<")
                            gitworker.registries['beacon_hash_reg'].update_entry(identifier=uuid, value=beacon)
                            content=self.client.get_article(uuid, self.track_gran['article'])
                            if not gitworker.registries['track_hash_reg'].compare_against_entry(identifier=uuid, value=content):
                                logging.info(f"> Content hash condition satisfied <")

                                articles_changed += 1

                                gitworker.update_repo_object(uuid, content)
                                gitworker.registries['track_hash_reg'].update_entry(identifier=uuid, value=content)
                                gitworker.update_index_list(uuid)
                                gitworker.add_to_index()
                                gitworker.update_commit_message(f"{uuid}: {content['url']}, beacon gran: {self.beacon_gran['article']}, track_gran: {self.track_gran['article']}")

                    if articles_changed > 0:
                        gitworker.post_commit(short_commit_message=f'Articles update for Category {cat_uuid}')
                        gitworker.push_to_remote_repository()
                        articles_changed=0
            else:
                logging.info(f"Articles tracking disabled in configuration file.")
        except Exception as e:
            raise Exception(f">>> Cannot resolve articles. {e}")



def main():
    wa_secrets=WorldAnvilSecrets(SECRET_PATH, WORLDANVIL_SECRET_SCHEMA)
    gitw=Gitworker(wa_secrets)
    wacli=WAClient(application_key=wa_secrets.application_key,
                   authentication_token=wa_secrets.authentication_token)


    while datetime.now() < datetime.strptime(QUIT_AT, '%Y-%m-%d %H:%M' ):
        for _world in wa_secrets.worlds_list:
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
