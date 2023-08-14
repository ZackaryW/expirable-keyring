
import abc
from typing import Optional
from keyring import credentials
from keyring.backend import KeyringBackend

from ekring.ek import ExpirableKeyringFactory
import os
import toml

script_loc = os.path.dirname(os.path.realpath(__file__))
config_path = os.path.join(script_loc, "ekb.toml")

class ExpirableKeyringBackend(KeyringBackend):
    @abc.abstractproperty
    def priority(cls):
        return 10
    
    def __init__(self):
        self.factory = ExpirableKeyringFactory()

    @staticmethod
    def init(metaname :str, metakey :str, secretkey :str, dateformat :str, prunetype :str):
        with open(config_path, "w") as f:
            options = {
                "META_NAME": metaname,
                "META_KEY": metakey,
                "SECRET_KEY": secretkey,
                "DATE_FORMAT": dateformat,
                "PRUNE_ACTION_TYPE": prunetype
            }

            options = {k:v for k,v in options.items() if v is not None}

            toml.dump(options, f)

    def get_password(self, service: str, username: str) -> str | None:
        return self.factory.get_password(service, username)
    
    def set_password(self, service: str, username: str, password: str) -> None:
        self.factory.set_password(service, username, password)

    def delete_password(self, service: str, username: str) -> None:
        self.factory.delete_password(service, username)

    def get_credential(self, service: str, username: str | None):
        raise NotImplementedError("get_credential not implemented")