import setuptools

setuptools.setup(
    name='publitio',
    packages=setuptools.find_packages(),
    version='1.3.0',
    description='A Python SDK for https://publit.io',
    author='Enn Michael',
    author_email='enntheprogrammer@gmail.com',
    url='https://github.com/ennmichael/publitio-python-sdk',
    install_requires=['requests'],
    keywords=['publitio'],
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent'
    ]
)
