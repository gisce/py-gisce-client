from setuptools import setup, find_packages

setup(
    name='pygisceclient',
    description='Python client to access the GISCE ERP',
    author='GISCE',
    author_email='devel@gisce.net',
    url='https://github.com/gisce/py-gisce-client',
    version='0.7.0',
    license='General Public Licence 2',
    long_description='''py-gisce-client is a Python client to access the GISCE ERP''',
    provides=['pygisceclient'],
    install_requires=[
        'requests'
    ],
    tests_require=[
        'pytest',
        'requests',
        'responses'
    ],
    packages=find_packages()
)
