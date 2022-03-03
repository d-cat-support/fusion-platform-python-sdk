#
# Data file model class test file.
#
# @author Matthew Casey
#
# (c) Digital Content Analysis Technology Ltd 2022
#

import json
import os
from time import sleep
import tempfile
import uuid

import pytest
import requests
import requests_mock

from tests.custom_test_case import CustomTestCase

from fusion_platform.common.utilities import json_default
from fusion_platform.models.data_file import DataFile, DataFileSchema
from fusion_platform.models.model import Model, ModelError
from fusion_platform.session import Session, RequestError


class TestDataFile(CustomTestCase):
    """
    Data file model tests.
    """

    def test_init(self):
        """
        Test initialisation of the data model class to ensure no exceptions are raised.
        """
        data_file = DataFile(Session())
        self.assertIsNotNone(data_file)

    def test_download_no_wait(self):
        """
        Tests that a download can be done without waiting for completion.
        """
        with open(self.fixture_path('data_file.json'), 'r') as file:
            data_file_content = json.loads(file.read())

        with open(self.fixture_path('download_file.json'), 'r') as file:
            download_file_content = json.loads(file.read())

        session = Session()
        organisation_id = uuid.uuid4()
        data_id = data_file_content.get('data_id')
        file_id = data_file_content.get('file_id')
        path = DataFile._PATH_DOWNLOAD_FILE.format(organisation_id=organisation_id, data_id=data_id, file_id=file_id)
        url = 'https://download-file.com/test'
        content = 'content'

        data_file = DataFile(session)
        self.assertIsNotNone(data_file)

        data_file._Model__set_model_from_response(data_file_content, DataFileSchema(), organisation_id=organisation_id)
        self.assertEqual(str(organisation_id), str(data_file.organisation_id))
        self.assertEqual(str(data_id), str(data_file.data_id))
        self.assertEqual(str(file_id), str(data_file.file_id))

        with tempfile.TemporaryDirectory() as dir:
            destination = os.path.join(dir, 'file.json')

            with requests_mock.Mocker() as mock:
                with pytest.raises(RequestError):
                    mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                    data_file.download(destination)

                with pytest.raises(RequestError):
                    mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                    data_file.download(destination)

                with pytest.raises(ModelError):
                    mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                    data_file.download(destination)

                with pytest.raises(RequestError):
                    mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_EXTRAS: download_file_content}))
                    mock.get(url, exc=requests.exceptions.ConnectTimeout)
                    data_file.download(destination)

                    while not data_file.download_complete():
                        progress_url, progress_destination, progress_size = data_file.download_progress()
                        self.assertEqual(url, progress_url)
                        self.assertEqual(destination, progress_destination)
                        self.assertIsNotNone(progress_size)

                        sleep(0.1)

                self.assertFalse(os.path.exists(destination))
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_EXTRAS: download_file_content}))
                mock.get(url, text=content)
                data_file.download(destination)
                self.assertFalse(os.path.exists(destination))

                while not data_file.download_complete():
                    sleep(0.1)

                self.assertTrue(os.path.exists(destination))

                with open(destination, 'r') as file:
                    self.assertEqual(content, file.read())

    def test_download_wait(self):
        """
        Tests that a download can be done while waiting for completion.
        """
        with open(self.fixture_path('data_file.json'), 'r') as file:
            data_file_content = json.loads(file.read())

        with open(self.fixture_path('download_file.json'), 'r') as file:
            download_file_content = json.loads(file.read())

        session = Session()
        organisation_id = uuid.uuid4()
        data_id = data_file_content.get('data_id')
        file_id = data_file_content.get('file_id')
        path = DataFile._PATH_DOWNLOAD_FILE.format(organisation_id=organisation_id, data_id=data_id, file_id=file_id)
        content = 'content'

        data_file = DataFile(session)
        self.assertIsNotNone(data_file)

        data_file._Model__set_model_from_response(data_file_content, DataFileSchema(), organisation_id=organisation_id)
        self.assertEqual(str(organisation_id), str(data_file.organisation_id))
        self.assertEqual(str(data_id), str(data_file.data_id))
        self.assertEqual(str(file_id), str(data_file.file_id))

        with tempfile.TemporaryDirectory() as dir:
            destination = os.path.join(dir, 'file.json')

            with requests_mock.Mocker() as mock:
                with pytest.raises(RequestError):
                    mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                    data_file.download(destination, wait=True)

                with pytest.raises(RequestError):
                    mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                    data_file.download(destination, wait=True)

                with pytest.raises(ModelError):
                    mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                    data_file.download(destination, wait=True)

                with pytest.raises(RequestError):
                    mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_EXTRAS: download_file_content}))
                    mock.get('https://download-file.com/test', exc=requests.exceptions.ConnectTimeout)
                    data_file.download(destination, wait=True)

                self.assertFalse(os.path.exists(destination))
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_EXTRAS: download_file_content}))
                mock.get('https://download-file.com/test', text=content)
                data_file.download(destination, wait=True)
                self.assertTrue(os.path.exists(destination))

                with open(destination, 'r') as file:
                    self.assertEqual(content, file.read())

    def test_download_url(self):
        """
        Tests that a download URL can be obtained for the file.
        """
        with open(self.fixture_path('data_file.json'), 'r') as file:
            data_file_content = json.loads(file.read())

        with open(self.fixture_path('download_file.json'), 'r') as file:
            download_file_content = json.loads(file.read())

        session = Session()
        organisation_id = uuid.uuid4()
        data_id = data_file_content.get('data_id')
        file_id = data_file_content.get('file_id')
        path = DataFile._PATH_DOWNLOAD_FILE.format(organisation_id=organisation_id, data_id=data_id, file_id=file_id)

        data_file = DataFile(session)
        self.assertIsNotNone(data_file)

        data_file._Model__set_model_from_response(data_file_content, DataFileSchema(), organisation_id=organisation_id)
        self.assertEqual(str(organisation_id), str(data_file.organisation_id))
        self.assertEqual(str(data_id), str(data_file.data_id))
        self.assertEqual(str(file_id), str(data_file.file_id))

        with requests_mock.Mocker() as mock:
            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                data_file.download_url()

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                data_file.download_url()

            with pytest.raises(ModelError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text='{}')
                data_file.download_url()

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({Model._RESPONSE_KEY_EXTRAS: download_file_content}))
            url = data_file.download_url()
            self.assertIsNotNone(url)

    def test_schema(self):
        """
        Tests that a data model can be loaded into the schema.
        """
        with open(self.fixture_path('data_file.json'), 'r') as file:
            content = json.loads(file.read())

        model = DataFileSchema().load(content)
        self.assertIsNotNone(model)

        for key in content:
            self.assertEqual(json.dumps(content[key], default=json_default), json.dumps(model[key], default=json_default))
