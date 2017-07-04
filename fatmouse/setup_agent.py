import os
import platform

from setuptools import setup, find_packages

description = "FatMouse agent (replaces Scalarizr)"


def make_data_files(dst, src):
    ret = []
    for directory, _, files in os.walk(src):
        if not directory.startswith("."):
            ret.append([
                directory.replace(src, dst),
                list(os.path.abspath(os.path.join(directory, f)) for f in files)
            ])
    return ret


def abspath_join(*args):
    return os.path.abspath(os.path.join(*args))


if platform.system() == 'Windows':
    install_dir = abspath_join(os.environ.get('INSTALL_DIR', os.environ.get('OMNIBUS_INSTALL_DIR')),
                               os.environ.get('OMNIBUS_BUILD_VERSION', os.environ.get('OMNIBUS_VERSION')))
else:
    install_dir = os.environ.get('INSTALL_DIR', os.environ.get('OMNIBUS_INSTALL_DIR'))

if not install_dir or 'None' in install_dir:
    raise AttributeError(
        'This setup file is designed to operate inside ci-omnibus build environment.\n'
        'It requires build version being set as OMNIBUS_BUILD_VERSION or OMNIBUS_VERSION envvars\n'
        'And project installation directory being set as INSTALL_DIR or OMNIBUS_INSTALL_DIR envvar')

data_files = make_data_files(abspath_join(install_dir, 'init'), 'init')
data_files.append([abspath_join(install_dir, 'etc'), ['docker/rabbitmq/fatmouse-ca/cacert.pem']])


cfg = dict(
    name="fatmouse-agent",
    version=open('version').read().strip(),
    description=description,
    long_description=description,
    author="Scalr Inc.",
    author_email="info@scalr.com",
    url="https://scalr.net",
    license="GPL",
    platforms="any",
    data_files=data_files,
    packages=find_packages('.', include=['common*', 'agent*']),
    package_data={'agent.tasks': ['downgrade_blacklist.json', 'hosts.aug']},
    include_package_data=True
)
setup(**cfg)
