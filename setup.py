import setuptools

setuptools.setup(
    name='publitio',
    packages=setuptools.find_packages(),
    version='1.2',
    description='A Python SDK for https://publit.io',
    author='enn michael',
    author_email='enntheprogrammer@gmail.com',
    url='https://github.com/ennmichael/publitio-python-sdk',
    install_requires=['requests'],
    keywords=['publitio']
)
