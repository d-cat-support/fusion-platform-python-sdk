#
# User model class test file.
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
from fusion_platform.models.organisation import Organisation
from fusion_platform.models.user import User, UserSchema
from fusion_platform.session import Session, RequestError


class TestUser(CustomTestCase):
    """
    User model tests.
    """

    def test_init(self):
        """
        Test initialisation of the user model class to ensure no exceptions are raised.
        """
        user = User(Session())
        self.assertIsNotNone(user)

    def test_change_password(self):
        """
        Tests change password.
        """
        with open(self.fixture_path('user.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        user_id = content.get(Model._FIELD_ID)
        path = User._PATH_CHANGE_PASSWORD.format(user_id=user_id)
        old_password = 'old'
        new_password = 'new'

        user = User(session)
        self.assertIsNotNone(user)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{User._PATH_GET.format(user_id=user_id)}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            user.get(id=user_id)
            self.assertIsNotNone(user)
            self.assertEqual(str(user_id), str(user.id))

            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                user.change_password(old=old_password, new=new_password)

            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                user.change_password(old=old_password, new=new_password)

            adapter = mock.post(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            user.change_password(old=old_password, new=new_password)

            self.assertEqual({'User': {'old_password': old_password, 'new_password': new_password}}, json.loads(adapter.last_request.text))

    def test_delete(self):
        """
        Tests that an object can be deleted from the API.
        """
        with open(self.fixture_path('user.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        user_id = content.get(Model._FIELD_ID)
        path = User._PATH_DELETE.format(user_id=user_id)

        user = User(session)
        self.assertIsNotNone(user)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{User._PATH_GET.format(user_id=user_id)}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            user.get(id=user_id)
            self.assertIsNotNone(user)
            self.assertEqual(str(user_id), str(user.id))

            with pytest.raises(RequestError):
                mock.delete(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                user.delete()

            with pytest.raises(RequestError):
                mock.delete(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                user.delete()

            mock.delete(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            user.delete()

    def test_get(self):
        """
        Tests that an object can be retrieved from the API.
        """
        with open(self.fixture_path('user.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        user_id = content.get(Model._FIELD_ID)
        path = User._PATH_GET.format(user_id=user_id)

        user = User(session)
        self.assertIsNotNone(user)

        with requests_mock.Mocker() as mock:
            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                user.get(id=user_id)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                user.get(id=user_id)

            with pytest.raises(ModelError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                user.get(id=user_id)

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            user.get(id=user_id)
            self.assertIsNotNone(user)
            self.assertEqual(str(user_id), str(user.id))

            user.get()
            self.assertIsNotNone(user)
            self.assertEqual(str(user_id), str(user.id))

    def test_model_from_api_id(self):
        """
        Tests that an object can be created from an API endpoint.
        """
        with open(self.fixture_path('user.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        user_id = content.get(Model._FIELD_ID)
        path = User._PATH_GET.format(user_id=user_id)

        with requests_mock.Mocker() as mock:
            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                User._model_from_api_id(session, id=user_id)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                User._model_from_api_id(session, id=user_id)

            with pytest.raises(ModelError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                User._model_from_api_id(session, id=user_id)

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            user = User._model_from_api_id(session, id=user_id)
            self.assertIsNotNone(user)
            self.assertEqual(str(user_id), str(user.id))

    def test_models_from_api_ids(self):
        """
        Tests that objects can be created from an API endpoint.
        """
        with open(self.fixture_path('user.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        user_id = content.get(Model._FIELD_ID)
        path = User._PATH_GET.format(user_id=user_id)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            users = User._models_from_api_ids(session, [{Model._FIELD_ID: user_id}])
            self.assertIsNotNone(users)

            for user in users:
                self.assertEqual(str(user_id), str(user.id))

    def test_models_from_api_path(self):
        """
        Tests that objects can be created from an API endpoint returning a list.
        """
        with open(self.fixture_path('user.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        user_id = content.get(Model._FIELD_ID)
        path = '/path'

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [content]}))
            users = User._models_from_api_path(session, path)
            self.assertIsNotNone(users)

            for user in users:
                self.assertEqual(str(user_id), str(user.id))

    def test_organisations(self):
        """
        Tests that an iterator through the user's organisations can be retrieved.
        """
        with open(self.fixture_path('user.json'), 'r') as file:
            user_content = json.loads(file.read())

        session = Session()
        organisation_ids = [organisation.get(Model._FIELD_ID) for organisation in user_content.get('organisations')]

        user_id = user_content.get(Model._FIELD_ID)

        user = User(session)
        self.assertIsNotNone(user)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{User._PATH_GET.format(user_id=user_id)}", text=json.dumps({Model._RESPONSE_KEY_MODEL: user_content}))
            user.get(id=user_id)
            self.assertIsNotNone(user)
            self.assertEqual(str(user_id), str(user.id))

            organisations = user.organisations
            self.assertIsNotNone(organisations)

            for index, organisation_id in enumerate(organisation_ids):
                with open(self.fixture_path(f"organisation{index + 1}.json"), 'r') as file:
                    organisation_content = json.loads(file.read())

                mock.get(f"{Session.API_URL_DEFAULT}{Organisation._PATH_GET.format(organisation_id=organisation_id)}",
                         text=json.dumps({Model._RESPONSE_KEY_MODEL: organisation_content}))
                organisation = next(organisations)
                self.assertIsNotNone(organisation)
                self.assertEqual(str(organisation_id), str(organisation.id))

    def test_schema(self):
        """
        Tests that a user model can be loaded into the schema.
        """
        with open(self.fixture_path('user.json'), 'r') as file:
            content = json.loads(file.read())

        model = UserSchema().load(content)
        self.assertIsNotNone(model)

        for key in content:
            self.assertEqual(json.dumps(content[key], default=json_default), json.dumps(model[key], default=json_default))

    def test_update(self):
        """
        Tests that an object can be updated to the API.
        """
        with open(self.fixture_path('user.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        user_id = content.get(Model._FIELD_ID)
        path = User._PATH_PATCH.format(user_id=user_id)
        given_name = 'Test'

        user = User(session)
        self.assertIsNotNone(user)

        with requests_mock.Mocker() as mock:
            mock.get(f"{Session.API_URL_DEFAULT}{User._PATH_GET.format(user_id=user_id)}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            user.get(id=user_id)
            self.assertIsNotNone(user)
            self.assertEqual(str(user_id), str(user.id))

            with pytest.raises(RequestError):
                mock.patch(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                user.update(given_name=given_name)

            with pytest.raises(RequestError):
                mock.patch(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                user.update(given_name=given_name)

            with pytest.raises(ModelError):
                mock.patch(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                user.update(given_name=given_name)

            self.assertNotEqual(given_name, user.given_name)

            content['given_name'] = given_name
            mock.patch(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            user.update(given_name=given_name)
            self.assertEqual(given_name, user.given_name)
