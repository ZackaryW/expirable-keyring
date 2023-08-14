import os
import click
import toml

from ekring.ek import ExpirableKeyringFactory, NotAnExpirableKey, AlreadyExpiredKey
factory : ExpirableKeyringFactory

script_loc = os.path.dirname(os.path.realpath(__file__))
config_path = os.path.join(script_loc, "ek.toml")

@click.group(invoke_without_command=True)
def cli():
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            toml_dict = toml.load(f)
    else:
        toml_dict = {}

    global factory
    factory = ExpirableKeyringFactory(**toml_dict)

@cli.command()
@click.option("--metaname", default=None)
@click.option("--metakey", default=None)
@click.option("--secretkey", default=None)
@click.option("--dateformat", default=None)
@click.option("--prunetype", default=None, type=click.Choice(["on_startup", "on_execution","task_scheduler"]))
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


@cli.command()
@click.argument('service')
@click.argument('name')
def get(service :str, name :str):
    try:
        res = factory.get_password(service, name)
        if res is None:
            return
        click.echo(res)
    except NotAnExpirableKey:
        click.echo("INVALID")
    except AlreadyExpiredKey:
        click.echo("EXPIRED")
    except Exception as e:
        click.echo("ERROR")
        click.echo(e)

@cli.command()
@click.argument('service')
@click.argument('name')
@click.argument('differs_by', default=None)
def differ(service :str, name :str, differs_by :str):
    try:
        factory.differ_password_expiration(
            service, name, differs_by
        )
    except NotAnExpirableKey:
        click.echo("INVALID")
    except Exception as e:
        click.echo("ERROR")
        click.echo(e)


@cli.command()
@click.argument('service')
@click.argument('name')
@click.argument('password')
@click.argument('expiration')
def set(service :str, name :str, password :str, expiration :str):
    try:
        if "." in expiration and expiration.replace(".", "").isdigit():
            expiration = float(expiration)
        elif expiration.isdigit():
            expiration = int(expiration)
        

        factory.set_password(service, name, password, expiration)
    except Exception as e:
        click.echo("INVALID")
        click.echo(e)


@cli.command()
@click.argument('service')
@click.argument('name')
def delete(service :str, name :str):
    try:
        factory.delete_password(service, name)
    except NotAnExpirableKey:
        click.echo("INVALID")
    except Exception as e:
        click.echo("ERROR")
        click.echo(e)
    
@cli.group()
def secret():
    pass

@secret.command("get")
@click.argument('name')
def get_secret(name :str):
    try:
        res = factory.get_secret(name)
        if res is None:
            return
        click.echo(res)
    except NotAnExpirableKey:
        click.echo("INVALID")
    except AlreadyExpiredKey:
        click.echo("EXPIRED")
    except Exception as e:
        click.echo("ERROR")
        raise e
    
@secret.command("set")
@click.argument('name')
@click.argument('secret')
@click.argument('expiration')
def set_secret(name :str, secret :str, expiration :str) -> None:
    try:
        if "." in expiration and expiration.replace(".", "").isdigit():
            expiration = float(expiration)
        elif expiration.isdigit():
            expiration = int(expiration)
        

        factory.set_secret(name, secret, expiration)
    except Exception as e:
        click.echo("INVALID")
        raise e

@secret.command("delete")
@click.argument('name')
def delete_secret(name :str):
    try:
        factory.delete_secret(name)
    except NotAnExpirableKey:
        click.echo("INVALID")
    except Exception as e:
        click.echo("ERROR")
        raise e
    

if __name__ == "__main__":
    cli()