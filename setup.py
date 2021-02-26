import os

from setuptools import setup, find_packages

longDesc = ''
if os.path.exists('README.md'):
    longDesc = open('README.md').read().strip()

version = ''
version_path = os.path.join('botstory', 'version.txt')
if os.path.exists(version_path):
    version = open(version_path).read().strip()

setup(
    name='botstory',
    packages=find_packages(),
    version=version,
    description='Async framework for bots',
    license='MIT',
    long_description=longDesc,
    author='Eugene Krevenets',
    author_email='ievegenii.krevenets@gmail.com',
    url='https://github.com/botstory/bot-story',
    download_url='https://github.com/botstory/bot-story/tarball/{}'.format(version),
    keywords=['bot', 'ai', 'nlp', 'asyncio'],
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'Topic :: Communications :: Chat',

        # Not early because of async/await
        'Programming Language :: Python :: 3.5',
    ],
    install_requires=[
        'aiohttp==3.7.4',
        'motor==1.1',
        'yarl==0.10.0',
    ],
    package_data={
        '': ['*.crt', '*.key', '*.txt']
    },
)
