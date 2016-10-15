import os

from setuptools import setup, find_packages

longDesc = ""
if os.path.exists("README.md"):
    longDesc = open("README.md").read().strip()

setup(
    name='botstory',
    packages=find_packages(),
    version='0.0.11',
    description='Async framework for bots',
    license='MIT',
    long_description=longDesc,
    author='Eugene Krevenets',
    author_email='ievegenii.krevenets@gmail.com',
    url='https://github.com/hyzhak/bot-story',
    download_url='https://github.com/hyzhak/bot-story/tarball/0.0.1',
    keywords=['bot', 'ai', 'nlp', 'asyncio'],
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'Topic :: Communications :: Chat',

        # Not early because of async/await
        'Programming Language :: Python :: 3.5',
    ],
    install_requires=[
        'aiohttp==1.0.5',
        'motor==0.7b0',
        'yarl==0.4.3',
    ],
)
