import os
import json
import time
import yaml
from datetime import datetime
from  pywaclient.api import BoromirApiClient
import git
from hashlib import sha1

SCRIPT_NAME='gitworker.py'
MAGPY_REPO_URL='https://github.com/Arghantyr/MagPy'
VERSION='0.1'
SSH_ID_FILE='/home/gitworker/.ssh/id_rsa'
REPO_PATH='/home/gitworker/repo'
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
        except Exception as e:
            raise Exceptions(f"{e}")


class Gitworker:
    def __init__(self, secret_obj:Secrets=None):
        self.load_secret(secret_obj)
        self.load_repo()
        self.validate_repo_settings()
        self.initiate_commit_backend()
    def load_secret(self, secret_obj:Secrets=None):
        try:
            self.repo_ssh_url=secret_obj.repo_ssh_url
        except Exception as e:
            raise Exceptions(f"{e}")
    def load_repo(self):
        try:
            self.remote_repo_name=self.repo_ssh_url.rstrip('.git').split('/')[-1]
            self.repo=git.Repo(f"{REPO_PATH}/{self.remote_repo_name}")
        except Exception as e:
            raise Exception(f"{e}")
    def validate_repo_settings(self):
        try:
            remote_repo_set=self.repo.remote('github-repo').exists()
            if remote_repo_set:
                self.remote=self.repo.remote('github-repo')
            self.repo.heads['main'].checkout()
        except Exception as e:
            raise Exception(f"{e}")
    def initiate_commit_backend(self):
        try:
            self.commit_message=""
            self.index_list=['hash_reg']
            pass
        except Exception as e:
            raise Exception(f"{e}")

    # Metadata and supporting functions
    def get_uuid_objhash(self, uuid:str="00000000-0000-0000-0000-000000000000", content:str="{}"):
        try:
            obj_hash=sha1(json.dumps(content, ensure_ascii=False).encode('utf-8')).hexdigest()
            return uuid, obj_hash
        except Exception as e:
            raise Exception(f"{e}")

    # Index list section
    def update_index_list(self, element:str=''):
        try:
            if element != '':
                self.index_list.append(element)
            else:
                raise Exception(f"Invalid element value. Index update aborted.")
        except Exception as e:
            raise Exception(f"{e}")
    def add_to_index(self):
        try:
            self.repo.index.add(self.index_list)
        except Exception as e:
            raise Exception(f"{e}")

    # Commit section
    def update_commit_message(self, message:str=""):
        try:
            self.commit_message += ''.join([message, '\n'])
        except Exception as e:
            raise Exception(f"{e}")
    def flush_commit_message(self):
        try:
            self.commit_message=""
        except Exception as e:
            raise Exception(f"{e}")
    def post_commit(self, short_commit_message:str="Object update"):
        try:
            self.repo.index.commit(''.join([short_commit_message,
                                            '\n\n',
                                            self.commit_message])
                                   )
            self.flush_commit_message()
        except Exception as e:
            raise Exception(f"{e}")

    # Stored object section
    def compare_object_hash(self, uuid:str="00000000-0000-0000-0000-000000000000", content:str="{}")->bool:
        try:
            with open(f'{REPO_PATH}/{self.remote_repo_name}/hash_reg', mode='r') as _hash_reg:
                hash_reg=json.load(_hash_reg)
            stored_hash=hash_reg.get(uuid)
            _, current_hash=self.get_uuid_objhash(uuid, content)
            if stored_hash==current_hash:
                return True
            else:
                return False
        except Exception as e:
            raise Exception(f"{e}")
    def update_repo_object(self, uuid:str="00000000-0000-0000-0000-000000000000", new_content:str="{}"):
        try:
            with open(f'{REPO_PATH}/{self.remote_repo_name}/{uuid}', mode='w') as file:
                new_content_str=json.dumps(new_content, indent=2)
                 
                file.write(new_content_str)
        except Exception as e:
            raise Exception(f"{e}") 
    def update_hash_reg(self, uuid:str="00000000-0000-0000-0000-000000000000", new_content:str="{}"):
        try:
            _, object_hash=self.get_uuid_objhash(uuid, new_content)
            with open(f'{REPO_PATH}/{self.remote_repo_name}/hash_reg', mode='r') as _hash_reg:
                hash_reg=json.load(_hash_reg)

            with open(f'{REPO_PATH}/{self.remote_repo_name}/hash_reg', mode='w') as _hash_reg:
                hash_reg[uuid]=object_hash
                json.dump(hash_reg, _hash_reg)
        except Exception as e:
            raise Exception(f"{e}")
    def push_to_remote_repository(self):
        try:
            with self.repo.git.custom_environment(GIT_SSH_COMMAND=f'ssh -i {SSH_ID_FILE}'):
                self.remote.push()
        except Exception as e:
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
        except Exception as e:
            raise Exception(f"{e}")
    def get_auth_user_id(self):
        try:
            return self.client.user.identity()
        except Exception as e:
            raise Exception(f"{e}")
    def get_user_worlds(self, user_id:str=''):
        try:
            return self.client.user.worlds(user_id)
        except Exception as e:
            raise Exception(f"{e}")
    def get_world(self, world_uuid:str='', granularity:int=-1):
        try:
            return self.client.world.get(world_uuid, granularity)
        except Exception as e:
            raise Exception(f"{e}")
    def get_world_categories_mapping(self, world_uuid:str=''):
        try:
            categories = [category['id'] for category in self.client.world.categories(world_uuid)]
            categories.append('-1')
            return {world_uuid: categories}
        except Exception as e:
            raise Exception(f"{e}")
    def get_category_articles_mapping(self, world_uuid:str='', category_uuids:list=[]):
        try:
            articles_mapping={cat_uuid: [art for art in self.client.category.articles(world_uuid, category_uuid)
                                         ] for cat_uuid in category_uuids}
            return articles_mapping
        except Exception as e:
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
        except Exception as e:
            raise Exception(f"{e}")
    def load_auth_user_id(self):
        try:
            self.auth_user_id=self.client.get_auth_user_id()['id']
        except Exception as e:
            raise Exception(f"{e}")
    def load_world_uuid(self):
        try:
            worlds={world['url']: world['id'] for world in self.client.get_user_worlds(self.auth_user_id)}
             
            self.world_uuid=worlds[self.url]
        except Exception as e:
            raise Exception(f"{e}")
    def load_category_mapping(self, track:bool=False):
        try:
            if track:
                self.category_mapping=self.client.get_world_categories_mapping(self.world_uuid)
            else:
                pass
        except Exception as e:
            raise Exception(f"{e}")
    def load_articles_dict(self, track:bool=False):
        try:
            if track:
                category_uuids=self.category_mapping(self.world_uuid)
                self.articles_mapping=self.client.get_category_artcles_mapping(self.world_uuid, category_uuids)
            else:
                pass
        except Exception as e:
            raise Exception(f"{e}") 
    def set_track_granularities(self):
        try:
            self.track_gran={
                    'world': 1,
                    'category': 1,
                    'article': 1
            }
        except Exception as e:
            raise Exception(f"{e}")
    def set_beacon_granularities(self):
        try:
            self.beacon_gran={
                    'world': 0,
                    'category': -1,
                    'article': -1
            }
            assert all([self.beacon_gran[prop] <= self.track_gran[prop] for prop in self.track_gran.keys()]) == True
        except AssertionError:
            raise Exception("Invalid granularity settings. Beacon must be <= than Track.")
        except Exception as e:
            raise Exception(f"{e}")
    def resolve_world(self, gitworker:Gitworker=None):
        try: 
            uuid=self.world_uuid
            beacon=self.client.get_world(uuid, self.beacon_gran['world'])
        
            if not gitworker.compare_object_hash(uuid, beacon):
                content=self.client.get_world(uuid, self.track_gran['world'])
                if not gitworker.compare_object_hash(uuid, content):
                    gitworker.update_repo_object(uuid, content)
                    gitworker.update_hash_reg(uuid, content)
                    gitworker.update_index_list(uuid)
                    gitworker.add_to_index()
                    gitworker.update_commit_message(f"{uuid}: {content['url']}, beacon gran: {self.beacon_gran['world']}, track_gran: {self.track_gran['world']}")

                    gitworker.post_commit(short_commit_message='World update')
                    gitworker.push_to_remote_repository()
                else :
                    pass
        except Exception as e:
            raise Exception(f"{e}")
    def resolve_categories(self, gitworker:Gitworker=None):
        try:
            pass
        except Exception as e:
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
            tr.resolve_world(gitw)
        time.sleep(PING_INTERVAL_S)



if __name__=='__main__':
    main()
    print("End of script.")
