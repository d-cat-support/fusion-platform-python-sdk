#
# Organisation model class test file.
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
from fusion_platform.common.utilities import json_default, value_to_read_only
from fusion_platform.models.credit import Credit
from fusion_platform.models.data import Data
from fusion_platform.models.model import Model, ModelError
from fusion_platform.models.organisation import Organisation, OrganisationSchema
from fusion_platform.models.process import Process, ProcessSchema
from fusion_platform.models.service import Service
from fusion_platform.session import Session, RequestError


class TestOrganisation(CustomTestCase):
    """
    Organisation model tests.
    """

    def test_init(self):
        """
        Test initialisation of the organisation model class to ensure no exceptions are raised.
        """
        organisation = Organisation(Session())
        self.assertIsNotNone(organisation)
        self._logger.info(organisation)

    def test_create_data_wait(self):
        """
        Tests that a data item can be created for the organisation with waiting for the upload and analysis to complete.
        """
        with open(self.fixture_path('organisation1.json'), 'r') as file:
            organisation_content = json.loads(file.read())

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
        new_path = Data._PATH_NEW.format(organisation_id=organisation_id)
        create_path = Data._PATH_CREATE.format(organisation_id=organisation_id)
        add_file_path = Data._PATH_ADD_FILE.format(organisation_id=organisation_id, data_id=data_id)
        files_path = Data._PATH_FILES.format(organisation_id=organisation_id, data_id=data_id)

        organisation = Organisation(session)
        self.assertIsNotNone(organisation)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{Organisation._PATH_GET.format(organisation_id=organisation_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: organisation_content}))
            organisation.get(id=organisation_id)
            self.assertIsNotNone(organisation)
            self.assertEqual(str(organisation_id), str(organisation.id))

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{new_path}", exc=requests.exceptions.ConnectTimeout)
                organisation.create_data(name, file_type, files, wait=True)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{new_path}", status_code=400)
                organisation.create_data(name, file_type, files, wait=True)

            with pytest.raises(ModelError):
                mock.get(f"{Session.API_URL_DEFAULT}{new_path}", text='{}')
                organisation.create_data(name, file_type, files, wait=True)

            mock.get(f"{Session.API_URL_DEFAULT}{new_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: data_content}))

            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}{create_path}", exc=requests.exceptions.ConnectTimeout)
                organisation.create_data(name, file_type, files, wait=True)

            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}{create_path}", status_code=400)
                organisation.create_data(name, file_type, files, wait=True)

            with pytest.raises(ModelError):
                mock.post(f"{Session.API_URL_DEFAULT}{create_path}", text='{}')
                organisation.create_data(name, file_type, files, wait=True)

            mock.post(f"{Session.API_URL_DEFAULT}{create_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: data_content}))

            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}{add_file_path}", exc=requests.exceptions.ConnectTimeout)
                organisation.create_data(name, file_type, files, wait=True)

            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}{add_file_path}", status_code=400)
                organisation.create_data(name, file_type, files, wait=True)

            with pytest.raises(ModelError):
                mock.post(f"{Session.API_URL_DEFAULT}{add_file_path}", text='{}')
                organisation.create_data(name, file_type, files, wait=True)

            mock.post(f"{Session.API_URL_DEFAULT}{add_file_path}", text=json.dumps(add_file_content))

            with pytest.raises(RequestError):
                mock.put(url, exc=requests.exceptions.ConnectTimeout)
                organisation.create_data(name, file_type, files, wait=True)

            with pytest.raises(RequestError):
                mock.put(url, status_code=400)
                organisation.create_data(name, file_type, files, wait=True)

            mock.put(url, status_code=200)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{files_path}", exc=requests.exceptions.ConnectTimeout)
                organisation.create_data(name, file_type, files, wait=True)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{files_path}", status_code=400)
                organisation.create_data(name, file_type, files, wait=True)

            mock.get(f"{Session.API_URL_DEFAULT}{files_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [file_content]}))
            organisation.create_data(name, file_type, files, wait=True)

    def test_create_data_no_wait(self):
        """
        Tests that a data item can be created for the organisation without waiting for the upload and analysis to complete
        """
        with open(self.fixture_path('organisation1.json'), 'r') as file:
            organisation_content = json.loads(file.read())

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
        new_path = Data._PATH_NEW.format(organisation_id=organisation_id)
        create_path = Data._PATH_CREATE.format(organisation_id=organisation_id)
        add_file_path = Data._PATH_ADD_FILE.format(organisation_id=organisation_id, data_id=data_id)
        files_path = Data._PATH_FILES.format(organisation_id=organisation_id, data_id=data_id)

        organisation = Organisation(session)
        self.assertIsNotNone(organisation)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{Organisation._PATH_GET.format(organisation_id=organisation_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: organisation_content}))
            organisation.get(id=organisation_id)
            self.assertIsNotNone(organisation)
            self.assertEqual(str(organisation_id), str(organisation.id))

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{new_path}", exc=requests.exceptions.ConnectTimeout)
                organisation.create_data(name, file_type, files, wait=True)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{new_path}", status_code=400)
                organisation.create_data(name, file_type, files, wait=True)

            with pytest.raises(ModelError):
                mock.get(f"{Session.API_URL_DEFAULT}{new_path}", text='{}')
                organisation.create_data(name, file_type, files, wait=True)

            mock.get(f"{Session.API_URL_DEFAULT}{new_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: data_content}))

            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}{create_path}", exc=requests.exceptions.ConnectTimeout)
                organisation.create_data(name, file_type, files)

            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}{create_path}", status_code=400)
                organisation.create_data(name, file_type, files)

            with pytest.raises(ModelError):
                mock.post(f"{Session.API_URL_DEFAULT}{create_path}", text='{}')
                organisation.create_data(name, file_type, files)

            mock.post(f"{Session.API_URL_DEFAULT}{create_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: data_content}))

            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}{add_file_path}", exc=requests.exceptions.ConnectTimeout)
                organisation.create_data(name, file_type, files)

            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}{add_file_path}", status_code=400)
                organisation.create_data(name, file_type, files)

            with pytest.raises(ModelError):
                mock.post(f"{Session.API_URL_DEFAULT}{add_file_path}", text='{}')
                organisation.create_data(name, file_type, files)

            mock.post(f"{Session.API_URL_DEFAULT}{add_file_path}", text=json.dumps(add_file_content))

            with pytest.raises(RequestError):
                mock.put(url, exc=requests.exceptions.ConnectTimeout)
                data = organisation.create_data(name, file_type, files)

                while not data.create_complete():
                    sleep(0.1)

            with pytest.raises(RequestError):
                mock.put(url, status_code=400)
                data = organisation.create_data(name, file_type, files)

                while not data.create_complete():
                    sleep(0.1)

            mock.put(url, status_code=200)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{files_path}", exc=requests.exceptions.ConnectTimeout)
                data = organisation.create_data(name, file_type, files)

                while not data.create_complete():
                    sleep(0.1)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{files_path}", status_code=400)
                data = organisation.create_data(name, file_type, files)

                while not data.create_complete():
                    sleep(0.1)

            mock.get(f"{Session.API_URL_DEFAULT}{files_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [file_content]}))
            data = organisation.create_data(name, file_type, files)

            while not data.create_complete():
                sleep(0.1)

    def test_credit(self):
        """
        Tests the credit property retrieves the organisations credit model.
        """
        with open(self.fixture_path('organisation1.json'), 'r') as file:
            organisation_content = json.loads(file.read())

        with open(self.fixture_path('credit.json'), 'r') as file:
            credit_content = json.loads(file.read())

        session = Session()
        organisation_id = organisation_content.get(Model._FIELD_ID)
        credit_id = credit_content.get(Model._FIELD_ID)
        path = Credit._PATH_GET.format(credit_id=credit_id, organisation_id=organisation_id)

        organisation = Organisation(session)
        self.assertIsNotNone(organisation)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{Organisation._PATH_GET.format(organisation_id=organisation_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: organisation_content}))
            organisation.get(id=organisation_id)
            self.assertIsNotNone(organisation)
            self.assertEqual(str(organisation_id), str(organisation.id))

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                organisation.credit

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                organisation.credit

            with pytest.raises(ModelError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                organisation.credit

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: credit_content}))
            credit = organisation.credit
            self.assertIsNotNone(credit)
            self.assertEqual(str(credit_id), str(credit.id))

    def test_data(self):
        """
        Tests the data property retrieves data items.
        """
        with open(self.fixture_path('organisation1.json'), 'r') as file:
            organisation_content = json.loads(file.read())

        with open(self.fixture_path('data.json'), 'r') as file:
            data_content = json.loads(file.read())

        session = Session()
        organisation_id = organisation_content.get(Model._FIELD_ID)
        path = Organisation._PATH_DATA.format(organisation_id=organisation_id)

        organisation = Organisation(session)
        self.assertIsNotNone(organisation)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{Organisation._PATH_GET.format(organisation_id=organisation_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: organisation_content}))
            organisation.get(id=organisation_id)
            self.assertIsNotNone(organisation)
            self.assertEqual(str(organisation_id), str(organisation.id))

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                next(organisation.data)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                next(organisation.data)

            with pytest.raises(StopIteration):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                next(organisation.data)

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [data_content]}))

            for data in organisation.data:
                self.assertEqual(str(organisation_id), str(data.organisation_id))

    def test_delete(self):
        """
        Tests that an object can be deleted from the API.
        """
        with open(self.fixture_path('organisation1.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get(Model._FIELD_ID)
        path = Organisation._PATH_DELETE.format(organisation_id=organisation_id)

        organisation = Organisation(session)
        self.assertIsNotNone(organisation)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{Organisation._PATH_GET.format(organisation_id=organisation_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            organisation.get(id=organisation_id)
            self.assertIsNotNone(organisation)
            self.assertEqual(str(organisation_id), str(organisation.id))

            with pytest.raises(RequestError):
                mock.delete(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                organisation.delete()

            with pytest.raises(RequestError):
                mock.delete(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                organisation.delete()

            mock.delete(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            organisation.delete()

    def test_find_data(self):
        """
        Tests the finding of data items.
        """
        with open(self.fixture_path('organisation1.json'), 'r') as file:
            organisation_content = json.loads(file.read())

        with open(self.fixture_path('data.json'), 'r') as file:
            data_content = json.loads(file.read())

        session = Session()
        organisation_id = organisation_content.get(Model._FIELD_ID)
        data_id = data_content.get(Model._FIELD_ID)
        name = data_content.get(Model._FIELD_NAME)
        search = data_content.get(Model._FIELD_NAME)
        path = Organisation._PATH_DATA.format(organisation_id=organisation_id)

        organisation = Organisation(session)
        self.assertIsNotNone(organisation)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{Organisation._PATH_GET.format(organisation_id=organisation_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: organisation_content}))
            organisation.get(id=organisation_id)
            self.assertIsNotNone(organisation)
            self.assertEqual(str(organisation_id), str(organisation.id))

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                organisation.find_data()

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                organisation.find_data()

            with pytest.raises(StopIteration):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                first, generator = organisation.find_data()
                self.assertIsNone(first)
                next(generator)

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [data_content]}))
            first, generator = organisation.find_data(id=data_id, name=name, search=search)
            self.assertIsNotNone(first)

            for data in generator:
                self.assertEqual(first.attributes, data.attributes)

    def test_find_dispatchers(self):
        """
        Tests the finding of dispatcher services.
        """
        with open(self.fixture_path('organisation1.json'), 'r') as file:
            organisation_content = json.loads(file.read())

        with open(self.fixture_path('service.json'), 'r') as file:
            service_content = json.loads(file.read())

        session = Session()
        organisation_id = organisation_content.get(Model._FIELD_ID)
        service_id = service_content.get(Model._FIELD_ID)
        ssd_id = service_content.get(Model._FIELD_SSD_ID)
        name = service_content.get(Model._FIELD_NAME)
        keyword = service_content.get(Model._FIELD_KEYWORDS)[0]
        search = service_content.get(Model._FIELD_NAME)
        path = Organisation._PATH_DISPATCHERS.format(organisation_id=organisation_id)

        organisation = Organisation(session)
        self.assertIsNotNone(organisation)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{Organisation._PATH_GET.format(organisation_id=organisation_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: organisation_content}))
            organisation.get(id=organisation_id)
            self.assertIsNotNone(organisation)
            self.assertEqual(str(organisation_id), str(organisation.id))

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                organisation.find_dispatchers()

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                organisation.find_dispatchers()

            with pytest.raises(StopIteration):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                first, generator = organisation.find_dispatchers()
                self.assertIsNone(first)
                next(generator)

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [service_content]}))
            first, generator = organisation.find_dispatchers(id=service_id, ssd_id=ssd_id, name=name, keyword=keyword, search=search)
            self.assertIsNotNone(first)

            for service in generator:
                self.assertEqual(first.attributes, service.attributes)

    def test_find_processes(self):
        """
        Tests the finding of processes.
        """
        with open(self.fixture_path('organisation1.json'), 'r') as file:
            organisation_content = json.loads(file.read())

        with open(self.fixture_path('process.json'), 'r') as file:
            process_content = json.loads(file.read())

        with open(self.fixture_path('extras.json'), 'r') as file:
            extras = json.loads(file.read())

        session = Session()
        organisation_id = organisation_content.get(Model._FIELD_ID)
        process_id = process_content.get(Model._FIELD_ID)
        name = process_content.get(Model._FIELD_NAME)
        search = process_content.get(Model._FIELD_NAME)
        path = Organisation._PATH_PROCESSES.format(organisation_id=organisation_id)

        organisation = Organisation(session)
        self.assertIsNotNone(organisation)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{Organisation._PATH_GET.format(organisation_id=organisation_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: organisation_content}))
            organisation.get(id=organisation_id)
            self.assertIsNotNone(organisation)
            self.assertEqual(str(organisation_id), str(organisation.id))

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                organisation.find_processes()

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                organisation.find_processes()

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
            organisation.find_processes()

            with pytest.raises(StopIteration):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_EXTRAS: {Model._FIELD_DISPATCHERS: extras}}))
                first, generator = organisation.find_processes()
                self.assertIsNone(first)
                next(generator)

            mock.get(f"{Session.API_URL_DEFAULT}{path}",
                     text=json.dumps({Model._RESPONSE_KEY_LIST: [process_content], Model._RESPONSE_KEY_EXTRAS: {Model._FIELD_DISPATCHERS: extras}}))
            first, generator = organisation.find_processes(id=process_id, name=name, search=search)
            self.assertIsNotNone(first)

            for process in generator:
                self.assertEqual(json.dumps(first.attributes, default=json_default),
                                 json.dumps(process.attributes, default=json_default))  # JSON to ignore available dispatchers.

    def test_find_services(self):
        """
        Tests the finding of services.
        """
        with open(self.fixture_path('organisation1.json'), 'r') as file:
            organisation_content = json.loads(file.read())

        with open(self.fixture_path('service.json'), 'r') as file:
            service_content = json.loads(file.read())

        session = Session()
        organisation_id = organisation_content.get(Model._FIELD_ID)
        service_id = service_content.get(Model._FIELD_ID)
        ssd_id = service_content.get(Model._FIELD_SSD_ID)
        name = service_content.get(Model._FIELD_NAME)
        keyword = service_content.get(Model._FIELD_KEYWORDS)[0]
        search = service_content.get(Model._FIELD_NAME)
        path = Organisation._PATH_SERVICES.format(organisation_id=organisation_id)

        organisation = Organisation(session)
        self.assertIsNotNone(organisation)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{Organisation._PATH_GET.format(organisation_id=organisation_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: organisation_content}))
            organisation.get(id=organisation_id)
            self.assertIsNotNone(organisation)
            self.assertEqual(str(organisation_id), str(organisation.id))

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                organisation.find_services()

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                organisation.find_services()

            with pytest.raises(StopIteration):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                first, generator = organisation.find_services()
                self.assertIsNone(first)
                next(generator)

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [service_content]}))
            first, generator = organisation.find_services(id=service_id, ssd_id=ssd_id, name=name, keyword=keyword, search=search)
            self.assertIsNotNone(first)

            for service in generator:
                self.assertEqual(first.attributes, service.attributes)

    def test_get(self):
        """
        Tests that an object can be retrieved from the API.
        """
        with open(self.fixture_path('organisation1.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get(Model._FIELD_ID)
        path = Organisation._PATH_GET.format(organisation_id=organisation_id)

        organisation = Organisation(session)
        self.assertIsNotNone(organisation)

        with requests_mock.Mocker() as mock:
            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                organisation.get(id=organisation_id)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                organisation.get(id=organisation_id)

            with pytest.raises(ModelError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                organisation.get(id=organisation_id)

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            organisation.get(id=organisation_id)
            self.assertIsNotNone(organisation)
            self.assertEqual(str(organisation_id), str(organisation.id))

            organisation.get()
            self.assertIsNotNone(organisation)
            self.assertEqual(str(organisation_id), str(organisation.id))

    def test_model_from_api_id(self):
        """
        Tests that an object can be created from an API endpoint.
        """
        with open(self.fixture_path('organisation1.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get(Model._FIELD_ID)
        path = Organisation._PATH_GET.format(organisation_id=organisation_id)

        with requests_mock.Mocker() as mock:
            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                Organisation._model_from_api_id(session, id=organisation_id)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                Organisation._model_from_api_id(session, id=organisation_id)

            with pytest.raises(ModelError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                Organisation._model_from_api_id(session, id=organisation_id)

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            organisation = Organisation._model_from_api_id(session, id=organisation_id)
            self.assertIsNotNone(organisation)
            self.assertEqual(str(organisation_id), str(organisation.id))

    def test_models_from_api_ids(self):
        """
        Tests that objects can be created from an API endpoint.
        """
        with open(self.fixture_path('organisation1.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get(Model._FIELD_ID)
        path = Organisation._PATH_GET.format(organisation_id=organisation_id)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            organisations = Organisation._models_from_api_ids(session, [{Model._FIELD_ID: organisation_id}])
            self.assertIsNotNone(organisations)

            for organisation in organisations:
                self.assertEqual(str(organisation_id), str(organisation.id))

    def test_models_from_api_path(self):
        """
        Tests that objects can be created from an API endpoint returning a list.
        """
        with open(self.fixture_path('organisation1.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get(Model._FIELD_ID)
        path = '/path'

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [content]}))
            organisations = Organisation._models_from_api_path(session, path)
            self.assertIsNotNone(organisations)

            for organisation in organisations:
                self.assertEqual(str(organisation_id), str(organisation.id))

    def test_new_process(self):
        """
        Tests that a template new process can be created from an API endpoint with validation using a Marshmallow schema.
        """
        with open(self.fixture_path('organisation1.json'), 'r') as file:
            organisation_content = json.loads(file.read())

        with open(self.fixture_path('process.json'), 'r') as file:
            process_content = json.loads(file.read())

        with open(self.fixture_path('extras.json'), 'r') as file:
            extras = json.loads(file.read())

        wrong_content = {}

        for key in process_content:
            wrong_content[f"new_{key}"] = process_content[key]

        with open(self.fixture_path('service.json'), 'r') as file:
            service_content = json.loads(file.read())

        session = Session()
        organisation_id = organisation_content.get(Model._FIELD_ID)
        service_id = service_content.get(Model._FIELD_ID)
        path = Process._PATH_NEW.format(organisation_id=organisation_id)

        organisation = Organisation(session)
        self.assertIsNotNone(organisation)

        service = Service(session)
        self.assertIsNotNone(service)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{Organisation._PATH_GET.format(organisation_id=organisation_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: organisation_content}))
            organisation.get(id=organisation_id)
            self.assertIsNotNone(organisation)
            self.assertEqual(str(organisation_id), str(organisation.id))

            mock.get(f"{Session.API_URL_DEFAULT}{Service._PATH_GET.format(organisation_id=organisation_id, service_id=service_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: service_content}))
            service.get(organisation_id=organisation_id, service_id=service_id)
            self.assertIsNotNone(service)
            self.assertEqual(str(service_id), str(service.id))

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                organisation.new_process('Test', service)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                organisation.new_process('Test', service)

            with pytest.raises(ModelError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                organisation.new_process('Test', service)

            mock.get(f"{Session.API_URL_DEFAULT}{path}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: wrong_content, Model._RESPONSE_KEY_EXTRAS: {Model._FIELD_DISPATCHERS: extras}}))
            organisation.new_process('Test', service)

            mock.get(f"{Session.API_URL_DEFAULT}{path}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content, Model._RESPONSE_KEY_EXTRAS: {Model._FIELD_DISPATCHERS: extras}}))
            process = organisation.new_process('Test', service)

            schema = ProcessSchema()

            for key in process_content:
                if (Model._METADATA_HIDE not in schema.fields[key].metadata) and (process_content[key] is not None):
                    self.assertEqual(json.dumps(value_to_read_only(process_content[key]), default=json_default),
                                     json.dumps(getattr(process, key), default=json_default))

            for dispatcher in process.available_dispatchers:
                self.assertIsNotNone(dispatcher)

    def test_own_services(self):
        """
        Tests the own services property retrieves service items.
        """
        with open(self.fixture_path('organisation1.json'), 'r') as file:
            organisation_content = json.loads(file.read())

        with open(self.fixture_path('service.json'), 'r') as file:
            service_content = json.loads(file.read())

        session = Session()
        organisation_id = organisation_content.get(Model._FIELD_ID)
        path = Organisation._PATH_OWN_SERVICES.format(organisation_id=organisation_id)

        organisation = Organisation(session)
        self.assertIsNotNone(organisation)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{Organisation._PATH_GET.format(organisation_id=organisation_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: organisation_content}))
            organisation.get(id=organisation_id)
            self.assertIsNotNone(organisation)
            self.assertEqual(str(organisation_id), str(organisation.id))

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                next(organisation.own_services)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                next(organisation.own_services)

            with pytest.raises(StopIteration):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                next(organisation.own_services)

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [service_content]}))

            for service in organisation.own_services:
                self.assertEqual(str(organisation_id), str(service.organisation_id))

    def test_processes(self):
        """
        Tests the processes property retrieves service items.
        """
        with open(self.fixture_path('organisation1.json'), 'r') as file:
            organisation_content = json.loads(file.read())

        with open(self.fixture_path('process.json'), 'r') as file:
            process_content = json.loads(file.read())

        with open(self.fixture_path('extras.json'), 'r') as file:
            extras = json.loads(file.read())

        session = Session()
        organisation_id = organisation_content.get(Model._FIELD_ID)
        path = Organisation._PATH_PROCESSES.format(organisation_id=organisation_id)

        organisation = Organisation(session)
        self.assertIsNotNone(organisation)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{Organisation._PATH_GET.format(organisation_id=organisation_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: organisation_content}))
            organisation.get(id=organisation_id)
            self.assertIsNotNone(organisation)
            self.assertEqual(str(organisation_id), str(organisation.id))

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                next(organisation.processes)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                next(organisation.processes)

            with pytest.raises(StopIteration):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                next(organisation.processes)

            with pytest.raises(StopIteration):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_EXTRAS: {Model._FIELD_DISPATCHERS: extras}}))
                next(organisation.processes)

            mock.get(f"{Session.API_URL_DEFAULT}{path}",
                     text=json.dumps({Model._RESPONSE_KEY_LIST: [process_content], Model._RESPONSE_KEY_EXTRAS: {Model._FIELD_DISPATCHERS: extras}}))

            for process in organisation.processes:
                self.assertEqual(str(organisation_id), str(process.organisation_id))

    def test_schema(self):
        """
        Tests that a organisation model can be loaded into the schema.
        """
        with open(self.fixture_path('organisation1.json'), 'r') as file:
            content = json.loads(file.read())

        model = OrganisationSchema().load(content)
        self.assertIsNotNone(model)

        for key in content:
            self.assertEqual(json.dumps(content[key], default=json_default), json.dumps(model[key], default=json_default))

    def test_services(self):
        """
        Tests the services property retrieves service items.
        """
        with open(self.fixture_path('organisation1.json'), 'r') as file:
            organisation_content = json.loads(file.read())

        with open(self.fixture_path('service.json'), 'r') as file:
            service_content = json.loads(file.read())

        session = Session()
        organisation_id = organisation_content.get(Model._FIELD_ID)
        path = Organisation._PATH_SERVICES.format(organisation_id=organisation_id)

        organisation = Organisation(session)
        self.assertIsNotNone(organisation)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{Organisation._PATH_GET.format(organisation_id=organisation_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: organisation_content}))
            organisation.get(id=organisation_id)
            self.assertIsNotNone(organisation)
            self.assertEqual(str(organisation_id), str(organisation.id))

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                next(organisation.services)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                next(organisation.services)

            with pytest.raises(StopIteration):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                next(organisation.services)

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [service_content]}))

            for service in organisation.services:
                self.assertEqual(str(organisation_id), str(service.organisation_id))

    def test_update(self):
        """
        Tests that an object can be updated to the API.
        """
        with open(self.fixture_path('organisation1.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get(Model._FIELD_ID)
        path = Organisation._PATH_PATCH.format(organisation_id=organisation_id)
        name = 'Test'

        organisation = Organisation(session)
        self.assertIsNotNone(organisation)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{Organisation._PATH_GET.format(organisation_id=organisation_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            organisation.get(id=organisation_id)
            self.assertIsNotNone(organisation)
            self.assertEqual(str(organisation_id), str(organisation.id))

            with pytest.raises(RequestError):
                mock.patch(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                organisation.update(name=name)

            with pytest.raises(RequestError):
                mock.patch(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                organisation.update(name=name)

            with pytest.raises(ModelError):
                mock.patch(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                organisation.update(name=name)

            self.assertNotEqual(name, organisation.name)

            content['name'] = name
            mock.patch(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            organisation.update(name=name)
            self.assertEqual(name, organisation.name)
