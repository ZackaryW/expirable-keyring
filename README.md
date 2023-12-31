# expirable-keyring

## Disclaimer 
first of all, I don't really think this is a good idea and this project is born for the sake of curiosity.

## What is this?
This is an extension to the keyring implementation that allows you to set an expiration date

## How to install?
install using github source
```bash
pip install git+https://github.com/ZackaryW/expirable-keyring.git@stable#egg=expirable-keyring
```

## How is it implemented?
- there exists a meta key that keeps a map of all the expirable-keys, their expiration date and encryption password
- to maintain a low footprint, all expiration dates that isn't today will trim off the time part

## How to use it?
```python
from ekring import ExpirableKeyringFactory

factory = ExpirableKeyringFactory()
factory.set_password('service', 'username', 'password', expire_date='2020-01-01') # will trigger an error
factory.get_password('service', 'username') # will raise NotAnExpiredKey

factory.set_password('service', 'username', 'password', expire_date="in 2 days")
factory.get_password('service', 'username') # will return 'password'
```

### CLI Usage
```bash
ekring set service username password "in 2 days"
ekring get service username
ekring secret set username password "in 2 days"
ekring secret get username
ekring differ service username "in 3 days"
ekring delete service username
```


```