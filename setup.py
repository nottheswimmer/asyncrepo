from distutils.core import setup

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='asyncrepo',
    version='0.0.8',
    description='A library for providing a unified asyncio API for various data sources',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Michael Phelps',
    author_email='michaelphelps@nottheswimmer.org',
    url='https://github.com/nottheswimmer/asyncrepo',
    packages=['asyncrepo'],
    install_requires=requirements,
    license='MIT',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
