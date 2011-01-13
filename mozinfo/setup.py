from setuptools import setup, find_packages

version = '0.1'

setup(name='mozinfo',
      version=version,
      description="file for interface to transform introspected system information to a format pallatable to Mozilla",
      long_description='',
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Jeff Hammel',
      author_email='jhammel@mozilla.com',
      url='https://wiki.mozilla.org/Auto-tools',
      license='MPL',
      py_modules=['mozinfo'],
      packages=[],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      [console_scripts]
      mozinfo = mozinfo:main
      """,
      )