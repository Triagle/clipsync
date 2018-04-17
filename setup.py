from setuptools import setup

setup(
    name='clipsync',
    version='0.1',
    packages=['clipsync'],
    install_requires=['Click', 'pygobject', 'sortedcontainers'],
    entry_points={"console_scripts": ['clipsync = clipsync.cli:cli']},
)
