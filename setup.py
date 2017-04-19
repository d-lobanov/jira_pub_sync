from setuptools import setup, find_packages

setup(
    name='jira-pub-sync',
    version='1.0',
    packages=find_packages(),
    py_modules=['jira_pub_sync'],
    include_package_data=True,
    install_requires=[
        'click', 'jira'
    ],
    entry_points='''
        [console_scripts]
        jirapub=jira_pub_sync:cli
    ''',
    author="Dmitry Lobanov",
    author_email="dmitry.lobanow@gmail.com",
    description="Tool for JIRAs synchronization.",
)
