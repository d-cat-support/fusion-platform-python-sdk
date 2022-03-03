#
# Raise thread test file.
#
# @author Matthew Casey
#
# (c) Digital Content Analysis Technology Ltd 2022
#

import pytest

from tests.custom_test_case import CustomTestCase

from fusion_platform.common.raise_thread import RaiseThread


class TestRaiseThread(CustomTestCase):
    def task_error(self):
        raise ValueError

    def task_success(self):
        pass

    def test_thread_error(self):
        """
        Tests that the thread runs and raises an exception.
        """
        thread = RaiseThread(target=self.task_error)
        thread.start()

        with pytest.raises(ValueError):
            thread.join()

    def test_thread_success(self):
        """
        Tests that the thread runs correctly.
        """
        thread = RaiseThread(target=self.task_success)
        thread.start()

        thread.join()
