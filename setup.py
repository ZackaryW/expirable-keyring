from setuptools import setup, find_packages

setup(
    name="expirable-keyring",
    version="0.1.0",
    description="primarily a cli tool that supports keyring entries with expiration",
    author="Zackary W",
    packages=find_packages(),
    install_requires=[
        "keyring",
        "click",
        "cryptography"
    ],
    entry_points={
        "console_scripts": [
            "ekring = ekring.cli:cli"
        ]
    },
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
)