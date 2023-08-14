import os

OS = os.name
DEFAULT_KEYRING = None
if OS == "nt":
    from keyring.backends.Windows import WinVaultKeyring
    DEFAULT_KEYRING = WinVaultKeyring()
#linux
elif OS == "posix":
    from keyring.backends.SecretService import Keyring
    DEFAULT_KEYRING = Keyring()
#mac
elif OS == "mac":
    from keyring.backends.OS_X import Keyring
    DEFAULT_KEYRING = Keyring()
else:
    raise NotImplementedError("Unsupported OS")

def get_password(service_name : str, username : str):
    return DEFAULT_KEYRING.get_password(service_name, username)

def set_password(service_name : str, username : str, password : str):
    DEFAULT_KEYRING.set_password(service_name, username, password)

def delete_password(service_name : str, username : str):
    try:
        DEFAULT_KEYRING.delete_password(service_name, username)
    except: # noqa
        pass

def has_password(service_name : str, username : str):
    try:
        res = DEFAULT_KEYRING.get_password(service_name, username)
        return res is not None
    except: # noqa
        return False    


__all__ = ["DEFAULT_KEYRING", "get_password", "set_password", "delete_password", "has_password"]

