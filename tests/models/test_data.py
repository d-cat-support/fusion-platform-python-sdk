#
# Data model class test file.
#
# @author Matthew Casey
#
# (c) Digital Content Analysis Technology Ltd 2022
#

import json
import pytest
import requests
import requests_mock
from time import sleep
import uuid

from tests.custom_test_case import CustomTestCase

import fusion_platform
from fusion_platform.common.utilities import json_default
from fusion_platform.models.model import Model, ModelError
from fusion_platform.models.data import Data, DataSchema
from fusion_platform.session import Session, RequestError


class TestData(CustomTestCase):
    """
    Data model tests.
    """

    def test_init(self):
        """
        Test initialisation of the data model class to ensure no exceptions are raised.
        """
        data = Data(Session())
        self.assertIsNotNone(data)

    def test_create_wait(self):
        """
        Tests that a data item can be created with waiting for the upload and analysis to complete.
        """
        with open(self.fixture_path('data.json'), 'r') as file:
            data_content = json.loads(file.read())

        with open(self.fixture_path('data_file.json'), 'r') as file:
            file_content = json.loads(file.read())

        url = 'https://upload.com/test'
        add_file_content = {Model._RESPONSE_KEY_EXTRAS: {Data._RESPONSE_KEY_FILE: str(uuid.uuid4()), Data._RESPONSE_KEY_URL: url}}

        session = Session()
        organisation_id = data_content.get('organisation_id')
        data_id = data_content.get(Model._FIELD_ID)
        name = 'Glasgow'
        file_type = fusion_platform.FILE_TYPE_GEOJSON,
        files = [fusion_platform.EXAMPLE_GLASGOW_FILE]
        create_path = Data._PATH_CREATE.format(organisation_id=organisation_id)
        add_file_path = Data._PATH_ADD_FILE.format(organisation_id=organisation_id, data_id=data_id)
        files_path = Data._PATH_FILES.format(organisation_id=organisation_id, data_id=data_id)

        data = Data(session)
        self.assertIsNotNone(data)

        data._set_model(data_content)

        with requests_mock.Mocker() as mock:
            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}{create_path}", exc=requests.exceptions.ConnectTimeout)
                data._Model__persisted = False
                data._create(name, file_type, files, wait=True)

            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}{create_path}", status_code=400)
                data._Model__persisted = False
                data._create(name, file_type, files, wait=True)

            with pytest.raises(ModelError):
                mock.post(f"{Session.API_URL_DEFAULT}{create_path}", text='{}')
                data._Model__persisted = False
                data._create(name, file_type, files, wait=True)

            mock.post(f"{Session.API_URL_DEFAULT}{create_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: data_content}))

            with pytest.raises(ModelError):
                data._create(name, file_type, ['does_not_exist'], wait=True)

            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}{add_file_path}", exc=requests.exceptions.ConnectTimeout)
                data._Model__persisted = False
                data._create(name, file_type, files, wait=True)

            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}{add_file_path}", status_code=400)
                data._Model__persisted = False
                data._create(name, file_type, files, wait=True)

            with pytest.raises(ModelError):
                mock.post(f"{Session.API_URL_DEFAULT}{add_file_path}", text='{}')
                data._Model__persisted = False
                data._create(name, file_type, files, wait=True)

            mock.post(f"{Session.API_URL_DEFAULT}{add_file_path}", text=json.dumps(add_file_content))

            with pytest.raises(RequestError):
                mock.put(url, exc=requests.exceptions.ConnectTimeout)
                data._Model__persisted = False
                data._create(name, file_type, files, wait=True)

            with pytest.raises(RequestError):
                mock.put(url, status_code=400)
                data._Model__persisted = False
                data._create(name, file_type, files, wait=True)

            mock.put(url, status_code=200)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{files_path}", exc=requests.exceptions.ConnectTimeout)
                data._Model__persisted = False
                data._create(name, file_type, files, wait=True)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{files_path}", status_code=400)
                data._Model__persisted = False
                data._create(name, file_type, files, wait=True)

            mock.get(f"{Session.API_URL_DEFAULT}{files_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [file_content]}))
            data._Model__persisted = False
            data._create(name, file_type, files, wait=True)

    def test_create_no_wait(self):
        """
        Tests that a data item can be created without waiting for the upload and analysis to complete
        """
        with open(self.fixture_path('data.json'), 'r') as file:
            data_content = json.loads(file.read())

        with open(self.fixture_path('data_file.json'), 'r') as file:
            file_content = json.loads(file.read())

        url = 'https://upload.com/test'
        add_file_content = {Model._RESPONSE_KEY_EXTRAS: {Data._RESPONSE_KEY_FILE: str(uuid.uuid4()), Data._RESPONSE_KEY_URL: url}}

        session = Session()
        organisation_id = data_content.get('organisation_id')
        data_id = data_content.get(Model._FIELD_ID)
        name = 'Glasgow'
        file_type = fusion_platform.FILE_TYPE_GEOJSON,
        files = [fusion_platform.EXAMPLE_GLASGOW_FILE]
        create_path = Data._PATH_CREATE.format(organisation_id=organisation_id)
        add_file_path = Data._PATH_ADD_FILE.format(organisation_id=organisation_id, data_id=data_id)
        files_path = Data._PATH_FILES.format(organisation_id=organisation_id, data_id=data_id)

        data = Data(session)
        self.assertIsNotNone(data)

        data._set_model(data_content)

        with requests_mock.Mocker() as mock:

            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}{create_path}", exc=requests.exceptions.ConnectTimeout)
                data._Model__persisted = False
                data._create(name, file_type, files)

            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}{create_path}", status_code=400)
                data._Model__persisted = False
                data._create(name, file_type, files)

            with pytest.raises(ModelError):
                mock.post(f"{Session.API_URL_DEFAULT}{create_path}", text='{}')
                data._Model__persisted = False
                data._create(name, file_type, files)

            mock.post(f"{Session.API_URL_DEFAULT}{create_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: data_content}))

            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}{add_file_path}", exc=requests.exceptions.ConnectTimeout)
                data._Model__persisted = False
                data._create(name, file_type, files)

            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}{add_file_path}", status_code=400)
                data._Model__persisted = False
                data._create(name, file_type, files)

            with pytest.raises(ModelError):
                mock.post(f"{Session.API_URL_DEFAULT}{add_file_path}", text='{}')
                data._Model__persisted = False
                data._create(name, file_type, files)

            mock.post(f"{Session.API_URL_DEFAULT}{add_file_path}", text=json.dumps(add_file_content))

            with pytest.raises(RequestError):
                mock.put(url, exc=requests.exceptions.ConnectTimeout)
                data._Model__persisted = False
                data._create(name, file_type, files)

                while not data.create_complete():
                    sleep(0.1)

            with pytest.raises(RequestError):
                mock.put(url, status_code=400)
                data._Model__persisted = False
                data._create(name, file_type, files)

                while not data.create_complete():
                    sleep(0.1)

            mock.put(url, status_code=200)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{files_path}", exc=requests.exceptions.ConnectTimeout)
                data._Model__persisted = False
                data._create(name, file_type, files)

                while not data.create_complete():
                    sleep(0.1)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{files_path}", status_code=400)
                data._Model__persisted = False
                data._create(name, file_type, files)

                while not data.create_complete():
                    sleep(0.1)

            mock.get(f"{Session.API_URL_DEFAULT}{files_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [file_content]}))
            data._Model__persisted = False
            data._create(name, file_type, files)

            while not data.create_complete():
                sleep(0.1)

    def test_delete(self):
        """
        Tests that an object can be deleted from the API.
        """
        with open(self.fixture_path('data.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get('organisation_id')
        data_id = content.get(Model._FIELD_ID)
        path = Data._PATH_DELETE.format(organisation_id=organisation_id, data_id=data_id)

        data = Data(session)
        self.assertIsNotNone(data)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{Data._PATH_GET.format(organisation_id=organisation_id, data_id=data_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            data.get(organisation_id=organisation_id, data_id=data_id)
            self.assertIsNotNone(data)
            self.assertEqual(str(data_id), str(data.id))

            with pytest.raises(RequestError):
                mock.delete(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                data.delete()

            with pytest.raises(RequestError):
                mock.delete(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                data.delete()

            mock.delete(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            data.delete()

    def test_files(self):
        """
        Tests the files property retrieves file items.
        """
        with open(self.fixture_path('data.json'), 'r') as file:
            data_content = json.loads(file.read())

        with open(self.fixture_path('data_file.json'), 'r') as file:
            file_content = json.loads(file.read())

        session = Session()
        organisation_id = data_content.get('organisation_id')
        data_id = data_content.get(Model._FIELD_ID)
        path = Data._PATH_FILES.format(organisation_id=organisation_id, data_id=data_id)

        data = Data(session)
        self.assertIsNotNone(data)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{Data._PATH_GET.format(organisation_id=organisation_id, data_id=data_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: data_content}))
            data.get(organisation_id=organisation_id, data_id=data_id)
            self.assertIsNotNone(data)
            self.assertEqual(str(data_id), str(data.id))

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                next(data.files)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                next(data.files)

            with pytest.raises(StopIteration):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                next(data.files)

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [file_content]}))

            for file in data.files:
                self.assertEqual(str(data_id), str(file.data_id))
                self.assertEqual(str(organisation_id), str(file.organisation_id))

    def test_get(self):
        """
        Tests that an object can be retrieved from the API.
        """
        with open(self.fixture_path('data.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get('organisation_id')
        data_id = content.get(Model._FIELD_ID)
        path = Data._PATH_GET.format(organisation_id=organisation_id, data_id=data_id)

        data = Data(session)
        self.assertIsNotNone(data)

        with requests_mock.Mocker() as mock:
            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                data.get(organisation_id=organisation_id, data_id=data_id)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                data.get(organisation_id=organisation_id, data_id=data_id)

            with pytest.raises(ModelError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                data.get(organisation_id=organisation_id, data_id=data_id)

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            data.get(organisation_id=organisation_id, data_id=data_id)
            self.assertIsNotNone(data)
            self.assertEqual(str(data_id), str(data.id))

            data.get()
            self.assertIsNotNone(data)
            self.assertEqual(str(data_id), str(data.id))

    def test_model_from_api_id(self):
        """
        Tests that an object can be created from an API endpoint.
        """
        with open(self.fixture_path('data.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get('organisation_id')
        data_id = content.get(Model._FIELD_ID)
        path = Data._PATH_GET.format(organisation_id=organisation_id, data_id=data_id)

        with requests_mock.Mocker() as mock:
            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                Data._model_from_api_id(session, id=data_id, organisation_id=organisation_id)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                Data._model_from_api_id(session, id=data_id, organisation_id=organisation_id)

            with pytest.raises(ModelError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                Data._model_from_api_id(session, id=data_id, organisation_id=organisation_id)

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            data = Data._model_from_api_id(session, id=data_id, organisation_id=organisation_id)
            self.assertIsNotNone(data)
            self.assertEqual(str(data_id), str(data.id))

    def test_models_from_api_ids(self):
        """
        Tests that objects can be created from an API endpoint.
        """
        with open(self.fixture_path('data.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get('organisation_id')
        data_id = content.get(Model._FIELD_ID)
        path = Data._PATH_GET.format(organisation_id=organisation_id, data_id=data_id)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            data_items = Data._models_from_api_ids(session, [{Model._FIELD_ID: data_id, 'organisation_id': organisation_id}])
            self.assertIsNotNone(data_items)

            for data in data_items:
                self.assertEqual(str(data_id), str(data.id))

    def test_models_from_api_path(self):
        """
        Tests that objects can be created from an API endpoint returning a list.
        """
        with open(self.fixture_path('data.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        data_id = content.get(Model._FIELD_ID)
        path = '/path'

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [content]}))
            data_items = Data._models_from_api_path(session, path)
            self.assertIsNotNone(data_items)

            for data in data_items:
                self.assertEqual(str(data_id), str(data.id))

    def test_new(self):
        """
        Tests that a template new object can be created from an API endpoint with validation using a Marshmallow schema.
        """
        with open(self.fixture_path('data.json'), 'r') as file:
            content = json.loads(file.read())

        wrong_content = {}

        for key in content:
            wrong_content[f"new_{key}"] = content[key]

        session = Session()
        organisation_id = content.get('organisation_id')
        path = Data._PATH_NEW.format(organisation_id=organisation_id)

        data = Data(session)
        self.assertIsNotNone(data)

        with requests_mock.Mocker() as mock:

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                data._new(organisation_id=organisation_id)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                data._new(organisation_id=organisation_id)

            with pytest.raises(ModelError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                data._new(organisation_id=organisation_id)

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: wrong_content}))
            data._new(organisation_id=organisation_id)

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            data._new(organisation_id=organisation_id)

            schema = DataSchema()

            for key in content:
                if (Model._METADATA_HIDE not in schema.fields[key].metadata) and (content[key] is not None):
                    self.assertEqual(json.dumps(content[key], default=json_default), json.dumps(getattr(data, key), default=json_default))

    def test_schema(self):
        """
        Tests that a data model can be loaded into the schema.
        """
        with open(self.fixture_path('data.json'), 'r') as file:
            content = json.loads(file.read())

        model = DataSchema().load(content)
        self.assertIsNotNone(model)

        for key in content:
            self.assertEqual(json.dumps(content[key], default=json_default), json.dumps(model[key], default=json_default))

    def test_update(self):
        """
        Tests that an object can be updated to the API.
        """
        with open(self.fixture_path('data.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get('organisation_id')
        data_id = content.get(Model._FIELD_ID)
        path = Data._PATH_PATCH.format(organisation_id=organisation_id, data_id=data_id)
        name = 'Test'

        data = Data(session)
        self.assertIsNotNone(data)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{Data._PATH_GET.format(organisation_id=organisation_id, data_id=data_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            data.get(organisation_id=organisation_id, data_id=data_id)
            self.assertIsNotNone(data)
            self.assertEqual(str(data_id), str(data.id))

            with pytest.raises(RequestError):
                mock.patch(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                data.update(name=name)

            with pytest.raises(RequestError):
                mock.patch(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                data.update(name=name)

            with pytest.raises(ModelError):
                mock.patch(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                data.update(name=name)

            self.assertNotEqual(name, data.name)

            content['name'] = name
            mock.patch(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            data.update(name=name)
            self.assertEqual(name, data.name)
