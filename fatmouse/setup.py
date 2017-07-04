from setuptools import setup, find_packages

description = "FatMouse server"

cfg = dict(
    name="fatmouse-server",
    version=open('version').read().strip(),
    description=description,
    long_description=description,
    author="Scalr Inc.",
    author_email="marat@scalr.com",
    url="https://scalr.net",
    license="GPL",
    platforms="any",
    py_modules=['celeryfile'],
    packages=find_packages('.', include=['common*', 'server*']),
    include_package_data=True
)
setup(**cfg)

