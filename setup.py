from setuptools import setup

setup(name='Wirecamel',
      description='Python based project that automate the use of SSLSPlit and generate human readable reports',
      author='Hamza ESSAYEGH',
      author_email='hamza.essayegh@protonmail.com',
      version='1.0',
      packages=['wirecamel', 'wirecamel/lib'],
      data_files=[
          ('/root/.wirecamel/conf', ['wirecamel/conf/hostapd.conf', 'wirecamel/conf/iptables-configuration'])
      ],
      install_requires=[
          'iso8601',
          'tabulate',
          'python-dateutil'
      ],
      entry_points={
          'console_scripts': [
              'wirecamel = wirecamel.__main__:main'
          ]
      },
      )
