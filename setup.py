from setuptools import setup

setup(
    name='jira-pub-sync',
    version='1.0',
    packages=['src'],
    include_package_data=True,
    install_requires=[
        'click', 'jira'
    ],
    entry_points='''
        [console_scripts]
        pub=pub_sync:cli
    ''',
)
