from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in erpnext_gsg/__init__.py
from erpnext_gsg import __version__ as version

setup(
	name="erpnext_gsg",
	version=version,
	description="Final Project",
	author="aazaqout",
	author_email="aazaqout@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
