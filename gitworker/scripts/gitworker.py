import json
import time
from datetime import datetime
import logging
import sys
import git

import BackendUtils
from APIClients import WAClient
from APIRelationships import WorldAnvilRelationships
from Secrets import WorldAnvilSecrets
from Schemas import WORLDANVIL_SECRET_SCHEMA



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
            raise Exception(f"{e}")
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
                 world_owner_uuid:str=NULL_UUID,
                 world_uuid:str=NULL_UUID,
                 track_changes:dict={},
                 apiobj_rels=None
                 ):
        try:
            self.world_owner_uuid=world_owner_uuid
            self.world_uuid=world_uuid
            self.track_changes=track_changes
            self.apiobj_rels=apiobj_rels
            logging.info(f">>> TrackWorld object initiated for world {self.world_uuid} owned by user {self.world_owner_uuid}. Track changes settings:\n{json.dumps(self.track_changes, indent=2)}")
        except Exception as e:
            logging.warning(f"TrackWorld object could not be created")
            raise Exception(f"{e}")

class TrackObjectService:
    def __init__(self, gitworker: Gitworker, trackobjs: dict, apiclient: WAClient):
        self.gitworker = gitworker
        self.trackobjs = trackobjs
        self.apiclient = apiclient

    def get_file_index_per_type(self, trackobj_identifier: str = NULL_UUID,
                                _type:str=''):
        try:
            wa_mapping_api_generators = {
                    'world': lambda: self.apiclient.get_mapping(trackobj_identifier, 'world'),
                    'categories': lambda: self.apiclient.get_mapping(trackobj_identifier, 'categories'),
                    'articles': lambda: self.apiclient.get_mapping(trackobj_identifier, 'articles')
            }
            _file_index={}
            match _type:
                case 'world':
                    _file_index={trackobj_identifier: 'world'}
                case 'categories':
                    _file_index={category_uuid: 'category' for category_uuid in wa_mapping_api_generators['categories']()}
                case 'articles':
                    articles_mapping = wa_mapping_api_generators['articles']()
                    for cat in articles_mapping.keys():
                        _file_index.update({article_uuid: 'article' for article_uuid in articles_mapping[cat]})
                case _:
                    logging.warning(f"Invalid file index type: {_type}")
                    raise Exception(f"Invalid file index type: {_type}")
            return _file_index
        except Exception as e:
            raise Exception(f"{e}")

    def update_file_index(self, trackobj_identifier: str = NULL_UUID):
        try:
            temp_file_index=self.gitworker.registries['file_index'].get_registry()

            for _type in ['world', 'categories', 'articles']:
                if self.trackobjs[trackobj_identifier].track_changes[_type]:
                    resolved_file_index=self.get_file_index_per_type(trackobj_identifier=trackobj_identifier,
                                                                     _type=_type)
                    temp_file_index.update(resolved_file_index)

            if not self.gitworker.registries['file_index'].compare_against_registry(value=temp_file_index):
                self.gitworker.registries['file_index'].update_registry(value=temp_file_index)
                self.gitworker.add_to_index()
                self.gitworker.post_commit(short_commit_message='File index updated')
                self.gitworker.push_to_remote_repository()
            logging.info(f">>>> File index updated <<<<")
        except Exception as e:
            raise Exception(f"File index could not be updated. {e}")

    def resolve_mapping(self, trackobj_identifier: str = NULL_UUID, objtype: str = 'world'):
        try:
            if trackobj_identifier not in self.trackobjs:
                raise Exception(f"TrackWorld object with identifier {trackobj_identifier} not found.")

            trackobj = self.trackobjs[trackobj_identifier]

            if trackobj.track_changes[objtype]:
                logging.info(f"{objtype.capitalize()} tracking: ON. Fetching {trackobj.apiobj_rels.find_parent(objtype)}-{objtype} mapping...")
                mapping = self.apiclient.get_mapping(_type=objtype, uuid=trackobj_identifier)
                for key_uuid in mapping:
                    logging.info(f">>>> Resolving {objtype.capitalize()} belonging to {trackobj.apiobj_rels.find_parent(objtype)}: {key_uuid} <<<<")
                    objs_changed = 0
                    for uuid in mapping[key_uuid]:
                        beacon = self.apiclient.apimethods_mapping[objtype](uuid=uuid, granularity=self.apiclient.beacon_gran[objtype])
                        logging.info(f">>> Resolving {objtype.capitalize()}-type Object Tracking <<<")
                        if not self.gitworker.registries['beacon_hash_reg'].compare_against_entry(identifier=uuid, value=beacon):
                            logging.info(f">> Beacon hash condition satisfied <<")
                            self.gitworker.registries['beacon_hash_reg'].update_entry(identifier=uuid, value=beacon)

                            content = self.apiclient.apimethods_mapping[objtype](uuid=uuid, granularity=self.apiclient.track_gran[objtype])
                            if not self.gitworker.registries['track_hash_reg'].compare_against_entry(identifier=uuid, value=content):
                                logging.info(f"> Content hash condition satisfied <")

                                objs_changed += 1

                                self.gitworker.update_repo_object(uuid=uuid, new_content=content)
                                self.gitworker.registries['track_hash_reg'].update_entry(identifier=uuid, value=content)
                                self.gitworker.update_index_list(element=uuid)
                                self.gitworker.add_to_index()
                                self.gitworker.update_commit_message(message=f"{uuid}: {content['url']}, beacon gran: {self.apiclient.beacon_gran[objtype]}, track_gran: {self.apiclient.track_gran[objtype]}")
                    if objs_changed > 0:
                        self.gitworker.post_commit(short_commit_message=f'{objtype.capitalize()} update')
                        self.gitworker.push_to_remote_repository()
                        objs_changed = 0
            else:
                logging.info(f"{objtype.capitalize()} tracking disabled in configuration file.")
        except Exception as e:
            raise Exception(f">>> Cannot resolve {objtype}. {e}")

    def main(self):
        try:
            while datetime.now() < datetime.strptime(QUIT_AT, '%Y-%m-%d %H:%M'):
                for identifier in self.trackobjs.keys():
                    self.update_file_index(identifier)
                    self.resolve_mapping(identifier, objtype='world')
                    self.resolve_mapping(identifier, objtype='categories')
                    self.resolve_mapping(identifier, objtype='articles')

                time.sleep(PING_INTERVAL_S)
        except Exception as e:
            logging.error(f"Error in main method: {e}")
            raise Exception(f"Error in main method: {e}")

if __name__=='__main__':
    try:
        wa_secrets = WorldAnvilSecrets(SECRET_PATH, WORLDANVIL_SECRET_SCHEMA)
        gitw = Gitworker(wa_secrets)
        wacli = WAClient(application_key=wa_secrets.application_key,
                        authentication_token=wa_secrets.authentication_token)

        owner_uuid = wacli.get_auth_user_id()['id']
        worlds_uuid_url_mapping = { _world['url']: _world['id'] for _world in wacli.get_user_worlds(uuid=owner_uuid)}

        trackobjs = { worlds_uuid_url_mapping[_world['url']]: TrackWorld(owner_uuid,
                                                                         worlds_uuid_url_mapping[_world['url']],
                                                                         _world['track_changes'],
                                                                         WorldAnvilRelationships()
                                                                         )
                    for _world in wa_secrets.worlds_list }
        track_service = TrackObjectService(gitworker=gitw, trackobjs=trackobjs, apiclient=wacli)
        logging.info(f"TrackObjectService initialized.")
        track_service.main()
        logging.info(f"TrackObjectService main loop finished.")
    except Exception as e:
        logging.error(f"Error in main: {e}")
        raise Exception(f"Error in main: {e}")
    print("End of script.")
