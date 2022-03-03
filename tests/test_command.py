#
# Command test file.
#
# @author Matthew Casey
#
# (c) Digital Content Analysis Technology Ltd 2022
#

from tests.custom_test_case import CustomTestCase

from fusion_platform.command import fusion_platform


class TestCommand(CustomTestCase):
    """
    Command tests.
    """

    def test_fusion_platform(self):
        """
        Test main entry point to ensure no exceptions are raised.
        """
        fusion_platform()
