#
# Process service execution model class test file.
#
# @author Matthew Casey
#
# (c) Digital Content Analysis Technology Ltd 2022
#

import json
import os
import pytest
import requests
import requests_mock
import tempfile

from tests.custom_test_case import CustomTestCase

from fusion_platform.common.utilities import json_default
from fusion_platform.models.data import Data
from fusion_platform.models.model import Model, ModelError
from fusion_platform.models.process_service_execution import ProcessServiceExecution, ProcessServiceExecutionSchema
from fusion_platform.models.process_service_execution_log import ProcessServiceExecutionLog
from fusion_platform.session import Session, RequestError


class TestProcessServiceExecution(CustomTestCase):
    """
    Process service execution model tests.
    """

    def test_init(self):
        """
        Test initialisation of the process execution model class to ensure no exceptions are raised.
        """
        process_service_execution = ProcessServiceExecution(Session())
        self.assertIsNotNone(process_service_execution)

    def test_download_log_file(self):
        """
        Tests that the log file from a process service execution can be downloaded.
        """
        with open(self.fixture_path('process_service_execution.json'), 'r') as file:
            process_service_execution_content = json.loads(file.read())

        with open(self.fixture_path('process_service_execution_log.json'), 'r') as file:
            process_service_execution_log_content = json.loads(file.read())

        session = Session()
        organisation_id = process_service_execution_content.get('organisation_id')
        process_service_execution_id = process_service_execution_content.get(Model._FIELD_ID)
        path = ProcessServiceExecution._PATH_LOGS.format(organisation_id=organisation_id, process_service_execution_id=process_service_execution_id)

        process_service_execution = ProcessServiceExecution(session)
        self.assertIsNotNone(process_service_execution)

        with requests_mock.Mocker() as mock:
            mock.get(
                f"{Session.API_URL_DEFAULT}{ProcessServiceExecution._PATH_GET.format(organisation_id=organisation_id, process_service_execution_id=process_service_execution_id)}",
                text=json.dumps({Model._RESPONSE_KEY_MODEL: process_service_execution_content}))
            process_service_execution.get(organisation_id=organisation_id, process_service_execution_id=process_service_execution_id)
            self.assertIsNotNone(process_service_execution)
            self.assertEqual(str(process_service_execution_id), str(process_service_execution.id))

            with tempfile.TemporaryDirectory() as dir:
                destination = os.path.join(dir, 'log.txt')

                with pytest.raises(RequestError):
                    mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                    process_service_execution.download_log_file(destination)

                with pytest.raises(RequestError):
                    mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                    process_service_execution.download_log_file(destination)

                mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [process_service_execution_log_content]}))

                self.assertFalse(os.path.exists(destination))
                process_service_execution.download_log_file(destination)
                self.assertTrue(os.path.exists(destination))

                with open(destination, 'r') as file:
                    lines = file.readlines()

                self.assertIsNotNone(lines)

                process_service_execution_log = ProcessServiceExecutionLog(session)
                process_service_execution_log._set_model(process_service_execution_log_content)
                first = True

                header, csv = process_service_execution_log.to_csv(exclude=['id', 'created_at', 'updated_at', 'process_service_execution_id'])

                for line in lines:
                    if first:
                        self.assertEqual(f"{header}\n", line)
                        first = False
                    else:
                        self.assertEqual(f"{csv}\n", line)

    def test_get(self):
        """
        Tests that an object can be retrieved from the API.
        """
        with open(self.fixture_path('process_service_execution.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get('organisation_id')
        process_service_execution_id = content.get(Model._FIELD_ID)
        path = ProcessServiceExecution._PATH_GET.format(organisation_id=organisation_id, process_service_execution_id=process_service_execution_id)

        process_service_execution = ProcessServiceExecution(session)
        self.assertIsNotNone(process_service_execution)

        with requests_mock.Mocker() as mock:
            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                process_service_execution.get(organisation_id=organisation_id, process_service_execution_id=process_service_execution_id)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                process_service_execution.get(organisation_id=organisation_id, process_service_execution_id=process_service_execution_id)

            with pytest.raises(ModelError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                process_service_execution.get(organisation_id=organisation_id, process_service_execution_id=process_service_execution_id)

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            process_service_execution.get(organisation_id=organisation_id, process_service_execution_id=process_service_execution_id)
            self.assertIsNotNone(process_service_execution)
            self.assertEqual(str(process_service_execution_id), str(process_service_execution.id))

            process_service_execution.get()
            self.assertIsNotNone(process_service_execution)
            self.assertEqual(str(process_service_execution_id), str(process_service_execution.id))

    def test_inputs(self):
        """
        Tests that inputs can be obtained from a model.
        """
        with open(self.fixture_path('process_service_execution.json'), 'r') as file:
            process_service_execution_content = json.loads(file.read())

        with open(self.fixture_path('data.json'), 'r') as file:
            data_content = json.loads(file.read())

        session = Session()
        organisation_id = process_service_execution_content.get('organisation_id')
        process_service_execution_id = process_service_execution_content.get(Model._FIELD_ID)

        process_service_execution = ProcessServiceExecution(session)
        self.assertIsNotNone(process_service_execution)

        with requests_mock.Mocker() as mock:
            mock.get(
                f"{Session.API_URL_DEFAULT}{ProcessServiceExecution._PATH_GET.format(organisation_id=organisation_id, process_service_execution_id=process_service_execution_id)}",
                text=json.dumps({Model._RESPONSE_KEY_MODEL: process_service_execution_content}))
            process_service_execution.get(organisation_id=organisation_id, process_service_execution_id=process_service_execution_id)
            self.assertIsNotNone(process_service_execution)
            self.assertEqual(str(process_service_execution_id), str(process_service_execution.id))

            path = Data._PATH_GET.format(organisation_id=organisation_id, data_id=process_service_execution._model['inputs'][0])

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                next(process_service_execution.inputs)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                next(process_service_execution.inputs)

            for id in process_service_execution._model['inputs']:
                path = Data._PATH_GET.format(organisation_id=organisation_id, data_id=id)
                data_content[Model._FIELD_ID] = str(id)
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: data_content}))

            for input in process_service_execution.inputs:
                self.assertIsNotNone(input.id)

    def test_model_from_api_id(self):
        """
        Tests that an object can be created from an API endpoint.
        """
        with open(self.fixture_path('process_service_execution.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get('organisation_id')
        process_service_execution_id = content.get(Model._FIELD_ID)
        path = ProcessServiceExecution._PATH_GET.format(organisation_id=organisation_id, process_service_execution_id=process_service_execution_id)

        with requests_mock.Mocker() as mock:
            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                ProcessServiceExecution._model_from_api_id(session, id=process_service_execution_id, organisation_id=organisation_id)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                ProcessServiceExecution._model_from_api_id(session, id=process_service_execution_id, organisation_id=organisation_id)

            with pytest.raises(ModelError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                ProcessServiceExecution._model_from_api_id(session, id=process_service_execution_id, organisation_id=organisation_id)

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            process_service_execution = ProcessServiceExecution._model_from_api_id(session, id=process_service_execution_id, organisation_id=organisation_id)
            self.assertIsNotNone(process_service_execution)
            self.assertEqual(str(process_service_execution_id), str(process_service_execution.id))

    def test_models_from_api_ids(self):
        """
        Tests that objects can be created from an API endpoint.
        """
        with open(self.fixture_path('process_service_execution.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get('organisation_id')
        process_service_execution_id = content.get(Model._FIELD_ID)
        path = ProcessServiceExecution._PATH_GET.format(organisation_id=organisation_id, process_service_execution_id=process_service_execution_id)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            process_service_executions = ProcessServiceExecution._models_from_api_ids(session, [
                {Model._FIELD_ID: process_service_execution_id, 'organisation_id': organisation_id}])
            self.assertIsNotNone(process_service_executions)

            for process_service_execution in process_service_executions:
                self.assertEqual(str(process_service_execution_id), str(process_service_execution.id))

    def test_models_from_api_path(self):
        """
        Tests that objects can be created from an API endpoint returning a list.
        """
        with open(self.fixture_path('process_service_execution.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        process_service_execution_id = content.get(Model._FIELD_ID)
        path = '/path'

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [content]}))
            process_service_executions = ProcessServiceExecution._models_from_api_path(session, path)
            self.assertIsNotNone(process_service_executions)

            for process_service_execution in process_service_executions:
                self.assertEqual(str(process_service_execution_id), str(process_service_execution.id))

    def test_outputs(self):
        """
        Tests that outputs can be obtained from a model.
        """
        with open(self.fixture_path('process_service_execution.json'), 'r') as file:
            process_service_execution_content = json.loads(file.read())

        with open(self.fixture_path('data.json'), 'r') as file:
            data_content = json.loads(file.read())

        session = Session()
        organisation_id = process_service_execution_content.get('organisation_id')
        process_service_execution_id = process_service_execution_content.get(Model._FIELD_ID)

        process_service_execution = ProcessServiceExecution(session)
        self.assertIsNotNone(process_service_execution)

        with requests_mock.Mocker() as mock:
            mock.get(
                f"{Session.API_URL_DEFAULT}{ProcessServiceExecution._PATH_GET.format(organisation_id=organisation_id, process_service_execution_id=process_service_execution_id)}",
                text=json.dumps({Model._RESPONSE_KEY_MODEL: process_service_execution_content}))
            process_service_execution.get(organisation_id=organisation_id, process_service_execution_id=process_service_execution_id)
            self.assertIsNotNone(process_service_execution)
            self.assertEqual(str(process_service_execution_id), str(process_service_execution.id))

            path = Data._PATH_GET.format(organisation_id=organisation_id, data_id=process_service_execution._model['outputs'][0])

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                next(process_service_execution.outputs)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                next(process_service_execution.outputs)

            for id in process_service_execution._model['outputs']:
                path = Data._PATH_GET.format(organisation_id=organisation_id, data_id=id)
                data_content[Model._FIELD_ID] = str(id)
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: data_content}))

            for output in process_service_execution.outputs:
                self.assertIsNotNone(output.id)

    def test_schema(self):
        """
        Tests that a process execution model can be loaded into the schema.
        """
        with open(self.fixture_path('process_service_execution.json'), 'r') as file:
            content = json.loads(file.read())

        model = ProcessServiceExecutionSchema().load(content)
        self.assertIsNotNone(model)

        for key in content:
            self.assertEqual(json.dumps(content[key], default=json_default), json.dumps(model[key], default=json_default))
