#
# Command test file.
#
# @author Matthew Casey
#
# (c) Digital Content Analysis Technology Ltd 2022
#

from mock import patch
import pytest
import sys

from tests.custom_test_case import CustomTestCase

from fusion_platform.command import main


class TestCommand(CustomTestCase):
    """
    Command tests.
    """

    def test_help(self):
        """
        Test help.
        """
        with patch.object(sys, 'argv', ['program', '--help']):
            with pytest.raises(SystemExit):
                main()

    def test_start_help(self):
        """
        Test main entry point to ensure no exceptions are raised.
        """
        with patch.object(sys, 'argv', ['program', 'start', '--help']):
            with pytest.raises(SystemExit):
                main()

    def test_define_help(self):
        """
        Test define help.
        """
        with patch.object(sys, 'argv', ['program', 'define', '--help']):
            with pytest.raises(SystemExit):
                main()

    def test_download_help(self):
        """
        Test download help.
        """
        with patch.object(sys, 'argv', ['program', 'download', '--help']):
            with pytest.raises(SystemExit):
                main()
