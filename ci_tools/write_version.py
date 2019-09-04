#  Authors: Sylvain Marie <sylvain.marie@se.com>
#
#  License: BSD 3 clause

from os.path import abspath

import click
from setuptools_scm import get_version


@click.command()
@click.argument('dest_folder')
def write_version(dest_folder):
    file_name = '%s/_version.py' % dest_folder
    print("Writing version to file: %s" % abspath(file_name))
    get_version('.', write_to=file_name)


if __name__ == '__main__':
    write_version()
