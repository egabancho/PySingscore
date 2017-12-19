from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='singscore',
      version='0.1',
      description='The funniest joke in the world',
      url='http://github.com/kristyhoran/singscore',
      author='Kristy Horan',
      author_email='kristyhoran15@gmail.com',
      license='MIT',
      packages=['singscore'],
      install_requires=[
          'pandas', 'sys', 'os', 'numpy','matplotlib', 'matplotlib.pyplot',
          'itertools','seaborn', 'scipy', 'scipy.stats',
          'matplotlib.gridspec','matplotlib.lines','matplotlib.patches',
      ],
      zip_safe=False)