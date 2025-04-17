import json
import logging

import Utils


class Registry:
    def __init__(self, reg_dir_filepath:str, reg_name:str):
        self.reg_name=reg_name
        self.reg_dir_filepath=f"{reg_dir_filepath}/{reg_name}"

    def get_registry(self):
        try:
            with open(self.reg_dir_filepath, mode='r') as _reg:
                reg=json.load(_reg)
            return reg
        except Exception as e:
            raise Exception(f"{e}")

    def update_registry(self, value:dict):
        try:
            reg=self.get_registry()
            reg.update(value)
            with open(self.reg_dir_filepath, mode='w') as _reg:
                json.dump(reg, _reg)
            logging.info(f"Updated registry: {self.reg_name} with new data: {json.dumps(value, indent=2)}")
        except Exception as e:
            raise Exception(f"{e}")

    def get_entry(self, identifier:str):
        try:
            return self.get_registry()[identifier]
        except Exception as e:
            raise Exception(f"{e}")

    def update_entry(self, identifier:str, value:dict):
        try:
            reg=self.get_registry()
            hashed_value=Utils.get_hash(json.dumps(value, ensure_ascii=False))
            if isinstance(value, dict):
                reg[identifier]=hashed_value
            else:
                raise TypeError(f"Invalid type for 'value'.")
            with open(self.reg_dir_filepath, mode='w') as _reg:
                json.dump(reg, _reg) 

            logging.info(f"{self.reg_name.capitalize()} registry updated for {identifier}: {hashed_value}.")
        except Exception as e:
            logging.warning(f"Unable to modify {reg_type} hash registry.")
            raise Exception(f"{e}")

    def compare_against_registry(self, value:dict):
        try:
            stored_reg=self.get_registry()
            stored_reg_hash=Utils.get_hash(json.dumps(stored_reg, ensure_ascii=False))
            compared_reg_hash=Utils.get_hash(json.dumps(value, ensure_ascii=False))
            logging.info(f'Calculated hash ({stored_reg_hash}) for stringified registry object: {stored_reg}')

            comp_result=(stored_reg_hash == compared_reg_hash)
            logging.info(f"Comparing hash for registry: {self.reg_name}. Stored: {stored_reg_hash}, current: {compared_reg_hash} with result: {comp_result}")
            return comp_result
        except Exception as e:
            logging.warning(f"Unable to compare 'value' against the stored registry.")
            raise Exception(f"{e}")

    def compare_against_entry(self, identifier:str, value:dict):
        try:
            stored_reg_entry_hash=self.get_registry()[identifier]
            compared_value_hash=Utils.get_hash(json.dumps(value, ensure_ascii=False))

            comp_result=(stored_reg_entry_hash == compared_value_hash)
            logging.info(f"Comparing hash for registry: {self.reg_name} with ID: {identifier}. Stored: {stored_reg_entry_hash}, current: {compared_value_hash} with result: {comp_result}")
            return comp_result
        except Exception as e:
            logging.warning(f"Unable to compare an 'entry' for id: {identifier} between stored and current 'value'")
            raise Exception(f"{e}")



