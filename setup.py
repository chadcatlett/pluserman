#!/usr/bin/python

from setuptools import setup

setup(name="pluserman",
      version="0.0.1",
      description="User Group Homogenization System",
      author="Chad Catlett",
      author_email="chad@catlett.info",
      packages=["pluserman"],
      install_requires=["flask>=0.10"],
      entry_points="""
      [console_scripts]
      pluserman = pluserman.pluserman:main
      """,
     )
