#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2018/2/27 14:15
# @Author  : CKHo
# @Email   : ckhoidea@hotmail.com
# @File    : setup.py.py
# @Software: PyCharm


from setuptools import setup, find_packages
setup(
    name='Strategy',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=['requests',
                      'bs4',
                      'tushare',
                      'retrying',
                      'requests',
                      'lxml',
                      'selenium',
                      'bosonnlp',
                      'baidu-aip'
                      ],

    description='The functions for trading',
    author='Hochikong',
    author_email='ckhoidea@hotmail.com',
    url='http://github.com/hochikong'
)