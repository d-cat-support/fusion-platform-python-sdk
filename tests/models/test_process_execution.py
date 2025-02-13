#
# Process execution model class test file.
#
# @author Matthew Casey
#
# (c) Digital Content Analysis Technology Ltd 2022
#

from datetime import datetime, timedelta, timezone
import json
import pytest
import requests
import requests_mock

from tests.custom_test_case import CustomTestCase

from fusion_platform.common.utilities import json_default
from fusion_platform.models.model import Model, ModelError
from fusion_platform.models.process_execution import ProcessExecution, ProcessExecutionSchema
from fusion_platform.session import Session, RequestError


class TestProcessExecution(CustomTestCase):
    """
    Process execution model tests.
    """

    def test_init(self):
        """
        Test initialisation of the process execution model class to ensure no exceptions are raised.
        """
        process_execution = ProcessExecution(Session())
        self.assertIsNotNone(process_execution)
        self._logger.info(process_execution)

    def test_change_delete_expiry(self):
        """
        Tests that the delete expiry for an execution can be updated.
        """
        with open(self.fixture_path('process_execution.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get('organisation_id')
        process_execution_id = content.get(Model._FIELD_ID)
        path = ProcessExecution._PATH_CHANGE_DELETE_EXPIRY.format(organisation_id=organisation_id, process_execution_id=process_execution_id)
        delete_expiry = datetime.now(timezone.utc) + timedelta(days=2)

        process_execution = ProcessExecution(session)
        self.assertIsNotNone(process_execution)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{ProcessExecution._PATH_GET.format(organisation_id=organisation_id, process_execution_id=process_execution_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            process_execution.get(organisation_id=organisation_id, process_execution_id=process_execution_id)
            self.assertIsNotNone(process_execution)
            self.assertEqual(str(process_execution_id), str(process_execution.id))

            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                process_execution.change_delete_expiry(delete_expiry=delete_expiry)

            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                process_execution.change_delete_expiry(delete_expiry=delete_expiry)

            self.assertNotEqual(delete_expiry, process_execution.delete_expiry)

            content['delete_expiry'] = delete_expiry
            adapter = mock.post(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}, default=json_default))
            process_execution.change_delete_expiry(delete_expiry=delete_expiry)

            self.assertEqual({'ProcessExecution': {'delete_expiry': delete_expiry.isoformat()}}, json.loads(adapter.last_request.text))

    def test_check_complete_no_wait(self):
        """
        Tests checking if the execution is complete without waiting.
        """
        with open(self.fixture_path('process_execution.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get('organisation_id')
        process_execution_id = content.get(Model._FIELD_ID)
        path = ProcessExecution._PATH_GET.format(organisation_id=organisation_id, process_execution_id=process_execution_id)

        process_execution = ProcessExecution(session)
        self.assertIsNotNone(process_execution)

        process_execution._set_model(content)

        with requests_mock.Mocker() as mock:
            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                process_execution.check_complete()

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                process_execution.check_complete()

            with pytest.raises(ModelError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                process_execution.check_complete()

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            self.assertTrue(process_execution.check_complete())

            with pytest.raises(ModelError):
                content['success'] = False
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
                process_execution.check_complete()

            content['progress'] = 50
            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            self.assertFalse(process_execution.check_complete())

    def test_check_complete_wait(self):
        """
        Tests checking if the execution is complete with waiting.
        """
        with open(self.fixture_path('process_execution.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get('organisation_id')
        process_execution_id = content.get(Model._FIELD_ID)
        path = ProcessExecution._PATH_GET.format(organisation_id=organisation_id, process_execution_id=process_execution_id)

        process_execution = ProcessExecution(session)
        self.assertIsNotNone(process_execution)

        process_execution._set_model(content)

        with requests_mock.Mocker() as mock:
            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                process_execution.check_complete(wait=True)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                process_execution.check_complete(wait=True)

            with pytest.raises(ModelError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                process_execution.check_complete(wait=True)

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            self.assertTrue(process_execution.check_complete(wait=True))

            with pytest.raises(ModelError):
                content['success'] = False
                content['abort_reason'] = 'Execution failed'
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
                process_execution.check_complete(wait=True)

            content['success'] = True
            not_complete_content = content.copy()
            not_complete_content['progress'] = 50
            content['abort_reason'] = 'Execution warning'
            mock.get(f"{Session.API_URL_DEFAULT}{path}",
                     [{'text': json.dumps({Model._RESPONSE_KEY_MODEL: not_complete_content})}, {'text': json.dumps({Model._RESPONSE_KEY_MODEL: content})}])
            self.assertTrue(process_execution.check_complete(wait=True))

    def test_components(self):
        """
        Tests the components property retrieves process service execution items.
        """
        with open(self.fixture_path('process_execution.json'), 'r') as file:
            process_execution_content = json.loads(file.read())

        with open(self.fixture_path('process_service_execution.json'), 'r') as file:
            component_content = json.loads(file.read())

        session = Session()
        organisation_id = process_execution_content.get('organisation_id')
        process_execution_id = process_execution_content.get(Model._FIELD_ID)
        path = ProcessExecution._PATH_COMPONENTS.format(organisation_id=organisation_id, process_execution_id=process_execution_id)

        process = ProcessExecution(session)
        self.assertIsNotNone(process)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{ProcessExecution._PATH_GET.format(organisation_id=organisation_id, process_execution_id=process_execution_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: process_execution_content}))
            process.get(organisation_id=organisation_id, process_execution_id=process_execution_id)
            self.assertIsNotNone(process)
            self.assertEqual(str(process_execution_id), str(process.id))

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                next(process.components)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                next(process.components)

            with pytest.raises(StopIteration):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                next(process.components)

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [component_content]}))

            for component in process.components:
                self.assertEqual(str(process_execution_id), str(component.process_execution_id))

    def test_delete(self):
        """
        Tests that an object can be deleted from the API.
        """
        with open(self.fixture_path('process_execution.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get('organisation_id')
        process_execution_id = content.get(Model._FIELD_ID)
        path = ProcessExecution._PATH_DELETE.format(organisation_id=organisation_id, process_execution_id=process_execution_id)

        process_execution = ProcessExecution(session)
        self.assertIsNotNone(process_execution)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{ProcessExecution._PATH_GET.format(organisation_id=organisation_id, process_execution_id=process_execution_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            process_execution.get(organisation_id=organisation_id, process_execution_id=process_execution_id)
            self.assertIsNotNone(process_execution)
            self.assertEqual(str(process_execution_id), str(process_execution.id))

            with pytest.raises(RequestError):
                mock.delete(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                process_execution.delete()

            with pytest.raises(RequestError):
                mock.delete(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                process_execution.delete()

            mock.delete(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            process_execution.delete()

    def test_get(self):
        """
        Tests that an object can be retrieved from the API.
        """
        with open(self.fixture_path('process_execution.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get('organisation_id')
        process_execution_id = content.get(Model._FIELD_ID)
        path = ProcessExecution._PATH_GET.format(organisation_id=organisation_id, process_execution_id=process_execution_id)

        process_execution = ProcessExecution(session)
        self.assertIsNotNone(process_execution)

        with requests_mock.Mocker() as mock:
            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                process_execution.get(organisation_id=organisation_id, process_execution_id=process_execution_id)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                process_execution.get(organisation_id=organisation_id, process_execution_id=process_execution_id)

            with pytest.raises(ModelError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                process_execution.get(organisation_id=organisation_id, process_execution_id=process_execution_id)

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            process_execution.get(organisation_id=organisation_id, process_execution_id=process_execution_id)
            self.assertIsNotNone(process_execution)
            self.assertEqual(str(process_execution_id), str(process_execution.id))

            process_execution.get()
            self.assertIsNotNone(process_execution)
            self.assertEqual(str(process_execution_id), str(process_execution.id))

    def test_model_from_api_id(self):
        """
        Tests that an object can be created from an API endpoint.
        """
        with open(self.fixture_path('process_execution.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get('organisation_id')
        process_execution_id = content.get(Model._FIELD_ID)
        path = ProcessExecution._PATH_GET.format(organisation_id=organisation_id, process_execution_id=process_execution_id)

        with requests_mock.Mocker() as mock:
            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                ProcessExecution._model_from_api_id(session, id=process_execution_id, organisation_id=organisation_id)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                ProcessExecution._model_from_api_id(session, id=process_execution_id, organisation_id=organisation_id)

            with pytest.raises(ModelError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                ProcessExecution._model_from_api_id(session, id=process_execution_id, organisation_id=organisation_id)

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            process_execution = ProcessExecution._model_from_api_id(session, id=process_execution_id, organisation_id=organisation_id)
            self.assertIsNotNone(process_execution)
            self.assertEqual(str(process_execution_id), str(process_execution.id))

    def test_models_from_api_ids(self):
        """
        Tests that objects can be created from an API endpoint.
        """
        with open(self.fixture_path('process_execution.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get('organisation_id')
        process_execution_id = content.get(Model._FIELD_ID)
        path = ProcessExecution._PATH_GET.format(organisation_id=organisation_id, process_execution_id=process_execution_id)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            process_executions = ProcessExecution._models_from_api_ids(session, [{Model._FIELD_ID: process_execution_id, 'organisation_id': organisation_id}])
            self.assertIsNotNone(process_executions)

            for process_execution in process_executions:
                self.assertEqual(str(process_execution_id), str(process_execution.id))

    def test_models_from_api_path(self):
        """
        Tests that objects can be created from an API endpoint returning a list.
        """
        with open(self.fixture_path('process_execution.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        process_execution_id = content.get(Model._FIELD_ID)
        path = '/path'

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [content]}))
            process_executions = ProcessExecution._models_from_api_path(session, path)
            self.assertIsNotNone(process_executions)

            for process_execution in process_executions:
                self.assertEqual(str(process_execution_id), str(process_execution.id))

    def test_schema(self):
        """
        Tests that a process execution model can be loaded into the schema.
        """
        with open(self.fixture_path('process_execution.json'), 'r') as file:
            content = json.loads(file.read())

        model = ProcessExecutionSchema().load(content)
        self.assertIsNotNone(model)

        for key in content:
            self.assertEqual(json.dumps(content[key], default=json_default), json.dumps(model[key], default=json_default))

    def test_update(self):
        """
        Tests that an object can be updated to the API.
        """
        with open(self.fixture_path('process_execution.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get('organisation_id')
        process_execution_id = content.get(Model._FIELD_ID)
        path = ProcessExecution._PATH_PATCH.format(organisation_id=organisation_id, process_execution_id=process_execution_id)
        delete_expiry = datetime.now(timezone.utc) + timedelta(days=2)

        process_execution = ProcessExecution(session)
        self.assertIsNotNone(process_execution)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{ProcessExecution._PATH_GET.format(organisation_id=organisation_id, process_execution_id=process_execution_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            process_execution.get(organisation_id=organisation_id, process_execution_id=process_execution_id)
            self.assertIsNotNone(process_execution)
            self.assertEqual(str(process_execution_id), str(process_execution.id))

            with pytest.raises(RequestError):
                mock.patch(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                process_execution.update(delete_expiry=delete_expiry)

            with pytest.raises(RequestError):
                mock.patch(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                process_execution.update(delete_expiry=delete_expiry)

            with pytest.raises(ModelError):
                mock.patch(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                process_execution.update(delete_expiry=delete_expiry)

            self.assertNotEqual(delete_expiry, process_execution.delete_expiry)

            content['delete_expiry'] = delete_expiry
            mock.patch(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}, default=json_default))
            process_execution.update(delete_expiry=delete_expiry)
            self.assertEqual(delete_expiry, process_execution.delete_expiry)
