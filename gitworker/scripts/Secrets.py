from Schemas import WORLDANVIL_SECRET_SCHEMA

from cerberus import Validator
import yaml
import logging




class WorldAnvilSecrets:
    def __init__(self, secret_filepath:str=''):
        self.secret_filepath=secret_filepath
        self.initialize_secret_fields()
    def load_secret(self):
        try:
            with open(self.secret_filepath, mode='rt') as secret_file:
                secrets=yaml.load(secret_file, yaml.Loader)
            return secrets
        except Exception as e:
            logging.warning("Unable to load 'secrets' file.")
            raise Exception(f"{e}")
    def validate_secret(self):
        try:
            val=Validator(WORLDANVIL_SECRET_SCHEMA)
            val.validate(self.load_secret())
            return val.errors=={}

        except Exception as e:
            raise Exception(f"{e}")
    def initialize_secret_fields(self):
        try:
            if self.validate_secret():
                wa_secret_map=self.load_secret()['WorldAnvil']
                self.application_key=wa_secret_map['credentials']['application_key']
                self.authentication_token=wa_secret_map['credentials']['authentication_token']
                self.repo_ssh_url=wa_secret_map['remote_repo']['remote_repository_url']
                self.worlds_list=wa_secret_map['track']['worlds']
                
                logging.info("Secrets loaded.")
        except Exception as e:
            logging.warning("Unable to process 'secrets' file.")
            raise Exception(f"{e}")

