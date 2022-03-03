#
# Base class test file.
#
# @author Matthew Casey
#
# (c) Digital Content Analysis Technology Ltd 2022
#

from tests.custom_test_case import CustomTestCase

from fusion_platform.base import Base


class TestBase(CustomTestCase):
    """
    Base tests.
    """

    def test_init(self):
        """
        Test initialisation of the class to ensure no exceptions are raised.
        """
        Base()

    def test_main(self):
        """
        Test main entry point to ensure no exceptions are raised.
        """
        Base.main()
