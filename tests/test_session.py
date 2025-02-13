#
# Session class test file.
#
# @author Matthew Casey
#
# (c) Digital Content Analysis Technology Ltd 2022
#

import json
import jwt
import os
import pytest
import requests
import requests_mock
import tempfile
import uuid

from tests.custom_test_case import CustomTestCase

from fusion_platform.session import RequestError, Session, ValueError


class TestSession(CustomTestCase):
    """
    Session tests.
    """

    def __init__(self, methodName):
        """
        Initialises the test case.

        :param methodName: The test method name.
        """
        super(TestSession, self).__init__(methodName)

        # Initialise the fields.
        self._download_size = None

    def download_callback(self, url, destination, size):
        """
        Test download callback method.

        :param url: The URL to download as a file.
        :param destination: The destination file path.
        :param size: The total size in bytes so far downloaded.
        """
        if self._download_size is None:
            self._download_size = size
        else:
            self._download_size += size

    def test_init(self):
        """
        Test initialisation of the class to ensure no exceptions are raised.
        """
        Session()

    def test_download_file(self):
        """
        Test that a file can be downloaded, checking that missing endpoints are handled correctly.
        """

        with tempfile.TemporaryDirectory() as dir:
            destination = os.path.join(dir, 'file.html')

            session = Session()

            with pytest.raises(RequestError):
                session.download_file('https://www.d-cat.co.uk/.well-known/acme-challenge/test.html', destination)

            self.assertFalse(os.path.exists(destination))
            session.download_file('https://www.d-cat.co.uk/home', destination, self.download_callback)
            self.assertTrue(os.path.exists(destination))
            self.assertIsNotNone(self._download_size)

    def test_login(self):
        """
        Test login using various parameters.
        """
        with pytest.raises(ValueError):
            Session().login()

        with pytest.raises(ValueError):
            Session().login(password='password')

        with pytest.raises(ValueError):
            Session().login(email='me@test.com')

        with requests_mock.Mocker() as mock:
            mock.post(f"{Session.API_URL_DEFAULT}/users/login", text='{}')

            with pytest.raises(RequestError):
                Session().login(email='me@test.com', password='password')

            with pytest.raises(RequestError):
                Session().login(user_id=str(uuid.uuid4()), password='password')

        key = b'-----BEGIN RSA PRIVATE KEY-----\nMIICXAIBAAKBgQCqGKukO1De7zhZj6+H0qtjTkVxwTCpvKe4eCZ0FPqri0cb2JZfXJ/DgYSF6vUp\nwmJG8wVQZKjeGcjDOL5UlsuusFncCzWBQ7RKNUSesmQRMSGkVb1/3j+skZ6UtW+5u09lHNsj6tQ5\n1s1SPrCBkedbNf0Tp0GbMJDyR4e9T04ZZwIDAQABAoGAFijko56+qGyN8M0RVyaRAXz++xTqHBLh\n3tx4VgMtrQ+WEgCjhoTwo23KMBAuJGSYnRmoBZM3lMfTKevIkAidPExvYCdm5dYq3XToLkkLv5L2\npIIVOFMDG+KESnAFV7l2c+cnzRMW0+b6f8mR1CJzZuxVLL6Q02fvLi55/mbSYxECQQDeAw6fiIQX\nGukBI4eMZZt4nscy2o12KyYner3VpoeE+Np2q+Z3pvAMd/aNzQ/W9WaI+NRfcxUJrmfPwIGm63il\nAkEAxCL5HQb2bQr4ByorcMWm/hEP2MZzROV73yF41hPsRC9m66KrheO9HPTJuo3/9s5p+sqGxOlF\nL0NDt4SkosjgGwJAFklyR1uZ/wPJjj611cdBcztlPdqoxssQGnh85BzCj/u3WqBpE2vjvyyvyI5k\nX6zk7S0ljKtt2jny2+00VsBerQJBAJGC1Mg5Oydo5NwD6BiROrPxGo2bpTbu/fhrT8ebHkTz2epl\nU9VQQSQzY1oZMVX8i1m5WUTLPz2yLJIBQVdXqhMCQBGoiuSoSjafUhV7i1cEGpb88h5NBYZzWXGZ\n37sJ5QsW+sJyoNde3xH8vdXhzU7eT82D6X/scw9RZz+/6rCJ4p0=\n-----END RSA PRIVATE KEY-----'
        user_id = str(uuid.uuid4())
        access_token = 'token'
        id_token = jwt.encode({'sub': user_id}, key=key, algorithm='RS256')
        body = {'access_token': access_token, 'id_token': id_token}

        with requests_mock.Mocker() as mock:
            mock.post(f"{Session.API_URL_DEFAULT}/users/login", text=json.dumps(body))

            session = Session()
            self.assertIsNotNone(session)
            self.assertIsNone(session.user_id)
            self.assertIsNone(session._Session__bearer_token)

            session.login(email='me@test.com', password='password')
            self.assertEqual(user_id, session.user_id)
            self.assertEqual(access_token, session._Session__bearer_token)

        with requests_mock.Mocker() as mock:
            mock.post(f"{Session.API_URL_DEFAULT}/users/login", text=json.dumps(body))

            session = Session()
            self.assertIsNotNone(session)
            self.assertIsNone(session.user_id)
            self.assertIsNone(session._Session__bearer_token)

            session.login(user_id=str(uuid.uuid4()), password='password')
            self.assertEqual(user_id, session.user_id)
            self.assertEqual(access_token, session._Session__bearer_token)

    def test_request_delete(self):
        """
        Test a delete request and error handling.
        """
        path = '/path'
        body = {'test': True}
        error = 'My Error'

        session = Session()
        self.assertIsNotNone(session)

        with requests_mock.Mocker() as mock:
            with pytest.raises(RequestError):
                mock.delete(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                session.request(path=path, method=Session.METHOD_DELETE)

            with pytest.raises(RequestError):
                mock.delete(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                session.request(path=path, method=Session.METHOD_DELETE)

            with pytest.raises(RequestError):
                mock.delete(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({'error_message': error}), status_code=400)
                session.request(path=path, method=Session.METHOD_DELETE)

            mock.delete(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps(body))
            response = session.request(path=path, method=Session.METHOD_DELETE)
            self.assertIsNotNone(response)
            self.assertEqual(body, response)

    def test_request_get(self):
        """
        Test a get request and error handling.
        """
        path = '/path'
        query_parameters = {'name': 'Joe', 'value': 1}
        body = {'test': True}
        error = 'My Error'

        session = Session()
        self.assertIsNotNone(session)

        with requests_mock.Mocker() as mock:
            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                session.request(path=path, query_parameters=query_parameters, method=Session.METHOD_GET)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                session.request(path=path, query_parameters=query_parameters, method=Session.METHOD_GET)

            with pytest.raises(RequestError):
                mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({'error_message': error}), status_code=400)
                session.request(path=path, query_parameters=query_parameters, method=Session.METHOD_GET)

            mock.get(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps(body))
            response = session.request(path=path, query_parameters=query_parameters, method=Session.METHOD_GET)
            self.assertIsNotNone(response)
            self.assertEqual(body, response)

    def test_request_patch(self):
        """
        Test a patch request and error handling.
        """
        path = '/path'
        body = {'test': True}
        error = 'My Error'

        session = Session()
        self.assertIsNotNone(session)

        with requests_mock.Mocker() as mock:
            with pytest.raises(RequestError):
                mock.patch(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                session.request(path=path, method=Session.METHOD_PATCH)

            with pytest.raises(RequestError):
                mock.patch(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                session.request(path=path, method=Session.METHOD_PATCH)

            with pytest.raises(RequestError):
                mock.patch(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({'error_message': error}), status_code=400)
                session.request(path=path, method=Session.METHOD_PATCH)

            def callback(request, _):
                return request.text

            mock.patch(f"{Session.API_URL_DEFAULT}{path}", text=callback)
            response = session.request(path=path, method=Session.METHOD_PATCH, body=body)
            self.assertIsNotNone(response)
            self.assertEqual(body, response)

    def test_request_post(self):
        """
        Test a post request and error handling.
        """
        path = '/path'
        body = {'test': True}
        error = 'My Error'

        session = Session()
        self.assertIsNotNone(session)

        with requests_mock.Mocker() as mock:
            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                session.request(path=path, method=Session.METHOD_POST)

            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                session.request(path=path, method=Session.METHOD_POST)

            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({'error_message': error}), status_code=400)
                session.request(path=path, method=Session.METHOD_POST)

            def callback(request, _):
                return request.text

            mock.post(f"{Session.API_URL_DEFAULT}{path}", text=callback)
            response = session.request(path=path, method=Session.METHOD_POST, body=body)
            self.assertIsNotNone(response)
            self.assertEqual(body, response)

    def test_request_put(self):
        """
        Test a put request and error handling.
        """
        path = '/path'
        body = {'test': True}
        error = 'My Error'

        session = Session()
        self.assertIsNotNone(session)

        with requests_mock.Mocker() as mock:
            with pytest.raises(RequestError):
                mock.put(f"{Session.API_URL_DEFAULT}{path}", exc=requests.exceptions.ConnectTimeout)
                session.request(path=path, method=Session.METHOD_PUT)

            with pytest.raises(RequestError):
                mock.put(f"{Session.API_URL_DEFAULT}{path}", status_code=400)
                session.request(path=path, method=Session.METHOD_PUT)

            with pytest.raises(RequestError):
                mock.put(f"{Session.API_URL_DEFAULT}{path}", text=json.dumps({'error_message': error}), status_code=400)
                session.request(path=path, method=Session.METHOD_PUT)

            def callback(request, _):
                return request.text

            mock.put(f"{Session.API_URL_DEFAULT}{path}", text=callback)
            response = session.request(path=path, method=Session.METHOD_PUT, body=body)
            self.assertIsNotNone(response)
            self.assertEqual(body, response)

    def test_upload_file(self):
        """
        Test that a file can be uploaded, checking that missing endpoints are handled correctly.
        """
        source = self.fixture_path('user.json')
        url = 'https://upload.com/test'

        session = Session()
        self.assertIsNotNone(session)

        with requests_mock.Mocker() as mock:
            with pytest.raises(RequestError):
                mock.put(url, exc=requests.exceptions.ConnectTimeout)
                session.upload_file(url, source)

            with pytest.raises(RequestError):
                mock.put(url, status_code=400)
                session.upload_file(url, source)

            adapter = mock.put(url, status_code=200)
            session.upload_file(url, source)
            self.assertIsNotNone(adapter.last_request.text)

            def callback(url, source, upload_size):
                pass

            session.upload_file(url, source, callback=callback)  # Because the request is mocked, the callback will not be called because there are no reads.
            self.assertIsNotNone(adapter.last_request.text)
