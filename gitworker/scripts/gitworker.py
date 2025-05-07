import BackendUtils
from APIClients import WAClient
from APIRelationships import WorldAnvilRelationships
from Secrets import WorldAnvilSecrets
from Schemas import WORLDANVIL_SECRET_SCHEMA

import json
import time
from datetime import datetime
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
                 client:WAClient=WAClient('', ''),
                 apiobj_rels=None):
        try:
            self.url=url
            self.track_changes=track_changes
            self.client=client
            self.apiobj_rels=apiobj_rels
            self.load_auth_user_id()
            self.load_world_uuid()
            self.load_mappings()
            
            self.set_granularities()
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

    def load_mappings(self):
        try:
            wa_mapping_api_generators = {
                    'world': { self.auth_user_id: [world['id'] for world in self.client.get_user_worlds(self.auth_user_id) if world['id'] == self.world_uuid] },
                    'categories': self.client.get_world_categories_mapping(self.world_uuid),
                    'articles': self.client.get_category_articles_mapping(self.world_uuid, self.client.get_world_categories_mapping(self.world_uuid)[self.world_uuid].copy())
            }
            self.mappings={}
            for _type in ['world', 'categories', 'articles']:
                if self.track_changes[_type]:
                    logging.info(f"{_type.capitalize()} tracking: ON. Fetching {self.apiobj_rels.find_parent(_type)}-{_type} mapping...")
                    self.mappings[_type]=wa_mapping_api_generators[_type]
                else:
                    logging.info(f"{_type.capitalize()} tracking: OFF.")
        except Exception as e:
            raise Exception(f"Could not load mapping. {e}")

    def get_file_index_per_type(self, _type:str='world'):
        try:
            _file_index={}
            match _type:
                case 'world':
                    _file_index={self.world_uuid: 'world'}
                case 'categories':
                    _file_index={category_uuid: 'category' for category_uuid in self.mappings['categories'][self.world_uuid]}
                case 'articles':
                    for cat in self.mappings['articles'].keys():
                        _file_index.update({article_uuid: 'article' for article_uuid in self.mappings['articles'][cat]})
                case _:
                    logging.warning(f"Invalid file index type: {_type}")
                    raise Exception(f"Invalid file index type: {_type}")
            return _file_index
        except Exception as e:
            raise Exception(f"{e}")

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

    def update_file_index(self, gitworker:Gitworker=None):
        try:
            temp_file_index=gitworker.registries['file_index'].get_registry()

            for _type in ['world', 'categories', 'articles']:
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

    def resolve_mapping(self, gitworker:Gitworker=None, mapping:dict={}, objtype:str='world', apimethod=None):
        try:
            if self.track_changes[objtype]:
                for key_uuid in mapping:
                    logging.info(f">>>> Resolving {objtype.capitalize()}  belonging to {self.apiobj_rels.find_parent(objtype)}: {key_uuid} <<<<")
                    objs_changed=0
                    for uuid in mapping[key_uuid]:

                        beacon=apimethod(uuid, self.beacon_gran[objtype])
                        logging.info(f">>> Resolving {objtype.capitalize()}-type Object Tracking <<<")
                        if not gitworker.registries['beacon_hash_reg'].compare_against_entry(identifier=uuid, value=beacon):
                            logging.info(f">> Beacon hash condition satisfied <<")
                            gitworker.registries['beacon_hash_reg'].update_entry(identifier=uuid, value=beacon)

                            content=apimethod(uuid, self.track_gran[objtype])
                            if not gitworker.registries['track_hash_reg'].compare_against_entry(identifier=uuid, value=content):
                                logging.info(f"> Content hash condition satisfied <")

                                objs_changed += 1

                                gitworker.update_repo_object(uuid, content)
                                gitworker.registries['track_hash_reg'].update_entry(identifier=uuid, value=content)
                                gitworker.update_index_list(uuid)
                                gitworker.add_to_index()
                                gitworker.update_commit_message(f"{uuid}: {content['url']}, beacon gran: {self.beacon_gran[objtype]}, track_gran: {self.track_gran[objtype]}")
                if objs_changed > 0:
                    gitworker.post_commit(short_commit_message=f'{objtype.capitalize()} update')
                    gitworker.push_to_remote_repository()
                    objs_changed=0
            else:
                logging.info(f"{objtype.capitalize()} tracking disabled in configuration file.")
        except Exception as e:
            raise Exception(f">>> Cannot resolve {objtype}. {e}")

class TrackObjectService:
    def __init__(self, gitworker: Gitworker, trackobjs: dict):
        self.gitworker = gitworker
        self.trackobjs = trackobjs

    def resolve_mapping(self, identifier: str, mapping: dict = {}, objtype: str = 'world', apimethod=None):
        try:
            if identifier not in self.trackobjs:
                raise Exception(f"TrackWorld object with identifier {identifier} not found.")
            
            trackobj = self.trackobjs[identifier]
            
            if trackobj.track_changes[objtype]:
                for key_uuid in mapping:
                    logging.info(f">>>> Resolving {objtype.capitalize()} belonging to {trackobj.apiobj_rels.find_parent(objtype)}: {key_uuid} <<<<")
                    objs_changed = 0
                    for uuid in mapping[key_uuid]:
                        beacon = apimethod(uuid, trackobj.beacon_gran[objtype])
                        logging.info(f">>> Resolving {objtype.capitalize()}-type Object Tracking <<<")
                        if not self.gitworker.registries['beacon_hash_reg'].compare_against_entry(identifier=uuid, value=beacon):
                            logging.info(f">> Beacon hash condition satisfied <<")
                            self.gitworker.registries['beacon_hash_reg'].update_entry(identifier=uuid, value=beacon)

                            content = apimethod(uuid, trackobj.track_gran[objtype])
                            if not self.gitworker.registries['track_hash_reg'].compare_against_entry(identifier=uuid, value=content):
                                logging.info(f"> Content hash condition satisfied <")

                                objs_changed += 1

                                self.gitworker.update_repo_object(uuid, content)
                                self.gitworker.registries['track_hash_reg'].update_entry(identifier=uuid, value=content)
                                self.gitworker.update_index_list(uuid)
                                self.gitworker.add_to_index()
                                self.gitworker.update_commit_message(f"{uuid}: {content['url']}, beacon gran: {trackobj.beacon_gran[objtype]}, track_gran: {trackobj.track_gran[objtype]}")
                    if objs_changed > 0:
                        self.gitworker.post_commit(short_commit_message=f'{objtype.capitalize()} update')
                        self.gitworker.push_to_remote_repository()
                        objs_changed = 0
            else:
                logging.info(f"{objtype.capitalize()} tracking disabled in configuration file.")
        except Exception as e:
            raise Exception(f">>> Cannot resolve {objtype}. {e}")


def main():
    wa_secrets = WorldAnvilSecrets(SECRET_PATH, WORLDANVIL_SECRET_SCHEMA)
    gitw = Gitworker(wa_secrets)
    wacli = WAClient(application_key=wa_secrets.application_key,
                     authentication_token=wa_secrets.authentication_token)

    trackobjs = { _world['url']: TrackWorld(_world['url'], _world['track_changes'], wacli, WorldAnvilRelationships()) for _world in wa_secrets.worlds_list }
    track_service = TrackObjectService(gitworker=gitw, trackobjs=trackobjs)

    while datetime.now() < datetime.strptime(QUIT_AT, '%Y-%m-%d %H:%M'):
        for identifier, trackobj in track_service.trackobjs.items():
            trackobj.update_file_index(gitw)
            track_service.resolve_mapping(identifier, trackobj.mappings['world'], 'world', apimethod=trackobj.client.get_world)
            track_service.resolve_mapping(identifier, trackobj.mappings['categories'], 'categories', apimethod=trackobj.client.get_category)
            track_service.resolve_mapping(identifier, trackobj.mappings['articles'], 'articles', apimethod=trackobj.client.get_article)

        time.sleep(PING_INTERVAL_S)



if __name__=='__main__':
    main()
    print("End of script.")
