#
# Raise thread class file.
#
# @author Matthew Casey
#
# (c) Digital Content Analysis Technology Ltd 2022
#

from threading import Thread


class RaiseThread(Thread):
    """
    Custom thread class used to make sure exceptions are raised on join. Based on:
    https://www.geeksforgeeks.org/handling-a-threads-exception-in-the-caller-thread-in-python/
    """

    def join(self, timeout=None):
        """
        Wait until the thread terminates or the timeout occurs.

        :param timeout: The amount of time to wait until the thread has terminated. Using None will bock indefinitely.
        """
        super(RaiseThread, self).join(timeout)

        # Make sure any exception is re-raised in the calling thread.
        if self.__error is not None:
            raise self.__error

    def run(self):
        """
        Runs the thread operation, but catches any error so that it can be re-raised on join.
        """
        self.__error = None

        try:
            super(RaiseThread, self).run()
        except Exception as e:
            self.__error = e
