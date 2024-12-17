#
# Process service execution log model class test file.
#
# @author Matthew Casey
#
# (c) Digital Content Analysis Technology Ltd 2022
#

import json
import pytest
import requests
import requests_mock

from tests.custom_test_case import CustomTestCase

from fusion_platform.common.utilities import json_default
from fusion_platform.models.data import Data
from fusion_platform.models.model import Model, ModelError
from fusion_platform.models.process_service_execution_log import ProcessServiceExecutionLog, ProcessServiceExecutionLogSchema
from fusion_platform.session import Session, RequestError


class TestProcessServiceExecutionLog(CustomTestCase):
    """
    Process service execution log model tests.
    """

    def test_init(self):
        """
        Test initialisation of the process execution log model class to ensure no exceptions are raised.
        """
        process_service_execution_log = ProcessServiceExecutionLog(Session())
        self.assertIsNotNone(process_service_execution_log)
        self._logger.info(process_service_execution_log)

    def test_schema(self):
        """
        Tests that a process execution log model can be loaded into the schema.
        """
        with open(self.fixture_path('process_service_execution_log.json'), 'r') as file:
            content = json.loads(file.read())

        model = ProcessServiceExecutionLogSchema().load(content)
        self.assertIsNotNone(model)

        for key in content:
            self.assertEqual(json.dumps(content[key], default=json_default), json.dumps(model[key], default=json_default))
