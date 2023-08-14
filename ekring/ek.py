from dataclasses import dataclass, field
import datetime
import typing
from ekring.os_kr import (
    delete_password, get_password, has_password, set_password
)
import json
from ekring.password import password_decrypt, password_encrypt, password_encrypt_with_gen
from ekring.utils import (
    default_counter,
    parse_date_info
)

class NotAnExpirableKey(Exception):
    pass

class AlreadyExpiredKey(Exception):
    pass

class ExpirableKeyringMeta:
    _factory : "ExpirableKeyringFactory"
    pairs : typing.Dict[str, typing.Tuple[str, typing.List[str]]]

    def __init__(self, factory : "ExpirableKeyringFactory"):
        self._factory = factory
        self._fetch_pairs()

    def _fetch_pairs(self):
        raw = get_password(self._factory.META_KEY, self._factory.META_NAME)        
        if raw is None:
            self.pairs = {}
            return

        self.pairs = json.loads(raw)

    def __contains__(self, key : str):
        return key in self.pairs    
    
    def has_username(self, username : str):
        for v in self.pairs.values():
            if username in v[1]:
                return True
        return False
    
    def get_encryption_key(self, key : str):
        return self.pairs[key][0]
    
    def set_user(self, key : str, username : str):
        if key not in self.pairs:
            raise ValueError("encryption key must be set before setting username")
    
        self.pairs[key][1].append(username)

    def set_encryption_key(self, key :str, encryption_key : str):
        if key not in self.pairs:
            self.pairs[key] = [encryption_key, []]
        else:
            raise ValueError("encryption key already set")
    
    def _has_meta(self):
        return has_password(self._factory.META_KEY, self._factory.META_NAME)

    def update_meta(self):
        set_password(self._factory.META_KEY, self._factory.META_NAME, json.dumps(self.pairs))

    def delete_user(self, username :str):
        for date_str, (_, usernames) in self.pairs.items():
            if username in usernames:
                usernames.remove(username)
                if len(usernames) == 0:
                    del self.pairs[date_str]
                break
@dataclass
class ExpirableKeyringFactory:
    META_NAME : str = field(default_factory=lambda : "EKR_META_" + str(default_counter()))
    META_KEY : str = "EKR_META"
    SECRET_KEY : str = "EKR_SECRETS"
    #"YYYYMMDDHHMMSS"
    DATE_FORMAT : str = "%Y%m%d%H%M%S"
    PRUNE_ACTION_TYPE : typing.Literal["on_startup", "on_execution","task_scheduler"] = "on_execution"
    meta : ExpirableKeyringMeta = field(init=False)

    def __post_init__(self):
        if self.PRUNE_ACTION_TYPE == "task_scheduler":
            raise NotImplementedError("task_scheduler not implemented yet")

        self.meta = ExpirableKeyringMeta(self)

        if self.PRUNE_ACTION_TYPE == "on_startup":
            self.prune_expired()

    @staticmethod
    def ensure_bypass_20_limit():
        raise NotImplementedError("ensure_bypass_20_limit not implemented yet")

    def prune_expired(self):
        for date_str in self.meta.pairs.keys():
            date_parsed = datetime.datetime.strptime(date_str, self.DATE_FORMAT)
            if date_parsed < datetime.datetime.now():
                pending_to_delete_usernames = self.meta.pairs[date_str][1]
                for username in pending_to_delete_usernames:
                    delete_password(self.NORMAL_KEY.format(name=username), username)
                del self.meta.pairs[date_str]
        self.meta.update_meta()

    def prune_if_expired(self, datestr : str):
        date_parsed = datetime.datetime.strptime(datestr, self.DATE_FORMAT)
        if date_parsed >= datetime.datetime.now():
            return False
        
        pending_to_delete_usernames = self.meta.pairs[datestr][1]
        for username in pending_to_delete_usernames:
            delete_password(self.SECRET_KEY.format(name=username), username)
        del self.meta.pairs[datestr]
        self.meta.update_meta()
        return True

    def set_password(
        self,
        service : str,
        username : str,
        password : str,
        expiration_date : typing.Union[str, int, float, datetime.timedelta, datetime.datetime]
    ):
        target_date = parse_date_info(expiration_date)
        date_str = target_date.strftime(self.DATE_FORMAT)

        # if date already passed
        if target_date < datetime.datetime.now():
            raise AlreadyExpiredKey("expiration date already passed")

        if date_str in self.meta:
            encryption_key = self.meta.get_encryption_key(date_str)
            encrypted_content = password_encrypt(password.encode(), encryption_key)
            self.meta.set_user(date_str, username)
        else:
            encrypted_content, encryption_key = password_encrypt_with_gen(password)
            self.meta.set_encryption_key(date_str, encryption_key)
            self.meta.set_user(date_str, username)

        set_password(service, username, encrypted_content)

    def get_password(
        self, 
        service : str,
        username : str
    ):
        for date_str, (encryption_key, usernames) in self.meta.pairs.items():
            if username not in usernames:
                continue
            
            if self.prune_if_expired(date_str):
                raise AlreadyExpiredKey(f"username {username} already expired")
            
            encrypted_content = get_password(service, username)
            if encrypted_content is None:
                return None

            decrypted = password_decrypt(encrypted_content, encryption_key)
            return decrypted

        raise NotAnExpirableKey(f"username {username} not found")
    
    def set_secret(
        self,
        name : str,
        secret : str,
        expiration_date : typing.Union[str, int, float, datetime.timedelta, datetime.datetime]
    ):
        self.set_password(self.SECRET_KEY, name, secret, expiration_date)
    
    def get_secret(
        self,
        name : str
    ):
        return self.get_password(self.SECRET_KEY, name)
    
    def delete_secret(
        self,
        name : str
    ):
        self.delete_password(self.SECRET_KEY, name)

    def delete_password(
        self,
        username : str
    ):
        if not self.meta.has_username(username):
            raise NotAnExpirableKey(f"username {username} not found")
        
        delete_password(self.SECRET_KEY.format(name=username), username)
        self.meta.delete_user(username)

    def purge_all(
        self
    ):
        for datestr, (_, usernames) in self.meta.pairs.items():
            for username in usernames:
                delete_password(self.SECRET_KEY.format(name=username), username)

        delete_password(self.META_KEY, self.META_NAME)