#
# Credit model class test file.
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
from fusion_platform.models.credit import Credit, CreditSchema
from fusion_platform.session import Session, RequestError


class TestCredit(CustomTestCase):
    """
    Credit model tests.
    """

    def test_init(self):
        """
        Test initialisation of the credit model class to ensure no exceptions are raised.
        """
        credit = Credit(Session())
        self.assertIsNotNone(credit)

    def test_get(self):
        """
        Tests that an object can be retrieved from the API.
        """
        with open(self.fixture_path('credit.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get('organisation_id')
        credit_id = content.get(Model.FIELD_ID)
        path = Credit._PATH_GET.format(organisation_id=organisation_id, credit_id=credit_id)

        credit = Credit(session)
        self.assertIsNotNone(credit)

        with requests_mock.Mocker() as mock:
            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                credit.get(organisation_id=organisation_id, credit_id=credit_id)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                credit.get(organisation_id=organisation_id, credit_id=credit_id)

            with pytest.raises(ModelError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                credit.get(organisation_id=organisation_id, credit_id=credit_id)

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            credit.get(organisation_id=organisation_id, credit_id=credit_id)
            self.assertIsNotNone(credit)
            self.assertEqual(str(credit_id), str(credit.id))

            credit.get()
            self.assertIsNotNone(credit)
            self.assertEqual(str(credit_id), str(credit.id))

    def test_model_from_api_id(self):
        """
        Tests that an object can be created from an API endpoint.
        """
        with open(self.fixture_path('credit.json'), 'r') as file:
            content = json.loads(file.read())

        session = Session()
        organisation_id = content.get('organisation_id')
        credit_id = content.get(Model.FIELD_ID)
        path = Credit._PATH_GET.format(organisation_id=organisation_id, credit_id=credit_id)

        with requests_mock.Mocker() as mock:
            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                Credit._model_from_api_id(session, id=credit_id, organisation_id=organisation_id)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                Credit._model_from_api_id(session, id=credit_id, organisation_id=organisation_id)

            with pytest.raises(ModelError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                Credit._model_from_api_id(session, id=credit_id, organisation_id=organisation_id)

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))
            credit = Credit._model_from_api_id(session, id=credit_id, organisation_id=organisation_id)
            self.assertIsNotNone(credit)
            self.assertEqual(str(credit_id), str(credit.id))

    def test_schema(self):
        """
        Tests that a credit model can be loaded into the schema.
        """
        with open(self.fixture_path('credit.json'), 'r') as file:
            content = json.loads(file.read())

        model = CreditSchema().load(content)
        self.assertIsNotNone(model)

        for key in content:
            self.assertEqual(json.dumps(content[key], default=json_default), json.dumps(model[key], default=json_default))
