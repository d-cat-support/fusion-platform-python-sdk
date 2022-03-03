#
# Package init test file.
#
# @author Matthew Casey
#
# (c) Digital Content Analysis Technology Ltd 2022
#

import json
import jwt
import os
import logging
import pytest
import requests
import requests_mock
import uuid

from tests.custom_test_case import CustomTestCase

import fusion_platform
from fusion_platform.models.model import Model
from fusion_platform.models.user import User
from fusion_platform.session import Session, RequestError


class TestInit(CustomTestCase):
    """
    Module tests.
    """

    def test_examples(self):
        """
        Test obtaining example files.
        """
        path = fusion_platform.EXAMPLE_GLASGOW_FILE
        self.assertIsNotNone(path)
        self.assertTrue(os.path.exists(path))

    def test_log_level(self):
        """
        Test setting the log level.
        """
        logger = logging.getLogger(fusion_platform.FUSION_PLATFORM_LOGGER)
        logger.setLevel(logging.INFO)
        self.assertEqual(logging.INFO, logger.level)

        fusion_platform.set_log_level(logging.DEBUG)
        self.assertEqual(logging.DEBUG, logger.level)

        self.assertEqual(logging.DEBUG, fusion_platform.get_log_level())

    def test_login(self):
        """
        Test logging in.
        """
        key = b'-----BEGIN RSA PRIVATE KEY-----\nMIICXAIBAAKBgQCqGKukO1De7zhZj6+H0qtjTkVxwTCpvKe4eCZ0FPqri0cb2JZfXJ/DgYSF6vUp\nwmJG8wVQZKjeGcjDOL5UlsuusFncCzWBQ7RKNUSesmQRMSGkVb1/3j+skZ6UtW+5u09lHNsj6tQ5\n1s1SPrCBkedbNf0Tp0GbMJDyR4e9T04ZZwIDAQABAoGAFijko56+qGyN8M0RVyaRAXz++xTqHBLh\n3tx4VgMtrQ+WEgCjhoTwo23KMBAuJGSYnRmoBZM3lMfTKevIkAidPExvYCdm5dYq3XToLkkLv5L2\npIIVOFMDG+KESnAFV7l2c+cnzRMW0+b6f8mR1CJzZuxVLL6Q02fvLi55/mbSYxECQQDeAw6fiIQX\nGukBI4eMZZt4nscy2o12KyYner3VpoeE+Np2q+Z3pvAMd/aNzQ/W9WaI+NRfcxUJrmfPwIGm63il\nAkEAxCL5HQb2bQr4ByorcMWm/hEP2MZzROV73yF41hPsRC9m66KrheO9HPTJuo3/9s5p+sqGxOlF\nL0NDt4SkosjgGwJAFklyR1uZ/wPJjj611cdBcztlPdqoxssQGnh85BzCj/u3WqBpE2vjvyyvyI5k\nX6zk7S0ljKtt2jny2+00VsBerQJBAJGC1Mg5Oydo5NwD6BiROrPxGo2bpTbu/fhrT8ebHkTz2epl\nU9VQQSQzY1oZMVX8i1m5WUTLPz2yLJIBQVdXqhMCQBGoiuSoSjafUhV7i1cEGpb88h5NBYZzWXGZ\n37sJ5QsW+sJyoNde3xH8vdXhzU7eT82D6X/scw9RZz+/6rCJ4p0=\n-----END RSA PRIVATE KEY-----'
        user_id = str(uuid.uuid4())
        access_token = 'token'
        id_token = jwt.encode({'sub': user_id}, key=key, algorithm='RS256')
        body = {'access_token': access_token, 'id_token': id_token}

        with open(self.fixture_path('user.json'), 'r') as file:
            content = json.loads(file.read())

        with requests_mock.Mocker() as mock:
            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}/users/login", exc=requests.exceptions.ConnectTimeout)
                fusion_platform.login(email='me@test.com', password='password')

            with pytest.raises(RequestError):
                mock.post(f"{Session.API_URL_DEFAULT}/users/login", text='{}')
                fusion_platform.login(email='me@test.com', password='password')

            mock.post(f"{Session.API_URL_DEFAULT}/users/login", text=json.dumps(body))
            mock.get(f"{Session.API_URL_DEFAULT}{User._PATH_GET.format(user_id=user_id)}", text=json.dumps({Model._RESPONSE_KEY_MODEL: content}))

            user = fusion_platform.login(email='me@test.com', password='password')
            self.assertIsNotNone(user)

            user = fusion_platform.login(user_id=str(uuid.uuid4()), password='password')
            self.assertIsNotNone(user)

    def test_version(self):
        """
        Test getting the version.
        """
        self.assertIsNotNone(fusion_platform.__version__)
        self.assertIsNotNone(fusion_platform.__version_date__)
