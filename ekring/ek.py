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
    date_encryption : typing.Dict[str, str]
    name_dates : typing.Dict[str, str]
    _cached_dates : typing.Dict[str, datetime.datetime]

    def __init__(self, factory : "ExpirableKeyringFactory"):
        self._factory = factory
        self._cached_dates = {}
        self._fetch_pairs()

    def _fetch_pairs(self):
        raw = get_password(self._factory.META_KEY, self._factory.META_NAME)        
        if raw is None:
            self.date_encryption = {}
            self.name_dates = {}
            return

        json_raw = json.loads(raw)
        self.date_encryption = json_raw["date_encryption"]
        self.name_dates = json_raw["name_dates"]

    def has_username(self, service : str, username : str):
        return f"{service}|{username}" in self.name_dates
    
    def has_date(self, date_str : str):
        return date_str in self.date_encryption

    def get_encryption_key(self, datestr : str):
        return self.date_encryption[datestr]
    
    def set_user(self, datestr : str, service : str, username : str):
        if "|" in username:
            raise ValueError("username cannot contain | character")
    
        if "|" in service:
            raise ValueError("service cannot contain | character")

        name = f"{service}|{username}"

        if datestr not in self.date_encryption:
            raise ValueError("date not found")
        
        self.name_dates[name] = datestr

    def set_encryption_key(self, datestr :str, encryption_key : str):
        if datestr in self.date_encryption:
            raise ValueError("date already exists")
        
        self.date_encryption[datestr] = encryption_key
    
    def _has_meta(self):
        return has_password(self._factory.META_KEY, self._factory.META_NAME)

    def update_meta(self):
        set_password(self._factory.META_KEY, self._factory.META_NAME, json.dumps(
            {
                "date_encryption" : self.date_encryption,
                "name_dates" : self.name_dates
            }
        ))

    def delete_entry(self, service : str, username : str, skipCheckDateEncrypted : bool = False):
        name = f"{service}|{username}"
        if name not in self.name_dates:
            raise ValueError("entry not found")
        
        date_str = self.name_dates[name]
        del self.name_dates[name]
        if skipCheckDateEncrypted and date_str not in self.name_dates.values():
            del self.date_encryption[date_str]

        self.update_meta()

    def delete_date(self, datestr :str):
        if datestr not in self.date_encryption:
            raise ValueError("date not found")

        del self.date_encryption[datestr]
        self.name_dates = {k : v for k, v in self.name_dates.items() if v != datestr}
        self.update_meta()

    def yield_dates(self):
        for name, datestr in self.name_dates.items():
            svc, username = name.split("|", 1)
            if datestr not in self._cached_dates:
                date_parsed = datetime.datetime.strptime(datestr, self._factory.DATE_FORMAT)
                self._cached_dates[datestr]: datetime.datetime = date_parsed

            yield datestr, self._cached_dates[datestr], svc, username

    def yield_expired(self):
        for datestr, date_parsed, svc, username in self.yield_dates():
            if date_parsed < datetime.datetime.now():
                yield datestr, date_parsed, svc, username

    def yield_items(self):
        for name, datestr in self.name_dates.items():
            svc , username = name.split("|", 1)
            yield svc, username, datestr, self.date_encryption[datestr]



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
        expired_datestr = []
        for datestr, _, svc, username in self.meta.yield_expired():
            self.meta.delete_entry(svc, username)
            delete_password(svc, username)
            if datestr not in expired_datestr:
                expired_datestr.append(datestr)
        
        self.meta.update_meta()


    def prune_if_expired(self, datestr : str):
        date_parsed = datetime.datetime.strptime(datestr, self.DATE_FORMAT)
        if date_parsed >= datetime.datetime.now():
            return False
        
        self.meta.delete_date(datestr)
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

        if self.meta.has_date(date_str):
            encryption_key = self.meta.get_encryption_key(date_str)
            encrypted_content = password_encrypt(password.encode(), encryption_key)
            self.meta.set_user(date_str,service, username)
        else:
            encrypted_content, encryption_key = password_encrypt_with_gen(password)
            self.meta.set_encryption_key(date_str, encryption_key)
            self.meta.set_user(date_str,service, username)
            
        set_password(service, username, encrypted_content)
        self.meta.update_meta()

    def get_password(
        self, 
        service : str,
        username : str
    ):
        if not self.meta.has_username(service, username):
            raise NotAnExpirableKey(f"{service}:{username} not found")

        datestr = self.meta.name_dates[f"{service}|{username}"]

        if self.prune_if_expired(datestr):
            raise AlreadyExpiredKey(f"{service}:{username} already expired")
    
        encrypted_content = get_password(service, username)
        if encrypted_content is None:
            return None

        encryption_key = self.meta.get_encryption_key(datestr)
        decrypted = password_decrypt(encrypted_content, encryption_key)
        return decrypted
    
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
        service : str,
        username : str
    ):
        if not self.meta.has_username(username):
            raise NotAnExpirableKey(f"username {username} not found")
        
        delete_password(service, username)
        self.meta.delete_entry(service, username)

    def purge_all(
        self
    ):
        for date_str, _, svc, username in self.meta.yield_dates():
            delete_password(svc, username)
            self.meta.delete_date(date_str)
        self.meta.update_meta()
    
    def differ_password_expiration(
        self, 
        service : str,
        username : str,
        expiration_date : typing.Union[str, int, float, datetime.timedelta, datetime.datetime]
    ):
        if not self.meta.has_username(service, username):
            raise NotAnExpirableKey(f"{service}:{username} not found")

        original_datestr = self.meta.name_dates[f"{service}|{username}"]
        target_date = parse_date_info(expiration_date)
        target_date_str = target_date.strftime(self.DATE_FORMAT)
        
        # check if only 1 datestr in meta
        if self.meta.name_dates.values().count(original_datestr) == 1:
            self.meta.name_dates[f"{service}|{username}"] = target_date_str
            self.meta.update_meta()
        else:
            # if more than 1 datestr in meta, create new entry
            self.set_password(
                service,
                username,
                self.get_password(service, username),
                target_date
            )
            