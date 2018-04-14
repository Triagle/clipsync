from setuptools import setup

setup(
    name='clipsync',
    version='0.1',
    py_modules=['clipsync'],
    install_requires=['Click', 'pygobject', 'sortedcontainers'],
    entry_points='''
        [console_scripts]
        clipsync=clipsync.clipsync:cli
    ''',
)
