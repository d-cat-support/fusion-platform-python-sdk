#
# Custom test case class file.
#
# @author Matthew Casey
#
# (c) Digital Content Analysis Technology Ltd 2022
#

import logging
import os

from unittest import TestCase

# Make sure localisation is set up before any SDK-specific imports.
from fusion_platform.localise import Localise

Localise.setup()

import fusion_platform


class CustomTestCase(TestCase):
    """
    Custom test case from which all test classes are descended. Implements custom and common elements for testing.
    """

    # Find the package root directory.
    PACKAGE_DIR = os.path.dirname(os.path.dirname(__file__))

    # Fixtures within the project root.
    FIXTURES_DIR = os.path.join('tests', 'fixtures')

    def __init__(self, methodName):
        """
        Initialises the test case.

        :param methodName: The test method name.
        """
        super().__init__(methodName)

        self._logger = logging.getLogger(fusion_platform.FUSION_PLATFORM_LOGGER)

    @classmethod
    def fixture_path(cls, path):
        """
        Returns the path to a fixture file or directory.

        :param path: The required file or directory.
        :return: The path to the fixture.
        """
        return os.path.join(CustomTestCase.PACKAGE_DIR, CustomTestCase.FIXTURES_DIR, path)
