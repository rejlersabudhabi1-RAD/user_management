"""
Setup configuration for RAD User Management package.
"""
from setuptools import setup, find_packages
import os

# Read README for long description
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

# Read requirements
with open('requirements.txt', 'r', encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='rad-user-management',
    version='1.0.0',
    author='Rejlers Abu Dhabi',
    author_email='development@rejlers.ae',
    description='Comprehensive User Management system for Django with authentication, RBAC, and activity tracking',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/rejlersabudhabi1-RAD/user_management',
    packages=find_packages(exclude=['tests*', 'docs*']),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Framework :: Django',
        'Framework :: Django :: 4.0',
        'Framework :: Django :: 4.1',
        'Framework :: Django :: 4.2',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'License :: Other/Proprietary License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet :: WWW/HTTP',
    ],
    python_requires='>=3.9',
    install_requires=requirements,
    include_package_data=True,
    zip_safe=False,
    keywords='django user-management authentication authorization rbac jwt',
    project_urls={
        'Bug Reports': 'https://github.com/rejlersabudhabi1-RAD/user_management/issues',
        'Source': 'https://github.com/rejlersabudhabi1-RAD/user_management',
        'Documentation': 'https://github.com/rejlersabudhabi1-RAD/user_management/blob/main/README.md',
    },
)
