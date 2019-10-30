from setuptools import setup, find_packages

setup(name='raven',
      version='0.1',
      description='Notification framework',
      long_description='A notification framework to standardize notifications and improve readability.',
      url='http://github.com/pravinsingh/raven',
      author='Pravin Singh',
      author_email='pravin.singh@outlook.com',
      license='MIT',
      packages=find_packages(),
      install_requires=[
          'json2html>=1.2.1',
          'markdown2>=2.3.8',
          'requests>=2.19.1'
      ],
      include_package_data=True,
      zip_safe=False)