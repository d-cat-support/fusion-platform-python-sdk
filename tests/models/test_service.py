#
# Service model class test file.
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
from fusion_platform.models.model import Model, ModelError
from fusion_platform.models.service import Service, ServiceSchema
from fusion_platform.session import Session, RequestError


class TestService(CustomTestCase):
    """
    Service model tests.
    """

    def test_init(self):
        """
        Test initialisation of the service model class to ensure no exceptions are raised.
        """
        service = Service(Session())
        self.assertIsNotNone(service)

    def test_delete(self):
        """
        Tests that an object can be deleted from the API.
        """
        with open(self.fixture_path('service.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get('organisation_id')
        service_id = content.get(Model.FIELD_ID)
        path = Service._PATH_DELETE.format(organisation_id=organisation_id, service_id=service_id)

        service = Service(session)
        self.assertIsNotNone(service)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{Service._PATH_GET.format(organisation_id=organisation_id, service_id=service_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            service.get(organisation_id=organisation_id, service_id=service_id)
            self.assertIsNotNone(service)
            self.assertEqual(str(service_id), str(service.id))

            with pytest.raises(RequestError):
                mock.delete(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                service.delete()

            with pytest.raises(RequestError):
                mock.delete(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                service.delete()

            mock.delete(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            service.delete()

    def test_get(self):
        """
        Tests that an object can be retrieved from the API.
        """
        with open(self.fixture_path('service.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get('organisation_id')
        service_id = content.get(Model.FIELD_ID)
        path = Service._PATH_GET.format(organisation_id=organisation_id, service_id=service_id)

        service = Service(session)
        self.assertIsNotNone(service)

        with requests_mock.Mocker() as mock:
            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                service.get(organisation_id=organisation_id, service_id=service_id)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                service.get(organisation_id=organisation_id, service_id=service_id)

            with pytest.raises(ModelError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                service.get(organisation_id=organisation_id, service_id=service_id)

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            service.get(organisation_id=organisation_id, service_id=service_id)
            self.assertIsNotNone(service)
            self.assertEqual(str(service_id), str(service.id))

            service.get()
            self.assertIsNotNone(service)
            self.assertEqual(str(service_id), str(service.id))

    def test_model_from_api_id(self):
        """
        Tests that an object can be created from an API endpoint.
        """
        with open(self.fixture_path('service.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get('organisation_id')
        service_id = content.get(Model.FIELD_ID)
        path = Service._PATH_GET.format(organisation_id=organisation_id, service_id=service_id)

        with requests_mock.Mocker() as mock:
            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                Service._model_from_api_id(session, id=service_id, organisation_id=organisation_id)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                Service._model_from_api_id(session, id=service_id, organisation_id=organisation_id)

            with pytest.raises(ModelError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                Service._model_from_api_id(session, id=service_id, organisation_id=organisation_id)

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            service = Service._model_from_api_id(session, id=service_id, organisation_id=organisation_id)
            self.assertIsNotNone(service)
            self.assertEqual(str(service_id), str(service.id))

    def test_models_from_api_ids(self):
        """
        Tests that objects can be created from an API endpoint.
        """
        with open(self.fixture_path('service.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get('organisation_id')
        service_id = content.get(Model.FIELD_ID)
        path = Service._PATH_GET.format(organisation_id=organisation_id, service_id=service_id)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            services = Service._models_from_api_ids(session, [{Model.FIELD_ID: service_id, 'organisation_id': organisation_id}])
            self.assertIsNotNone(services)

            for service in services:
                self.assertEqual(str(service_id), str(service.id))

    def test_models_from_api_path(self):
        """
        Tests that objects can be created from an API endpoint returning a list.
        """
        with open(self.fixture_path('service.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        service_id = content.get(Model.FIELD_ID)
        path = '/path'

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [content]}))
            services = Service._models_from_api_path(session, path)
            self.assertIsNotNone(services)

            for service in services:
                self.assertEqual(str(service_id), str(service.id))

    def test_schema(self):
        """
        Tests that a service model can be loaded into the schema.
        """
        with open(self.fixture_path('service.json'), 'r') as file:
            content = json.loads(file.read())

        model = ServiceSchema().load(content)
        self.assertIsNotNone(model)

        for key in content:
            self.assertEqual(json.dumps(content[key], default=json_default), json.dumps(model[key], default=json_default))

    def test_update(self):
        """
        Tests that an object can be updated to the API.
        """
        with open(self.fixture_path('service.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get('organisation_id')
        service_id = content.get(Model.FIELD_ID)
        path = Service._PATH_PATCH.format(organisation_id=organisation_id, service_id=service_id)
        name = 'Test'

        service = Service(session)
        self.assertIsNotNone(service)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{Service._PATH_GET.format(organisation_id=organisation_id, service_id=service_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            service.get(organisation_id=organisation_id, service_id=service_id)
            self.assertIsNotNone(service)
            self.assertEqual(str(service_id), str(service.id))

            with pytest.raises(RequestError):
                mock.patch(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                service.update(name=name)

            with pytest.raises(RequestError):
                mock.patch(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                service.update(name=name)

            with pytest.raises(ModelError):
                mock.patch(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                service.update(name=name)

            self.assertNotEqual(name, service.name)

            content['name'] = name
            mock.patch(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            service.update(name=name)
            self.assertEqual(name, service.name)
