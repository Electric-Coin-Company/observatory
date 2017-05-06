# -lr/usr/bin/env python3
# -*- coding: utf-8 -*-
from setuptools import setup
import os
import re

REQUIREMENTS = [pkg.strip() for pkg in open("requirements.txt").readlines()]
long_description = open("README.md").read()

def file_list(path):
    files = []
    subdirs = [subdir[0] for subdir in os.walk(path)]
    regex = re.compile('.*\/.git\/.*')
    for filename in os.listdir(path):
        if os.path.isfile(os.path.join(path, filename)):
            files.append(os.path.join(path, filename))
    for subdir in subdirs:
        for filename in os.listdir(subdir):
            if os.path.isfile(os.path.join(subdir, filename)):
                files.append(os.path.join(subdir, filename))
    filtered = [x for x in files if not regex.match(x)]
    return list(set(filtered))

setup(
    name="zcash-block-observatory",
    version="0.1.0",
    description="Zcash Block Observatory",
    license="MIT",
    author="Zcash Company",
    author_email="sysadmin@z.cash",
    url="https://github.com/ageis/zcash-block-observatory",
    packages=['zcash-block-observatory'],
    keywords='Zcash, cryptocurrency, Bitcoin, blocks, Zerocoin',
    install_requires=REQUIREMENTS,
    long_description=long_description,
    data_files=file_list(os.getcwd()),
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
   ]
)
