#
# Model base class test file.
#
# @author Matthew Casey
#
# (c) Digital Content Analysis Technology Ltd 2022
#

from datetime import datetime, timezone
from functools import partial
import json
from mock import patch
import pytest
import requests
import requests_mock
import uuid

from tests.custom_test_case import CustomTestCase

from fusion_platform.common.utilities import json_default, value_to_read_only, value_to_string
from fusion_platform.session import Session, RequestError
from fusion_platform.models.process import ProcessSchema
from fusion_platform.models.model import Model, ModelError
from fusion_platform.models.user import User, UserSchema


class TestModel(CustomTestCase):
    """
    Model tests.
    """

    def test_init(self):
        """
        Test initialisation of the model base class to ensure no exceptions are raised.
        """
        session = Session()

        model = Model(session)
        self.assertIsNotNone(model)
        self.assertEqual(session, model._session)

    def test_attributes(self):
        """
        Test that properties can be retrieved as a dictionary of attributes.
        """
        model = Model(Session(), schema=UserSchema())
        self.assertIsNotNone(model)

        with open(self.fixture_path('user.json'), 'r') as file:
            content = json.loads(file.read())

        model._set_model(content)

        with patch.object(Model, '_Model__get_schema', return_value=UserSchema()):
            attributes = model.attributes

            for key in attributes:
                self.assertEqual(getattr(model, key), attributes[key])

    def test_build_filter(self):
        """
        Test build a filter.
        """
        id = uuid.uuid4()

        self.assertEqual({'id__eq': id}, Model._build_filter([(Model._FIELD_ID, Model._FILTER_MODIFIER_EQ, id)]))
        self.assertEqual({}, Model._build_filter([(Model._FIELD_ID, Model._FILTER_MODIFIER_EQ, None)]))

    def test_create_abstract(self):
        """
        Tests the create method does not work with abstract path methods.
        """
        with pytest.raises(NotImplementedError):
            model = Model(Session())
            model._create()

    def test_create_mocked(self):
        """
        Tests that an object can be created via a post to the API endpoint with response validation using a Marshmallow schema.
        """
        with open(self.fixture_path('user.json'), 'r') as file:
            content = json.loads(file.read())

        wrong_content = {}

        for key in content:
            wrong_content[f"new_{key}"] = content[key]

        session = Session()
        path = '/path'
        given_name = 'Test'

        model = Model(session, schema=UserSchema())
        self.assertIsNotNone(model)

        model._set_model(content)

        with requests_mock.Mocker() as mock:
            with patch.object(Model, Model._get_path.__name__, return_value=path):
                with patch.object(Model, '_Model__get_schema', return_value=UserSchema()):

                    with pytest.raises(RequestError):
                        mock.post(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                        model._create(given_name=given_name)

                    with pytest.raises(RequestError):
                        mock.post(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                        model._create(given_name=given_name)

                    with pytest.raises(ModelError):
                        mock.post(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                        model._create(given_name=given_name)

                    with pytest.raises(ModelError):
                        mock.post(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: wrong_content}))
                        model._create(given_name=given_name)

                    content['given_name'] = given_name
                    adapter = mock.post(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
                    model._create(given_name=given_name, last_request_at=datetime.now(timezone.utc))

                    self.assertEqual(json.dumps(model._Model__build_body(given_name=given_name), default=json_default), adapter.last_request.text)

                    schema = UserSchema()

                    for key in content:
                        if Model._METADATA_HIDE not in schema.fields[key].metadata:
                            self.assertEqual(json.dumps(content[key], default=json_default), json.dumps(getattr(model, key), default=json_default))
                        else:
                            self.assertFalse(hasattr(model, key))

    def test_delete_abstract(self):
        """
        Tests the delete method does not work with abstract path methods.
        """
        with pytest.raises(NotImplementedError):
            model = Model(Session())
            model._Model__persisted = True
            model.delete()

    def test_delete_mocked(self):
        """
        Tests that an object can be deleted via a DELETE to the API endpoint.
        """
        with open(self.fixture_path('user.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        path = '/path'

        model = Model(session)
        self.assertIsNotNone(model)
        model._Model__persisted = True

        with requests_mock.Mocker() as mock:
            with patch.object(Model, Model._get_path.__name__, return_value=path):
                with pytest.raises(RequestError):
                    mock.delete(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                    model.delete()

                with pytest.raises(RequestError):
                    mock.delete(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                    model.delete()

                mock.delete(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
                model.delete()

    def test_eq(self):
        """
        Tests model equals.
        """
        with open(self.fixture_path('user.json'), 'r') as file:
            content = json.loads(file.read())

        model1 = User(Session())
        model1._set_model(content)

        model2 = User(Session())
        model2._set_model(content)

        content['email'] = 'sid.james@test.com'

        model3 = User(Session())
        model3._set_model(content)

        self.assertTrue(model1 == model1)
        self.assertTrue(model2 == model2)
        self.assertTrue(model3 == model3)
        self.assertTrue(model1 == model2)
        self.assertTrue(model2 == model1)
        self.assertFalse(model1 == model3)
        self.assertFalse(model2 == model3)

    def test_first_and_generator(self):
        """
        Tests the first and generator method.
        """

        def dummy_generator(nothing=False, items_per_request=10):
            count = items_per_request if not nothing else 0
            i = 0

            while i < count:
                yield i
                i += 1

        partial_generator = partial(dummy_generator, nothing=True)

        first, generator = Model._first_and_generator(partial_generator)
        self.assertIsNone(first)
        self.assertIsNotNone(generator)

        with pytest.raises(StopIteration):
            next(generator)

        partial_generator = partial(dummy_generator, nothing=False)

        first, generator = Model._first_and_generator(partial_generator)
        self.assertIsNotNone(first)
        self.assertIsNotNone(generator)

        self.assertEqual(0, first)

        for index, item in enumerate(generator):
            self.assertEqual(index, item)

    def test_get_id_name(self):
        """
        Tests that the correct id name is returned.
        """
        self.assertEqual('user_id', Model._get_id_name(User.__name__))

    def test_get_ids_from_list(self):
        """
        Tests that the correct id list is returned.
        """
        user_id = uuid.uuid4()
        organisation_id = uuid.uuid4()
        self.assertEqual([{'user_id': user_id, 'organisation_id': organisation_id}], User._get_ids_from_list([user_id], organisation_id=organisation_id))

    def test_get_abstract(self):
        """
        Tests the get method does not work with abstract path methods.
        """
        with pytest.raises(NotImplementedError):
            model = Model(Session())
            model.get()

    def test_get_mocked(self):
        """
        Tests that an object can be created from an API endpoint with validation using a Marshmallow schema.
        """
        with open(self.fixture_path('user.json'), 'r') as file:
            content = json.loads(file.read())

        wrong_content = {}

        for key in content:
            wrong_content[f"new_{key}"] = content[key]

        session = Session()
        path = '/path'

        model = Model(session)
        self.assertIsNotNone(model)

        with requests_mock.Mocker() as mock:
            with patch.object(Model, Model._get_path.__name__, return_value=path):
                with patch.object(Model, '_Model__get_schema', return_value=UserSchema()):

                    with pytest.raises(RequestError):
                        mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                        model.get()

                    with pytest.raises(RequestError):
                        mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                        model.get()

                    with pytest.raises(ModelError):
                        mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                        model.get()

                    with pytest.raises(ModelError):
                        mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: wrong_content}))
                        model.get()

                    mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
                    model.get()

                    schema = UserSchema()

                    for key in content:
                        if Model._METADATA_HIDE not in schema.fields[key].metadata:
                            self.assertEqual(json.dumps(content[key], default=json_default), json.dumps(getattr(model, key), default=json_default))
                        else:
                            self.assertFalse(hasattr(model, key))

    def test_get_path(self):
        """
        Tests the get path method.
        """
        with pytest.raises(NotImplementedError):
            Model(Session())._get_path(Model._PATH_DELETE)

        with pytest.raises(NotImplementedError):
            Model(Session())._get_path(Model._PATH_GET)

        with pytest.raises(NotImplementedError):
            Model(Session())._get_path(Model._PATH_PATCH)

        self.assertEqual('/model/999', Model(Session())._get_path('/model/{model_id}', id=999))

    def test_get_schema(self):
        """
        Tests the get schema method.
        """
        with pytest.raises(NotImplementedError):
            Model(Session())._Model__get_schema()

        with patch.object(Model, '_Model__get_schema', return_value=UserSchema()):
            Model(Session())._Model__get_schema()

    def test_model_from_api_id(self):
        """
        Tests the loading of a model with an id from the API method does not work with abstract methods.
        """
        with pytest.raises(NotImplementedError):
            Model._model_from_api_id(Session(), id=uuid.uuid4())

    def test_models_from_api_ids(self):
        """
        Tests generating an iterator through models with ids from the API method does not work with abstract methods.
        """
        with pytest.raises(NotImplementedError):
            iterator = Model._models_from_api_ids(Session(), [{Model._FIELD_ID: uuid.uuid4()}])
            next(iterator)

    def test_models_from_api_path(self):
        """
        Tests generating an iterator through models with a path from the API method does not work with abstract methods.
        """
        with open(self.fixture_path('user.json'), 'r') as file:
            content = json.loads(file.read())

        path = '/path'

        with pytest.raises(ModelError):
            with requests_mock.Mocker() as mock:
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [content]}))
                iterator = Model._models_from_api_path(Session(), path, items_per_request=10, reverse=True, filter={'test_begins_with': 'Test'}, search='search')
                next(iterator)

    def test_new_abstract(self):
        """
        Tests the new method does not work with abstract path methods.
        """
        with pytest.raises(NotImplementedError):
            model = Model(Session())
            model._new()

    def test_new_mocked(self):
        """
        Tests that a template new object can be created from an API endpoint with validation using a Marshmallow schema.
        """
        with open(self.fixture_path('process.json'), 'r') as file:
            content = json.loads(file.read())

        with open(self.fixture_path('extras.json'), 'r') as file:
            extras = json.loads(file.read())

        wrong_content = {}

        for key in content:
            wrong_content[f"new_{key}"] = content[key]

        session = Session()
        organisation_id = content.get('organisation_id')
        path = '/path'

        model = Model(session)
        self.assertIsNotNone(model)

        schema = ProcessSchema()
        del schema.fields[Model._FIELD_AVAILABLE_DISPATCHERS].metadata[Model._METADATA_HIDE]  # Remove 'hide' so that the extras are loaded as an attribute.

        with requests_mock.Mocker() as mock:
            with patch.object(Model, Model._get_path.__name__, return_value=path):
                with patch.object(Model, '_Model__get_schema', return_value=schema):

                    with pytest.raises(RequestError):
                        mock.get(f"{Session.API_URL_DEFAULT}{path}?test=value", exc=requests.exceptions.ConnectTimeout)
                        model._new(query_parameters={'test': 'value'}, extras=[(Model._FIELD_DISPATCHERS, Model._FIELD_AVAILABLE_DISPATCHERS)],
                                   organisation_id=organisation_id)

                    with pytest.raises(RequestError):
                        mock.get(f"{Session.API_URL_DEFAULT}{path}?test=value", status_code=400)
                        model._new(query_parameters={'test': 'value'}, extras=[(Model._FIELD_DISPATCHERS, Model._FIELD_AVAILABLE_DISPATCHERS)],
                                   organisation_id=organisation_id)

                    with pytest.raises(ModelError):
                        mock.get(f"{Session.API_URL_DEFAULT}{path}?test=value", text='{}')
                        model._new(query_parameters={'test': 'value'}, extras=[(Model._FIELD_DISPATCHERS, Model._FIELD_AVAILABLE_DISPATCHERS)],
                                   organisation_id=organisation_id)

                    mock.get(f"{Session.API_URL_DEFAULT}{path}?test=value", text=json.dumps({Model._RESPONSE_KEY_MODEL: wrong_content}))
                    model._new(query_parameters={'test': 'value'}, organisation_id=organisation_id)

                    with pytest.raises(ModelError):
                        mock.get(f"{Session.API_URL_DEFAULT}{path}?test=value", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
                        model._new(query_parameters={'test': 'value'}, extras=[(Model._FIELD_DISPATCHERS, Model._FIELD_AVAILABLE_DISPATCHERS)],
                                   organisation_id=organisation_id)

                    mock.get(f"{Session.API_URL_DEFAULT}{path}?test=value", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
                    model._new(query_parameters={'test': 'value'}, organisation_id=organisation_id)

                    mock.get(f"{Session.API_URL_DEFAULT}{path}?test=value",
                             text=json.dumps({Model._RESPONSE_KEY_MODEL: content, Model._RESPONSE_KEY_EXTRAS: {Model._FIELD_DISPATCHERS: extras}}))
                    model._new(query_parameters={'test': 'value'}, extras=[(Model._FIELD_DISPATCHERS, Model._FIELD_AVAILABLE_DISPATCHERS)],
                               organisation_id=organisation_id)

                    for key in content:
                        if (Model._METADATA_HIDE not in schema.fields[key].metadata) and (content[key] is not None):
                            self.assertEqual(json.dumps(content[key], default=json_default), json.dumps(getattr(model, key), default=json_default))
                        else:
                            self.assertFalse(hasattr(model, key))

                    self.assertEqual(json.loads(json.dumps(extras, default=json_default)),
                                     json.loads(json.dumps(model.available_dispatchers, default=json_default)))

        schema.fields[Model._FIELD_AVAILABLE_DISPATCHERS].metadata[Model._METADATA_HIDE] = True  # Put back 'hide' so that the remaining tests work.

    def test_set_field(self):
        """
        Test that a field cna be set.
        """
        schema = UserSchema()
        model = Model(Session(), schema=schema)
        self.assertIsNotNone(model)

        with open(self.fixture_path('user.json'), 'r') as file:
            content = json.loads(file.read())

        model._set_model(content)
        self.assertEqual(content['email'], model.email)

        previous = model._model

        with pytest.raises(ModelError):
            model._set_field(['rubbish1', 'rubbish2', 'rubbish3'], 'rubbish')

        self.assertEqual(previous, model._model)

        new_email = f"new_{content['email']}"
        model._set_field(['email'], new_email)
        self.assertEqual(new_email, model.email)

        model._set_field(['notification_contact', 0], 'text')
        self.assertEqual(('text',), model.notification_contact)

    def test_set_model(self):
        """
        Test that properties are set correctly from the dictionary.
        """
        schema = UserSchema()
        model = Model(Session(), schema=schema)
        self.assertIsNotNone(model)

        with open(self.fixture_path('user.json'), 'r') as file:
            content = json.loads(file.read())

        model._set_model(content)

        for key in content:
            if Model._METADATA_HIDE not in schema.fields[key].metadata:
                self.assertEqual(value_to_read_only(content[key]), getattr(model, key))

                with pytest.raises(ModelError):
                    setattr(model, key, False)
            else:
                self.assertFalse(hasattr(model, key))

    def test_to_csv(self):
        """
        Test that properties can be retrieved as a CSV string.
        """
        model = Model(Session(), schema=UserSchema())
        self.assertIsNotNone(model)

        with open(self.fixture_path('user.json'), 'r') as file:
            content = json.loads(file.read())

        model._set_model(content)

        with patch.object(Model, '_Model__get_schema', return_value=UserSchema()):
            attributes = model.attributes

            header, line = model.to_csv()
            self.assertIsNotNone(header)
            self.assertIsNotNone(line)

            self.assertEqual(list(attributes.keys()), header.split(','))
            self.assertEqual([value_to_string(value) for value in attributes.values()], line.split(','))

            header, line = model.to_csv(exclude='email')
            self.assertIsNotNone(header)
            self.assertIsNotNone(line)

            self.assertTrue('email' not in header.split(','))
            self.assertTrue('joe.bloggs@d-cat.co.uk' not in line.split(','))

    def test_update_abstract(self):
        """
        Tests the update method does not work with abstract path methods.
        """
        with pytest.raises(NotImplementedError):
            model = Model(Session())
            model.update()

    def test_update_not_persisted_mocked(self):
        """
        Tests that an object can be updated when it is not persisted.
        """
        with open(self.fixture_path('user.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        path = '/path'
        given_name = 'Test'

        model = Model(session, schema=UserSchema())
        self.assertIsNotNone(model)

        model._set_model(content)
        model._Model__persisted = False

        now = datetime.now(timezone.utc)
        model.update(given_name=given_name, last_request_at=now)
        self.assertEqual(given_name, model.given_name)
        self.assertNotEqual(now, model.last_request_at)

    def test_update_persisted_mocked(self):
        """
        Tests that an object can be updated via a patch to the API endpoint with response validation using a Marshmallow schema.
        """
        with open(self.fixture_path('user.json'), 'r') as file:
            content = json.loads(file.read())

        wrong_content = {}

        for key in content:
            wrong_content[f"new_{key}"] = content[key]

        session = Session()
        path = '/path'
        given_name = 'Test'

        model = Model(session)
        self.assertIsNotNone(model)
        model._Model__persisted = True

        with requests_mock.Mocker() as mock:
            with patch.object(Model, Model._get_path.__name__, return_value=path):
                with patch.object(Model, '_Model__get_schema', return_value=UserSchema()):

                    with pytest.raises(RequestError):
                        mock.patch(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                        model.update(given_name=given_name)

                    with pytest.raises(RequestError):
                        mock.patch(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                        model.update(given_name=given_name)

                    with pytest.raises(ModelError):
                        mock.patch(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                        model.update(given_name=given_name)

                    with pytest.raises(ModelError):
                        mock.patch(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: wrong_content}))
                        model.update(given_name=given_name)

                    with pytest.raises(ModelError):
                        mock.patch(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
                        model.update()

                    content['given_name'] = given_name
                    adapter = mock.patch(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
                    model.update(given_name=given_name, last_request_at=datetime.now(timezone.utc))

                    self.assertEqual({'Model[given_name]': given_name}, json.loads(adapter.last_request.text))

                    schema = UserSchema()

                    for key in content:
                        if Model._METADATA_HIDE not in schema.fields[key].metadata:
                            self.assertEqual(json.dumps(content[key], default=json_default), json.dumps(getattr(model, key), default=json_default))
                        else:
                            self.assertFalse(hasattr(model, key))
