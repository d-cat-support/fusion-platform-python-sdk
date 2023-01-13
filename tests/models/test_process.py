#
# Process model class test file.
#
# @author Matthew Casey
#
# (c) Digital Content Analysis Technology Ltd 2022
#

import json
import pytest
import requests
import requests_mock
import uuid

import fusion_platform
from tests.custom_test_case import CustomTestCase

from fusion_platform.common.utilities import json_default
from fusion_platform.models.data import Data
from fusion_platform.models.model import Model, ModelError
from fusion_platform.models.process import Process, ProcessInputSchema, ProcessOptionSchema, ProcessSchema
from fusion_platform.models.process_execution import ProcessExecution
from fusion_platform.session import Session, RequestError


class TestProcess(CustomTestCase):
    """
    Process model tests.
    """

    def test_init(self):
        """
        Test initialisation of the process model class to ensure no exceptions are raised.
        """
        process = Process(Session())
        self.assertIsNotNone(process)

    def test_copy(self):
        """
        Tests that a template copy object can be created from an API endpoint with validation using a Marshmallow schema.
        """
        with open(self.fixture_path('process.json'), 'r') as file:
            content = json.loads(file.read())

        with open(self.fixture_path('data.json'), 'r') as file:
            data_content = json.loads(file.read())

        with open(self.fixture_path('data_file.json'), 'r') as file:
            file_content = json.loads(file.read())

        session = Session()
        organisation_id = content.get('organisation_id')
        process_id = content.get('id')
        path = Process._PATH_COPY.format(organisation_id=organisation_id, process_id=process_id)
        name = 'Test'

        data1_id = uuid.uuid4()
        data2_id = uuid.uuid4()

        content['inputs'][0]['id'] = str(data1_id)
        content['inputs'][1]['id'] = str(data2_id)

        process = Process(session)
        self.assertIsNotNone(process)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{Process._PATH_GET.format(organisation_id=organisation_id, process_id=process_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            process.get(organisation_id=organisation_id, process_id=process_id)

            data_content['id'] = str(data1_id)
            mock.get(f"{Session.API_URL_DEFAULT}{Data._PATH_GET.format(organisation_id=organisation_id, data_id=data1_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: data_content}))
            file_content['file_type'] = fusion_platform.FILE_TYPE_GEOJSON
            mock.get(f"{Session.API_URL_DEFAULT}{Data._PATH_FILES.format(organisation_id=organisation_id, data_id=data1_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_LIST: [file_content]}))

            data_content['id'] = str(data2_id)
            mock.get(f"{Session.API_URL_DEFAULT}{Data._PATH_GET.format(organisation_id=organisation_id, data_id=data2_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: data_content}))
            file_content['file_type'] = fusion_platform.FILE_TYPE_GEOTIFF
            mock.get(f"{Session.API_URL_DEFAULT}{Data._PATH_FILES.format(organisation_id=organisation_id, data_id=data2_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_LIST: [file_content]}))

            content['id'] = str(uuid.uuid4())

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                process.copy(name=name)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                process.copy(name=name)

            with pytest.raises(ModelError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                process.copy(name=name)

            with pytest.raises(ModelError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({'rubbish': content}))
                process.copy(name=name)

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            process_copy = process.copy(name=name)

            schema = ProcessSchema()

            for key in content:
                if (Model._METADATA_HIDE not in schema.fields[key].metadata) and (content[key] is not None):
                    self.assertEqual(json.dumps(content[key], default=json_default), json.dumps(getattr(process_copy, key), default=json_default))

            self.assertNotEqual(process_copy.id, process.id)
            self.assertEqual(name, process_copy.name)

            for option in content['options']:
                for item in process_copy.options:
                    if item.name == option['name']:
                        if (not isinstance(item.value, bool)) and (isinstance(item.value, int) or isinstance(item.value, float)):
                            self.assertEqual(float(item.value), float(option['value']))
                        else:
                            self.assertEqual(str(item.value).lower(), str(option['value']).lower())

            for input in content['inputs']:
                self.assertTrue(any([item for item in process_copy.inputs if str(item.id) == str(input['id'])]))

    def test_create(self):
        """
        Tests that a process object can be created.
        """
        with open(self.fixture_path('process.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get('organisation_id')
        path = Process._PATH_CREATE.format(organisation_id=organisation_id)

        process = Process(session)
        self.assertIsNotNone(process)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{Process._PATH_NEW.format(organisation_id=organisation_id)}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            process._new(organisation_id=organisation_id)

            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                process.create()

            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                process.create()

            with pytest.raises(ModelError):
                mock.post(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                process.create()

            mock.post(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            process.create()

            schema = ProcessSchema()

            for key in content:
                if (Model._METADATA_HIDE not in schema.fields[key].metadata) and (content[key] is not None):
                    self.assertEqual(json.dumps(content[key], default=json_default), json.dumps(getattr(process, key), default=json_default))

    def test_delete(self):
        """
        Tests that an object can be deleted from the API.
        """
        with open(self.fixture_path('process.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get('organisation_id')
        process_id = content.get(Model._FIELD_ID)
        path = Process._PATH_DELETE.format(organisation_id=organisation_id, process_id=process_id)

        process = Process(session)
        self.assertIsNotNone(process)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{Process._PATH_GET.format(organisation_id=organisation_id, process_id=process_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            process.get(organisation_id=organisation_id, process_id=process_id)
            self.assertIsNotNone(process)
            self.assertEqual(str(process_id), str(process.id))

            with pytest.raises(RequestError):
                mock.delete(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                process.delete()

            with pytest.raises(RequestError):
                mock.delete(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                process.delete()

            mock.delete(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            process.delete()

    def test_execute_no_wait(self):
        """
        Tests that a process can be executed without waiting.
        """
        with open(self.fixture_path('process.json'), 'r') as file:
            process_content = json.loads(file.read())

        with open(self.fixture_path('process_execution.json'), 'r') as file:
            execution_content = json.loads(file.read())

        session = Session()
        organisation_id = process_content.get('organisation_id')
        process_id = process_content.get(Model._FIELD_ID)
        process_execution_id = execution_content.get(Model._FIELD_ID)
        execute_path = Process._PATH_EXECUTE.format(organisation_id=organisation_id, process_id=process_id)
        get_path = Process._PATH_GET.format(organisation_id=organisation_id, process_id=process_id)
        executions_path = Process._PATH_EXECUTIONS.format(organisation_id=organisation_id, process_id=process_id)
        execution_path = ProcessExecution._PATH_GET.format(organisation_id=organisation_id, process_execution_id=process_execution_id)

        process = Process(session)
        self.assertIsNotNone(process)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{get_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content}))
            process.get(organisation_id=organisation_id, process_id=process_id)
            self.assertIsNotNone(process)
            self.assertEqual(str(process_id), str(process.id))

            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}{execute_path}", exc=requests.exceptions.ConnectTimeout)
                process.execute()

            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}{execute_path}", status_code=400)
                process.execute()

            with pytest.raises(ModelError):
                mock.post(f"{Session.API_URL_DEFAULT}{execute_path}", text='{}')
                process.execute()

            process_content['process_status'] = Process._PROCESS_STATUS_EXECUTE
            mock.post(f"{Session.API_URL_DEFAULT}{execute_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content}))
            process.execute()

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{get_path}", exc=requests.exceptions.ConnectTimeout)
                process.wait_for_next_execution()

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{get_path}", status_code=400)
                process.wait_for_next_execution()

            with pytest.raises(ModelError):
                mock.get(f"{Session.API_URL_DEFAULT}{get_path}", text='{}')
                process.wait_for_next_execution()

            mock.get(f"{Session.API_URL_DEFAULT}{get_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content}))
            process.wait_for_next_execution()

            mock.get(f"{Session.API_URL_DEFAULT}{executions_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [execution_content]}))

            for process_execution in process.executions:
                with pytest.raises(RequestError):
                    mock.get(f"{Session.API_URL_DEFAULT}{execution_path}", exc=requests.exceptions.ConnectTimeout)
                    process_execution.check_complete()

                with pytest.raises(RequestError):
                    mock.get(f"{Session.API_URL_DEFAULT}{execution_path}", status_code=400)
                    process_execution.check_complete()

                with pytest.raises(ModelError):
                    mock.get(f"{Session.API_URL_DEFAULT}{execution_path}", text='{}')
                    process_execution.check_complete()

                mock.get(f"{Session.API_URL_DEFAULT}{execution_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: execution_content}))
                self.assertTrue(process_execution.check_complete())

    def test_execute_wait(self):
        """
        Tests that a process can be executed with waiting.
        """
        with open(self.fixture_path('process.json'), 'r') as file:
            process_content = json.loads(file.read())

        with open(self.fixture_path('process_execution.json'), 'r') as file:
            execution_content = json.loads(file.read())

        session = Session()
        organisation_id = process_content.get('organisation_id')
        process_id = process_content.get(Model._FIELD_ID)
        process_execution_id = execution_content.get(Model._FIELD_ID)
        execute_path = Process._PATH_EXECUTE.format(organisation_id=organisation_id, process_id=process_id)
        get_path = Process._PATH_GET.format(organisation_id=organisation_id, process_id=process_id)
        executions_path = Process._PATH_EXECUTIONS.format(organisation_id=organisation_id, process_id=process_id)
        execution_path = ProcessExecution._PATH_GET.format(organisation_id=organisation_id, process_execution_id=process_execution_id)

        process = Process(session)
        self.assertIsNotNone(process)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{get_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content}))
            process.get(organisation_id=organisation_id, process_id=process_id)
            self.assertIsNotNone(process)
            self.assertEqual(str(process_id), str(process.id))

            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}{execute_path}", exc=requests.exceptions.ConnectTimeout)
                process.execute(wait=True)

            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}{execute_path}", status_code=400)
                process.execute(wait=True)

            with pytest.raises(ModelError):
                mock.post(f"{Session.API_URL_DEFAULT}{execute_path}", text='{}')
                process.execute(wait=True)

            process_content['process_status'] = Process._PROCESS_STATUS_EXECUTE
            mock.post(f"{Session.API_URL_DEFAULT}{execute_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content}))
            mock.get(f"{Session.API_URL_DEFAULT}{get_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content}))
            mock.get(f"{Session.API_URL_DEFAULT}{executions_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [execution_content]}))
            mock.get(f"{Session.API_URL_DEFAULT}{execution_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: execution_content}))
            process.execute(wait=True)

    def test_execute_wait_group(self):
        """
        Tests that a process with a group of executions can be executed with waiting.
        """
        with open(self.fixture_path('process_with_group.json'), 'r') as file:
            process_content = json.loads(file.read())

        with open(self.fixture_path('process_execution.json'), 'r') as file:
            execution_content = json.loads(file.read())

        session = Session()
        organisation_id = process_content.get('organisation_id')
        process_id = process_content.get(Model._FIELD_ID)
        process_execution_id = execution_content.get(Model._FIELD_ID)
        execute_path = Process._PATH_EXECUTE.format(organisation_id=organisation_id, process_id=process_id)
        get_path = Process._PATH_GET.format(organisation_id=organisation_id, process_id=process_id)
        executions_path = Process._PATH_EXECUTIONS.format(organisation_id=organisation_id, process_id=process_id)
        execution_path = ProcessExecution._PATH_GET.format(organisation_id=organisation_id, process_execution_id=process_execution_id)

        process = Process(session)
        self.assertIsNotNone(process)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{get_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content}))
            process.get(organisation_id=organisation_id, process_id=process_id)
            self.assertIsNotNone(process)
            self.assertEqual(str(process_id), str(process.id))

            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}{execute_path}", exc=requests.exceptions.ConnectTimeout)
                process.execute(wait=True)

            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}{execute_path}", status_code=400)
                process.execute(wait=True)

            with pytest.raises(ModelError):
                mock.post(f"{Session.API_URL_DEFAULT}{execute_path}", text='{}')
                process.execute(wait=True)

            process_content['process_status'] = Process._PROCESS_STATUS_EXECUTE
            mock.post(f"{Session.API_URL_DEFAULT}{execute_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content}))
            mock.get(f"{Session.API_URL_DEFAULT}{get_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content}))
            mock.get(f"{Session.API_URL_DEFAULT}{executions_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [execution_content]}))
            mock.get(f"{Session.API_URL_DEFAULT}{execution_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: execution_content}))
            process.execute(wait=True)

    def test_executions(self):
        """
        Tests the executions property retrieves process execution items.
        """
        with open(self.fixture_path('process.json'), 'r') as file:
            process_content = json.loads(file.read())

        with open(self.fixture_path('process_execution.json'), 'r') as file:
            execution_content = json.loads(file.read())

        session = Session()
        organisation_id = process_content.get('organisation_id')
        process_id = process_content.get(Model._FIELD_ID)
        path = Process._PATH_EXECUTIONS.format(organisation_id=organisation_id, process_id=process_id)

        process = Process(session)
        self.assertIsNotNone(process)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{Process._PATH_GET.format(organisation_id=organisation_id, process_id=process_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content}))
            process.get(organisation_id=organisation_id, process_id=process_id)
            self.assertIsNotNone(process)
            self.assertEqual(str(process_id), str(process.id))

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                next(process.executions)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                next(process.executions)

            with pytest.raises(StopIteration):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                next(process.executions)

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [execution_content]}))

            for execution in process.executions:
                self.assertEqual(str(process_id), str(execution.process_id))

    def test_find_executions(self):
        """
        Tests the finding of process execution items.
        """
        with open(self.fixture_path('process.json'), 'r') as file:
            process_content = json.loads(file.read())

        with open(self.fixture_path('process_execution.json'), 'r') as file:
            execution_content = json.loads(file.read())

        session = Session()
        organisation_id = process_content.get('organisation_id')
        process_id = process_content.get(Model._FIELD_ID)
        process_execution_id = execution_content.get(Model._FIELD_ID)
        group_id = execution_content.get(Model._FIELD_GROUP_ID)
        path = Process._PATH_EXECUTIONS.format(organisation_id=organisation_id, process_id=process_id)

        process = Process(session)
        self.assertIsNotNone(process)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{Process._PATH_GET.format(organisation_id=organisation_id, process_id=process_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content}))
            process.get(organisation_id=organisation_id, process_id=process_id)
            self.assertIsNotNone(process)
            self.assertEqual(str(process_id), str(process.id))

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                process.find_executions()

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                process.find_executions()

            with pytest.raises(StopIteration):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                first, generator = process.find_executions()
                self.assertIsNone(first)
                next(generator)

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [execution_content]}))
            first, generator = process.find_executions(id=process_execution_id, group_id=group_id)
            self.assertIsNotNone(first)

            for execution in generator:
                self.assertEqual(first.attributes, execution.attributes)

    def test_get(self):
        """
        Tests that an object can be retrieved from the API.
        """
        with open(self.fixture_path('process.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get('organisation_id')
        process_id = content.get(Model._FIELD_ID)
        path = Process._PATH_GET.format(organisation_id=organisation_id, process_id=process_id)

        process = Process(session)
        self.assertIsNotNone(process)

        with requests_mock.Mocker() as mock:
            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                process.get(organisation_id=organisation_id, process_id=process_id)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                process.get(organisation_id=organisation_id, process_id=process_id)

            with pytest.raises(ModelError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                process.get(organisation_id=organisation_id, process_id=process_id)

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            process.get(organisation_id=organisation_id, process_id=process_id)
            self.assertIsNotNone(process)
            self.assertEqual(str(process_id), str(process.id))

            process.get()
            self.assertIsNotNone(process)
            self.assertEqual(str(process_id), str(process.id))

    def test_inputs(self):
        """
        Tests that the inputs can be obtained from a process model.
        """
        with open(self.fixture_path('process.json'), 'r') as file:
            process_content = json.loads(file.read())

        with open(self.fixture_path('data.json'), 'r') as file:
            data_content = json.loads(file.read())

        session = Session()
        organisation_id = process_content.get('organisation_id')
        process_id = process_content.get(Model._FIELD_ID)
        data_id = data_content.get(Model._FIELD_ID)
        path = Process._PATH_GET.format(organisation_id=organisation_id, process_id=process_id)

        process = Process(session)
        self.assertIsNotNone(process)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content}))
            process.get(organisation_id=organisation_id, process_id=process_id)
            self.assertIsNotNone(process)
            self.assertEqual(str(process_id), str(process.id))

            mock.get(f"{Session.API_URL_DEFAULT}{Data._PATH_GET.format(organisation_id=organisation_id, data_id=data_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: data_content}))

            inputs = process.inputs
            self.assertIsNotNone(inputs)

            for input in inputs:
                self.assertIsNotNone(input.ssd_id)

    def test_model_from_api_id(self):
        """
        Tests that an object can be created from an API endpoint.
        """
        with open(self.fixture_path('process.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get('organisation_id')
        process_id = content.get(Model._FIELD_ID)
        path = Process._PATH_GET.format(organisation_id=organisation_id, process_id=process_id)

        with requests_mock.Mocker() as mock:
            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                Process._model_from_api_id(session, id=process_id, organisation_id=organisation_id)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                Process._model_from_api_id(session, id=process_id, organisation_id=organisation_id)

            with pytest.raises(ModelError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                Process._model_from_api_id(session, id=process_id, organisation_id=organisation_id)

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            process = Process._model_from_api_id(session, id=process_id, organisation_id=organisation_id)
            self.assertIsNotNone(process)
            self.assertEqual(str(process_id), str(process.id))

    def test_models_from_api_ids(self):
        """
        Tests that objects can be created from an API endpoint.
        """
        with open(self.fixture_path('process.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get('organisation_id')
        process_id = content.get(Model._FIELD_ID)
        path = Process._PATH_GET.format(organisation_id=organisation_id, process_id=process_id)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            processes = Process._models_from_api_ids(session, [{Model._FIELD_ID: process_id, 'organisation_id': organisation_id}])
            self.assertIsNotNone(processes)

            for process in processes:
                self.assertEqual(str(process_id), str(process.id))

    def test_models_from_api_path(self):
        """
        Tests that objects can be created from an API endpoint returning a list.
        """
        with open(self.fixture_path('process.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        process_id = content.get(Model._FIELD_ID)
        path = '/path'

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [content]}))
            processes = Process._models_from_api_path(session, path)
            self.assertIsNotNone(processes)

            for process in processes:
                self.assertEqual(str(process_id), str(process.id))

    def test_new(self):
        """
        Tests that a template new object can be created from an API endpoint with validation using a Marshmallow schema.
        """
        with open(self.fixture_path('process.json'), 'r') as file:
            content = json.loads(file.read())

        wrong_content = {}

        for key in content:
            wrong_content[f"new_{key}"] = content[key]

        session = Session()
        organisation_id = content.get('organisation_id')
        path = Process._PATH_NEW.format(organisation_id=organisation_id)

        process = Process(session)
        self.assertIsNotNone(process)

        with requests_mock.Mocker() as mock:

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                process._new(organisation_id=organisation_id)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                process._new(organisation_id=organisation_id)

            with pytest.raises(ModelError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                process._new(organisation_id=organisation_id)

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: wrong_content}))
            process._new(organisation_id=organisation_id)

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            process._new(organisation_id=organisation_id)

            schema = ProcessSchema()

            for key in content:
                if (Model._METADATA_HIDE not in schema.fields[key].metadata) and (content[key] is not None):
                    self.assertEqual(json.dumps(content[key], default=json_default), json.dumps(getattr(process, key), default=json_default))

    def test_options(self):
        """
        Tests that the options can be obtained from a process model.
        """
        with open(self.fixture_path('process.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get('organisation_id')
        process_id = content.get(Model._FIELD_ID)
        path = Process._PATH_GET.format(organisation_id=organisation_id, process_id=process_id)

        process = Process(session)
        self.assertIsNotNone(process)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            process.get(organisation_id=organisation_id, process_id=process_id)
            self.assertIsNotNone(process)
            self.assertEqual(str(process_id), str(process.id))

            options = process.options
            self.assertIsNotNone(options)

            for option in options:
                self.assertIsNotNone(option.ssd_id)

    def test_schema(self):
        """
        Tests that a process model can be loaded into the schema.
        """
        with open(self.fixture_path('process.json'), 'r') as file:
            content = json.loads(file.read())

        model = ProcessSchema().load(content)
        self.assertIsNotNone(model)

        for key in content:
            self.assertEqual(json.dumps(content[key], default=json_default), json.dumps(model[key], default=json_default))

    def test_stop(self):
        """
        Tests that a process can be stopped.
        """
        with open(self.fixture_path('process.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get('organisation_id')
        process_id = content.get(Model._FIELD_ID)
        path = Process._PATH_STOP.format(organisation_id=organisation_id, process_id=process_id)

        process = Process(session)
        self.assertIsNotNone(process)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{Process._PATH_GET.format(organisation_id=organisation_id, process_id=process_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            process.get(organisation_id=organisation_id, process_id=process_id)
            self.assertIsNotNone(process)
            self.assertEqual(str(process_id), str(process.id))

            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                process.stop()

            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                process.stop()

            with pytest.raises(ModelError):
                mock.post(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                process.stop()

            mock.post(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            process.stop()

    def test_update(self):
        """
        Tests that an object can be updated to the API.
        """
        with open(self.fixture_path('process.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get('organisation_id')
        process_id = content.get(Model._FIELD_ID)
        path = Process._PATH_PATCH.format(organisation_id=organisation_id, process_id=process_id)
        name = 'New Name'

        process = Process(session)
        self.assertIsNotNone(process)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{Process._PATH_GET.format(organisation_id=organisation_id, process_id=process_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            process.get(organisation_id=organisation_id, process_id=process_id)
            self.assertIsNotNone(process)
            self.assertEqual(str(process_id), str(process.id))

            with pytest.raises(RequestError):
                mock.patch(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                process.update(name=name)

            with pytest.raises(RequestError):
                mock.patch(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                process.update(name=name)

            with pytest.raises(ModelError):
                mock.patch(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                process.update(name=name)

            self.assertNotEqual(name, process.name)

            content['process_status'] = Process._PROCESS_STATUS_EXECUTE
            mock.get(f"{Session.API_URL_DEFAULT}{Process._PATH_GET.format(organisation_id=organisation_id, process_id=process_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            process.get(organisation_id=organisation_id, process_id=process_id)
            self.assertEqual(Process._PROCESS_STATUS_EXECUTE, process.process_status)

            with pytest.raises(ModelError):
                mock.patch(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
                process.update(name=name)

            content['process_status'] = 'draft'
            mock.get(f"{Session.API_URL_DEFAULT}{Process._PATH_GET.format(organisation_id=organisation_id, process_id=process_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            process.get(organisation_id=organisation_id, process_id=process_id)
            self.assertNotEqual(Process._PROCESS_STATUS_EXECUTE, process.process_status)

            content['name'] = name
            mock.patch(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            process.update(name=name)
            self.assertEqual(name, process.name)

    def test_update_input(self):
        """
        Tests setting an input on a template process.
        """
        with open(self.fixture_path('process.json'), 'r') as file:
            process_content = json.loads(file.read())

        input_content = process_content['inputs'][0]

        with open(self.fixture_path('data.json'), 'r') as file:
            data_content = json.loads(file.read())

        with open(self.fixture_path('data_file.json'), 'r') as file:
            file_content = json.loads(file.read())

        session = Session()
        organisation_id = process_content.get('organisation_id')
        data_id = uuid.uuid4()
        input_id = process_content.get('inputs')[0].get('id')
        get_path = Process._PATH_NEW.format(organisation_id=organisation_id)
        files_path = Data._PATH_FILES.format(organisation_id=organisation_id, data_id=data_id)

        process = Process(session)
        self.assertIsNotNone(process)

        data = Data(session)
        data_content['id'] = data_id
        data._set_model(data_content)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{Data._PATH_GET.format(organisation_id=organisation_id, data_id=input_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: data_content}, default=str))

            mock.get(f"{Session.API_URL_DEFAULT}{Data._PATH_GET.format(organisation_id=organisation_id, data_id=data_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: data_content}, default=str))

            with pytest.raises(ModelError):
                process.update(input_number=1, data=None)

            with pytest.raises(ModelError):
                process_content['process_status'] = Process._PROCESS_STATUS_EXECUTE
                mock.get(f"{Session.API_URL_DEFAULT}{get_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content}))
                process._new(organisation_id=organisation_id)
                input = next(process.inputs)
                process.update(input=input, data=data)

            process_content['process_status'] = 'draft'
            mock.get(f"{Session.API_URL_DEFAULT}{get_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content}))
            process._new(organisation_id=organisation_id)

            with pytest.raises(ModelError):
                process.update(input_number=3, data=data)

            with pytest.raises(ModelError):
                input_content['input'] = 2
                input = Model(None, schema=ProcessInputSchema())
                input._set_model(input_content)
                process.update(input=input, data=data)

            del file_content['publishable']
            mock.get(f"{Session.API_URL_DEFAULT}{files_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [file_content]}))
            input = next(process.inputs)

            with pytest.raises(ModelError):
                process.update(input=input, data=data)

            file_content['publishable'] = False
            mock.get(f"{Session.API_URL_DEFAULT}{files_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [file_content]}))

            with pytest.raises(ModelError):
                file_content['file_type'] = fusion_platform.FILE_TYPE_GEOTIFF
                mock.get(f"{Session.API_URL_DEFAULT}{files_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [file_content]}))
                process.update(input_number=1, data=data)

            file_content['file_type'] = fusion_platform.FILE_TYPE_ESRI_SHAPEFILE
            mock.get(f"{Session.API_URL_DEFAULT}{files_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [file_content]}))

            self.assertEqual(str(process_content['inputs'][0]['id']), str(next(process.inputs).id))
            process.update(input_number=1, data=data)
            self.assertEqual(str(data_id), str(next(process.inputs).id))

            process._new(organisation_id=organisation_id)

            self.assertEqual(str(process_content['inputs'][0]['id']), str(next(process.inputs).id))
            process.update(input=input, data=data)
            self.assertEqual(str(data_id), str(next(process.inputs).id))

    def test_update_option(self):
        """
        Tests setting an option on a template process.
        """
        with open(self.fixture_path('process.json'), 'r') as file:
            process_content = json.loads(file.read())

        option_content = process_content['options'][0]

        session = Session()
        organisation_id = process_content.get('organisation_id')
        get_path = Process._PATH_NEW.format(organisation_id=organisation_id)

        process = Process(session)
        self.assertIsNotNone(process)

        with requests_mock.Mocker() as mock:
            with pytest.raises(ModelError):
                process_content['process_status'] = Process._PROCESS_STATUS_EXECUTE
                mock.get(f"{Session.API_URL_DEFAULT}{get_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content}))
                process._new(organisation_id=organisation_id)
                option = next(process.options)
                process.update(option=option, value=None)

            process_content['process_status'] = 'draft'
            mock.get(f"{Session.API_URL_DEFAULT}{get_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content}))
            process._new(organisation_id=organisation_id)

            with pytest.raises(ModelError):
                option_content['name'] = 'rubbish'
                option = Model(None, schema=ProcessOptionSchema())
                option._set_model(option_content)
                process.update(option=option, value=None)

            option_content['name'] = 'latest_date'

            with pytest.raises(ModelError):
                option = Model(None, schema=ProcessOptionSchema())
                option._set_model(option_content)
                process.update(option=option, value='rubbish')

            option = next(process.options)

            self.assertEqual(True, next(process.options).value)
            process.update(option_name='latest_date', value=False)
            self.assertEqual(False, next(process.options).value)

            process._new(organisation_id=organisation_id)

            self.assertEqual(True, next(process.options).value)
            process.update(option=option, value=False)
            self.assertEqual(False, next(process.options).value)

            self.assertEqual(False, next(process.options).value)
            process.update(option=option, value='true', coerce_value=True)
            self.assertEqual(True, next(process.options).value)

            process.update(option=option, value=None)
            self.assertEqual(None, next(process.options).value)
