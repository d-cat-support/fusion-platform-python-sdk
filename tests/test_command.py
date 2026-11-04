#
# Command test file.
#
# @author Matthew Casey
#
# (c) Digital Content Analysis Technology Ltd 2026
#

from datetime import datetime, timedelta, timezone
import i18n
import json
import jwt
import keyring
from keyring.errors import PasswordDeleteError
import logging
from mock import patch, mock_open
import os
from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput
import pytest
import re
import requests_mock
import sys
import tempfile
import uuid

import fusion_platform
from tests.custom_test_case import CustomTestCase

from fusion_platform.command import Command, CommandError
from fusion_platform.models.data import Data, DataSchema
from fusion_platform.models.data_file import DataFile, DataFileSchema
from fusion_platform.models.model import Model, ModelError
from fusion_platform.models.organisation import Organisation
from fusion_platform.models.process import Process, ProcessSchema
from fusion_platform.models.process_execution import ProcessExecution, ProcessExecutionSchema
from fusion_platform.models.service import Service, ServiceSchema
from fusion_platform.models.user import User
from fusion_platform.session import RequestError


class TestCommand(CustomTestCase):
    """
    Command tests.
    """

    def __login(self, command):
        """
        Used to mock login and to return a valid organisation model.

        Args:
            command: The command object for which login is required.

        Returns:
            The base URL and the logged in organisation.
        """
        key = b'-----BEGIN RSA PRIVATE KEY-----\nMIICXAIBAAKBgQCqGKukO1De7zhZj6+H0qtjTkVxwTCpvKe4eCZ0FPqri0cb2JZfXJ/DgYSF6vUp\nwmJG8wVQZKjeGcjDOL5UlsuusFncCzWBQ7RKNUSesmQRMSGkVb1/3j+skZ6UtW+5u09lHNsj6tQ5\n1s1SPrCBkedbNf0Tp0GbMJDyR4e9T04ZZwIDAQABAoGAFijko56+qGyN8M0RVyaRAXz++xTqHBLh\n3tx4VgMtrQ+WEgCjhoTwo23KMBAuJGSYnRmoBZM3lMfTKevIkAidPExvYCdm5dYq3XToLkkLv5L2\npIIVOFMDG+KESnAFV7l2c+cnzRMW0+b6f8mR1CJzZuxVLL6Q02fvLi55/mbSYxECQQDeAw6fiIQX\nGukBI4eMZZt4nscy2o12KyYner3VpoeE+Np2q+Z3pvAMd/aNzQ/W9WaI+NRfcxUJrmfPwIGm63il\nAkEAxCL5HQb2bQr4ByorcMWm/hEP2MZzROV73yF41hPsRC9m66KrheO9HPTJuo3/9s5p+sqGxOlF\nL0NDt4SkosjgGwJAFklyR1uZ/wPJjj611cdBcztlPdqoxssQGnh85BzCj/u3WqBpE2vjvyyvyI5k\nX6zk7S0ljKtt2jny2+00VsBerQJBAJGC1Mg5Oydo5NwD6BiROrPxGo2bpTbu/fhrT8ebHkTz2epl\nU9VQQSQzY1oZMVX8i1m5WUTLPz2yLJIBQVdXqhMCQBGoiuSoSjafUhV7i1cEGpb88h5NBYZzWXGZ\n37sJ5QsW+sJyoNde3xH8vdXhzU7eT82D6X/scw9RZz+/6rCJ4p0=\n-----END RSA PRIVATE KEY-----'
        user_id = str(uuid.uuid4())
        access_token = 'token'
        id_token = jwt.encode({'sub': user_id}, key=key, algorithm='RS256')
        body = {'access_token': access_token, 'id_token': id_token}

        with open(self.fixture_path('user.json'), 'r') as file:
            user_content = json.loads(file.read())

        with open(self.fixture_path('organisation1.json'), 'r') as file:
            organisation1_content = json.loads(file.read())

        organisation1_id = organisation1_content.get('id')
        organisation1_name = organisation1_content.get(Model._FIELD_NAME)

        with open(self.fixture_path('organisation2.json'), 'r') as file:
            organisation2_content = json.loads(file.read())

        organisation2_id = organisation2_content.get(Model._FIELD_ID)

        deployment = Command._DEPLOYMENT_STAGE
        email = 'test@test.com'
        password = 'password'

        url = Command.DEPLOYMENTS[deployment][Command._DEPLOYMENT_KEY_URL]

        with patch('keyring.get_password', return_value=None) as mock_get_password:
            with patch('keyring.set_password') as mock_set_password:
                with requests_mock.Mocker() as mock:
                    mock.post(f"{url}/users/login", text=json.dumps(body))
                    mock.get(f"{url}{User._PATH_GET.format(user_id=user_id)}", text=json.dumps({Model._RESPONSE_KEY_MODEL: user_content}))
                    mock.get(f"{url}{Organisation._PATH_GET.format(organisation_id=organisation1_id)}",
                             text=json.dumps({Model._RESPONSE_KEY_MODEL: organisation1_content}))
                    mock.get(f"{url}{Organisation._PATH_GET.format(organisation_id=organisation2_id)}",
                             text=json.dumps({Model._RESPONSE_KEY_MODEL: organisation2_content}))

                    with create_pipe_input() as input:
                        input.send_text(f"{password}\n")
                        input.send_text('\n')

                        with create_app_session(input=input, output=DummyOutput()):
                            organisation, stage, region = command.login(deployment, email, None, False)
                            self.assertIsNotNone(organisation)
                            self.assertIsNotNone(stage)
                            self.assertIsNotNone(region)

                            self.assertEqual(organisation1_name, organisation.name)
                            self.assertEqual(deployment, stage)
                            self.assertEqual(Command.DEPLOYMENTS[deployment][Command._DEPLOYMENT_KEY_REGION], region)

                    mock_get_password.assert_called_once()
                    mock_set_password.assert_called_once()
                    self.assertEqual(5, mock.call_count)

        return url, organisation

    def test_main_help(self):
        """
        Test main entry point to ensure no exceptions are raised.
        """
        command = Command()
        self.assertIsNotNone(command)

        _, organisation = self.__login(command)

        with patch.object(sys, 'argv', ['program', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                command.main()

            self.assertEqual(0, exc_info.value.code)

    def test_main_debug(self):
        """
        Test turning on of debug.
        """
        command = Command()
        self.assertIsNotNone(command)

        with patch.object(sys, 'argv', ['program', 'list', 'process']):
            with patch.object(command, 'login', side_effect=Exception):
                with pytest.raises(Exception):
                    command.main()

            self.assertEqual(logging.WARNING, command._logger.level)
            self.assertEqual(logging.INFO, command._Command__print_level)

        with patch.object(sys, 'argv', ['program', 'list', 'process', '--debug']):
            with patch.object(command, 'login', side_effect=Exception):
                with pytest.raises(Exception):
                    command.main()

            self.assertEqual(logging.DEBUG, command._logger.level)
            self.assertEqual(logging.DEBUG, command._Command__print_level)

    def test_main_define(self):
        """
        Test main entry point for define.
        """
        command = Command()
        self.assertIsNotNone(command)

        _, organisation = self.__login(command)

        with patch.object(sys, 'argv', ['program', 'define', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                command.main()

            self.assertEqual(0, exc_info.value.code)

        processes = ['process1', 'process2']

        with patch.object(sys, 'argv', ['program', 'define'] + processes):
            with patch.object(command, 'login', return_value=(organisation, None, None)) as mock_login:
                with patch.object(Command, 'define_process', return_value={}) as mock_define_processs:
                    command.main()

                    mock_login.assert_called_once()
                    mock_define_processs.assert_called()
                    self.assertEqual(len(processes), mock_define_processs.call_count)

                    for process in processes:
                        file = f"{process}{Command._YAML_EXTENSION}"
                        self.assertTrue(os.path.exists(file))
                        os.remove(file)

    def test_main_delete_process(self):
        """
        Test main entry point for delete process.
        """
        command = Command()
        self.assertIsNotNone(command)

        _, organisation = self.__login(command)

        with patch.object(sys, 'argv', ['program', 'delete', 'process', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                command.main()

            self.assertEqual(0, exc_info.value.code)

        processes = ['process1', 'process2']

        with patch.object(sys, 'argv', ['program', 'delete', 'process'] + processes):
            with patch.object(command, 'login', return_value=(organisation, None, None)) as mock_login:
                with patch.object(Command, 'delete_process', return_value=True) as mock_delete_process:
                    command.main()

                    mock_login.assert_called_once()
                    mock_delete_process.assert_called()
                    self.assertEqual(len(processes), mock_delete_process.call_count)

    def test_main_delete_upload(self):
        """
        Test main entry point for delete upload.
        """
        command = Command()
        self.assertIsNotNone(command)

        _, organisation = self.__login(command)

        with patch.object(sys, 'argv', ['program', 'delete', 'upload', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                command.main()

            self.assertEqual(0, exc_info.value.code)

        uploads = ['upload1', 'upload2']

        with patch.object(sys, 'argv', ['program', 'delete', 'upload'] + uploads):
            with patch.object(command, 'login', return_value=(organisation, None, None)) as mock_login:
                with patch.object(Command, 'delete_upload', return_value=True) as mock_delete_upload:
                    command.main()

                    mock_login.assert_called_once()
                    mock_delete_upload.assert_called()
                    self.assertEqual(len(uploads), mock_delete_upload.call_count)

    def test_main_display_process(self):
        """
        Test main entry point for display process.
        """
        command = Command()
        self.assertIsNotNone(command)

        _, organisation = self.__login(command)

        with patch.object(sys, 'argv', ['program', 'display', 'process', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                command.main()

            self.assertEqual(0, exc_info.value.code)

        processes = ['process1', 'process2']

        with patch.object(sys, 'argv', ['program', 'display', 'process'] + processes):
            with patch.object(command, 'login', return_value=(organisation, None, None)) as mock_login:
                with patch.object(Command, 'display_process', return_value=False) as mock_display_process:
                    command.main()

                    mock_login.assert_called_once()
                    mock_display_process.assert_called()
                    self.assertEqual(len(processes), mock_display_process.call_count)

    def test_main_display_service(self):
        """
        Test main entry point for display service.
        """
        command = Command()
        self.assertIsNotNone(command)

        _, organisation = self.__login(command)

        with patch.object(sys, 'argv', ['program', 'display', 'service', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                command.main()

            self.assertEqual(0, exc_info.value.code)

        services = ['service1', 'service2']

        with patch.object(sys, 'argv', ['program', 'display', 'service'] + services):
            with patch.object(command, 'login', return_value=(organisation, None, None)) as mock_login:
                with patch.object(Command, 'display_service', return_value=True) as mock_display_service:
                    command.main()

                    mock_login.assert_called_once()
                    mock_display_service.assert_called()
                    self.assertEqual(len(services), mock_display_service.call_count)

    def test_main_download_process(self):
        """
        Test main entry point for download process.
        """
        command = Command()
        self.assertIsNotNone(command)

        _, organisation = self.__login(command)

        with open(self.fixture_path('process.json'), 'r') as file:
            process_content = json.loads(file.read())

        process = Process(organisation._session)
        process._set_model_from_response(process_content, ProcessSchema(), organisation_id=organisation.id)

        with patch.object(sys, 'argv', ['program', 'download', 'process', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                command.main()

            self.assertEqual(0, exc_info.value.code)

        processes = ['process1', 'process2']

        with patch.object(sys, 'argv', ['program', 'download', 'process'] + processes + ['--remove']):
            with patch.object(command, 'login', return_value=(organisation, None, None)) as mock_login:
                with patch.object(Command, 'download_process_execution', return_value=process) as mock_download_process_execution:
                    with patch.object(Command, 'remove_process_and_inputs') as mock_remove_process_and_inputs:
                        command.main()

                        mock_login.assert_called_once()
                        mock_download_process_execution.assert_called()
                        self.assertEqual(len(processes), mock_download_process_execution.call_count)
                        mock_remove_process_and_inputs.assert_called()
                        self.assertEqual(len(processes), mock_remove_process_and_inputs.call_count)

    def test_main_download_upload(self):
        """
        Test main entry point for download upload.
        """
        command = Command()
        self.assertIsNotNone(command)

        _, organisation = self.__login(command)

        with patch.object(sys, 'argv', ['program', 'download', 'upload', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                command.main()

            self.assertEqual(0, exc_info.value.code)

        uploads = ['upload1', 'upload2']

        with patch.object(sys, 'argv', ['program', 'download', 'upload'] + uploads):
            with patch.object(command, 'login', return_value=(organisation, None, None)) as mock_login:
                with patch.object(Command, 'download_upload') as mock_download_upload:
                    command.main()

                    mock_login.assert_called_once()
                    mock_download_upload.assert_called()
                    self.assertEqual(len(uploads), mock_download_upload.call_count)

    def test_main_list_processes(self):
        """
        Test main entry point for list processes.
        """
        command = Command()
        self.assertIsNotNone(command)

        _, organisation = self.__login(command)

        with patch.object(sys, 'argv', ['program', 'list', 'process', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                command.main()

            self.assertEqual(0, exc_info.value.code)

        with patch.object(sys, 'argv', ['program', 'list', 'process']):
            with patch.object(command, 'login', return_value=(organisation, None, None)) as mock_login:
                with patch.object(Command, 'list_processes') as mock_list_processes:
                    command.main()

                    mock_login.assert_called_once()
                    mock_list_processes.assert_called_once()

    def test_main_list_services(self):
        """
        Test main entry point for list services.
        """
        command = Command()
        self.assertIsNotNone(command)

        _, organisation = self.__login(command)

        with patch.object(sys, 'argv', ['program', 'list', 'service', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                command.main()

            self.assertEqual(0, exc_info.value.code)

        with patch.object(sys, 'argv', ['program', 'list', 'service']):
            with patch.object(command, 'login', return_value=(organisation, None, None)) as mock_login:
                with patch.object(Command, 'list_services') as mock_list_services:
                    command.main()

                    mock_login.assert_called_once()
                    mock_list_services.assert_called_once()

    def test_main_list_uploads(self):
        """
        Test main entry point for list uploads.
        """
        command = Command()
        self.assertIsNotNone(command)

        _, organisation = self.__login(command)

        with patch.object(sys, 'argv', ['program', 'list', 'upload', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                command.main()

            self.assertEqual(0, exc_info.value.code)

        with patch.object(sys, 'argv', ['program', 'list', 'upload']):
            with patch.object(command, 'login', return_value=(organisation, None, None)) as mock_login:
                with patch.object(Command, 'list_uploads') as mock_list_uploads:
                    command.main()

                    mock_login.assert_called_once()
                    mock_list_uploads.assert_called_once()

    def test_main_start(self):
        """
        Test main entry point for start.
        """
        command = Command()
        self.assertIsNotNone(command)

        _, organisation = self.__login(command)

        with open(self.fixture_path('process.json'), 'r') as file:
            process_content = json.loads(file.read())

        process = Process(organisation._session)
        process._set_model_from_response(process_content, ProcessSchema(), organisation_id=organisation.id)

        with patch.object(sys, 'argv', ['program', 'start', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                command.main()

            self.assertEqual(0, exc_info.value.code)

        service_or_yamls = ['service1', 'service2']

        with patch.object(sys, 'argv', ['program', 'start'] + service_or_yamls + ['--download', '--remove']):
            with patch.object(command, 'login', return_value=(organisation, None, None)) as mock_login:
                with patch.object(Command, 'extract_start_parameters', return_value=('Service', 'Process', [], [], {}, [])) as mock_extract_start_parametersn:
                    with patch.object(Command, 'start_process', return_value=process) as mock_start_process:
                        with patch.object(Command, '_Command__print_process', return_value=process) as mock_print_process:
                            with patch.object(Command, 'download_process_execution', return_value=process) as mock_download_process_execution:
                                with patch.object(Command, 'remove_process_and_inputs', return_value=process) as mock_remove_process_and_inputs:
                                    command.main()

                                    mock_login.assert_called_once()
                                    mock_extract_start_parametersn.assert_called()
                                    self.assertEqual(len(service_or_yamls), mock_extract_start_parametersn.call_count)
                                    mock_download_process_execution.assert_called()
                                    self.assertEqual(len(service_or_yamls), mock_extract_start_parametersn.call_count)
                                    mock_start_process.assert_called()
                                    self.assertEqual(len(service_or_yamls), mock_start_process.call_count)
                                    mock_print_process.assert_called()
                                    self.assertEqual(len(service_or_yamls), mock_print_process.call_count)
                                    mock_remove_process_and_inputs.assert_called()
                                    self.assertEqual(len(service_or_yamls), mock_remove_process_and_inputs.call_count)

    def test_main_template(self):
        """
        Test main entry point for template.
        """
        command = Command()
        self.assertIsNotNone(command)

        _, organisation = self.__login(command)

        with patch.object(sys, 'argv', ['program', 'template', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                command.main()

            self.assertEqual(0, exc_info.value.code)

        services = ['service1', 'service2']

        with patch.object(sys, 'argv', ['program', 'template'] + services):
            with patch.object(command, 'login', return_value=(organisation, None, None)) as mock_login:
                with patch.object(Command, 'template_service', return_value={}) as mock_template_service:
                    command.main()

                    mock_login.assert_called_once()
                    mock_template_service.assert_called()
                    self.assertEqual(len(services), mock_template_service.call_count)

                    for service in services:
                        file = f"{service}{Command._YAML_EXTENSION}"
                        self.assertTrue(os.path.exists(file))
                        os.remove(file)

    def test_main_upload(self):
        """
        Test main entry point for upload.
        """
        command = Command()
        self.assertIsNotNone(command)

        _, organisation = self.__login(command)

        with patch.object(sys, 'argv', ['program', 'upload', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                command.main()

            self.assertEqual(0, exc_info.value.code)

        with patch.object(sys, 'argv', ['program', 'upload', 'upload_name', 'GeoJSON', 'path/to/file']):
            with patch.object(command, 'login', return_value=(organisation, None, None)) as mock_login:
                with patch.object(Command, 'upload') as mock_upload:
                    command.main()

                    mock_login.assert_called_once()
                    mock_upload.assert_called()
                    self.assertEqual(1, mock_upload.call_count)

    def test_main_unknown_command(self):
        """
        Test main entry point for unknown command.
        """
        command = Command()
        self.assertIsNotNone(command)

        _, organisation = self.__login(command)

        with patch.object(sys, 'argv', ['program', 'rubbish', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                command.main()

            self.assertEqual(2, exc_info.value.code)

    def test_provision_process(self):
        """
        Test create process.
        """
        command = Command()
        self.assertIsNotNone(command)

        url, organisation = self.__login(command)

        with open(self.fixture_path('service.json'), 'r') as file:
            service_content = json.loads(file.read())

        with open(self.fixture_path('process.json'), 'r') as file:
            process_content = json.loads(file.read())

        process_name = process_content.get(Model._FIELD_NAME)

        with open(self.fixture_path('service.json'), 'r') as file:
            service_content = json.loads(file.read())

        with open(self.fixture_path('extras.json'), 'r') as file:
            extras_content = json.loads(file.read())

        service = Service(organisation._session)
        service._set_model_from_response(service_content, ServiceSchema(), organisation_id=organisation.id)

        new_process_path = Process._PATH_NEW.format(organisation_id=organisation.id)
        create_process_path = Process._PATH_CREATE.format(organisation_id=organisation.id)

        with open(self.fixture_path('data.json'), 'r') as file:
            data_content = json.loads(file.read())

        data = Data(organisation._session)
        data._set_model_from_response(data_content, DataSchema(), organisation_id=organisation.id)

        with open(self.fixture_path('data_file.json'), 'r') as file:
            file_content = json.loads(file.read())

        files_path = Data._PATH_FILES.format(organisation_id=organisation.id, data_id=data.id)

        options = {}
        data_items = []
        dispatchers = []

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{new_process_path}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content, Model._RESPONSE_KEY_EXTRAS: {Model._FIELD_DISPATCHERS: extras_content}}))
            mock.post(f"{url}{create_process_path}",
                      text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content, Model._RESPONSE_KEY_EXTRAS: {Model._FIELD_DISPATCHERS: extras_content}}))

            process = organisation.new_process(name=process_name, service=service)
            self.assertIsNotNone(process)

            command._Command__provision_process(process, data_items, options, dispatchers)

            self.assertEqual(2, mock.call_count)

        options = {'rubbish': 6}

        match = i18n.t('models.process.cannot_find_option', option=list(options.keys())[0])
        match = re.escape(match)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{new_process_path}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content, Model._RESPONSE_KEY_EXTRAS: {Model._FIELD_DISPATCHERS: extras_content}}))
            mock.post(f"{url}{create_process_path}",
                      text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content, Model._RESPONSE_KEY_EXTRAS: {Model._FIELD_DISPATCHERS: extras_content}}))
            mock.get(f"{url}{files_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [file_content]}))

            process = organisation.new_process(name=process_name, service=service)
            self.assertIsNotNone(process)

            with pytest.raises(ModelError, match=match):
                command._Command__provision_process(process, data_items, options, dispatchers)

            self.assertEqual(1, mock.call_count)

        options = {'maximum_scan_days': 6, 'output_storage_period': 7, 'run_type': 'run_once', 'repeat_count': 1, 'repeat_start': None, 'repeat_end': None,
                   'repeat_gap': None, 'repeat_offset': None}
        data_items = [data, data, data, data]

        match = i18n.t('models.process.wrong_file_type', expected='GeoTIFF', actual='ESRI Shapefile')
        match = re.escape(match)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{new_process_path}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content, Model._RESPONSE_KEY_EXTRAS: {Model._FIELD_DISPATCHERS: extras_content}}))
            mock.post(f"{url}{create_process_path}",
                      text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content, Model._RESPONSE_KEY_EXTRAS: {Model._FIELD_DISPATCHERS: extras_content}}))
            mock.get(f"{url}{files_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [file_content]}))

            process = organisation.new_process(name=process_name, service=service)
            self.assertIsNotNone(process)

            with pytest.raises(ModelError, match=match):
                command._Command__provision_process(process, data_items, options, dispatchers)

            self.assertEqual(3, mock.call_count)

        options = {'maximum_scan_days': 6, 'output_storage_period': 7, 'run_type': 'run_once', 'repeat_count': 1, 'repeat_start': None, 'repeat_end': None,
                   'repeat_gap': None, 'repeat_offset': None}
        data_items = [data]
        dispatchers = [{Model._FIELD_NAME: 'AWS S3', Model._FIELD_OPTIONS: {'rubbish': 1}}]

        match = i18n.t('models.process.cannot_find_dispatcher_option', option=list(dispatchers[0].get(Model._FIELD_OPTIONS).keys())[0])
        match = re.escape(match)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{new_process_path}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content, Model._RESPONSE_KEY_EXTRAS: {Model._FIELD_DISPATCHERS: extras_content}}))
            mock.post(f"{url}{create_process_path}",
                      text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content, Model._RESPONSE_KEY_EXTRAS: {Model._FIELD_DISPATCHERS: extras_content}}))
            mock.get(f"{url}{files_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [file_content]}))

            process = organisation.new_process(name=process_name, service=service)
            self.assertIsNotNone(process)

            with pytest.raises(ModelError, match=match):
                command._Command__provision_process(process, data_items, options, dispatchers)

            self.assertEqual(2, mock.call_count)

        dispatchers = [{Model._FIELD_NAME: 'AWS S3', Model._FIELD_OPTIONS: {'bucket': 'bucket'}}]

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{new_process_path}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content, Model._RESPONSE_KEY_EXTRAS: {Model._FIELD_DISPATCHERS: extras_content}}))
            mock.post(f"{url}{create_process_path}",
                      text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content, Model._RESPONSE_KEY_EXTRAS: {Model._FIELD_DISPATCHERS: extras_content}}))
            mock.get(f"{url}{files_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [file_content]}))

            process = organisation.new_process(name=process_name, service=service)
            self.assertIsNotNone(process)

            command._Command__provision_process(process, data_items, options, dispatchers)

            self.assertEqual(3, mock.call_count)

        dispatchers = None

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{new_process_path}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content, Model._RESPONSE_KEY_EXTRAS: {Model._FIELD_DISPATCHERS: extras_content}}))
            mock.post(f"{url}{create_process_path}",
                      text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content, Model._RESPONSE_KEY_EXTRAS: {Model._FIELD_DISPATCHERS: extras_content}}))
            mock.get(f"{url}{files_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [file_content]}))

            with create_pipe_input() as input:
                input.send_text('\n')

                with create_app_session(input=input, output=DummyOutput()):
                    process = organisation.new_process(name=process_name, service=service)
                    self.assertIsNotNone(process)

                    command._Command__provision_process(process, data_items, options, dispatchers)

            self.assertEqual(3, mock.call_count)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{new_process_path}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content, Model._RESPONSE_KEY_EXTRAS: {Model._FIELD_DISPATCHERS: extras_content}}))
            mock.post(f"{url}{create_process_path}",
                      text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content, Model._RESPONSE_KEY_EXTRAS: {Model._FIELD_DISPATCHERS: extras_content}}))
            mock.get(f"{url}{files_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [file_content]}))

            with create_pipe_input() as input:
                input.send_text(f"{i18n.t('command.prompt_yes')}\n")
                input.send_text(f"{i18n.t('command.prompt_yes')}\n")
                input.send_text('bucket\n')
                input.send_text('\n')
                input.send_text('\n')
                input.send_text('\n')
                input.send_text('\n')
                input.send_text('\n')

                with create_app_session(input=input, output=DummyOutput()):
                    process = organisation.new_process(name=process_name, service=service)
                    self.assertIsNotNone(process)

                    command._Command__provision_process(process, data_items, options, dispatchers)

            self.assertEqual(3, mock.call_count)

    def test_define_process(self):
        """
        Test define process.
        """
        command = Command()
        self.assertIsNotNone(command)

        url, organisation = self.__login(command)
        processes_path = Organisation._PATH_PROCESSES.format(organisation_id=organisation.id)
        services_path = Organisation._PATH_SERVICES.format(organisation_id=organisation.id)

        with open(self.fixture_path('process.json'), 'r') as file:
            process_content = json.loads(file.read())

        process_name = process_content.get(Model._FIELD_NAME)

        with open(self.fixture_path('service.json'), 'r') as file:
            service_content = json.loads(file.read())

        service_ssd_id = service_content.get(Model._FIELD_SSD_ID)
        service_name = service_content.get(Model._FIELD_NAME)

        with open(self.fixture_path('extras.json'), 'r') as file:
            extras_content = json.loads(file.read())

        process_content[Model._FIELD_DISPATCHERS] = extras_content
        process = Process(organisation._session)
        process._set_model_from_response(process_content, ProcessSchema(), organisation_id=organisation.id)

        with open(self.fixture_path('data.json'), 'r') as file:
            data_content = json.loads(file.read())

        data_id = data_content.get(Model._FIELD_ID)
        uploaded_data_path = Organisation._PATH_DATA.format(organisation_id=organisation.id)
        data_path = Data._PATH_GET.format(organisation_id=organisation.id, data_id=data_id)

        with open(self.fixture_path('data_file.json'), 'r') as file:
            file_content = json.loads(file.read())

        files_path = Data._PATH_FILES.format(organisation_id=organisation.id, data_id=data_id)

        match = i18n.t('command.no_such_process', process=process_name)
        match = re.escape(match)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{processes_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))

            with pytest.raises(CommandError, match=match):
                command.define_process(organisation, process_name)

            self.assertEqual(2, mock.call_count)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{processes_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [process_content]}))
            mock.get(f"{url}{services_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))
            mock.get(f"{url}{data_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: data_content}))

            process_definition = command.define_process(organisation, process_name)
            self.assertIsNotNone(process_definition)

            self.assertEqual('', process_definition[Command._YAML_SERVICE_NAME])
            self.assertEqual(process_name, process_definition[Command._YAML_PROCESS_NAME])
            self.assertEqual(len(process_content[Model._FIELD_INPUTS]), len(process_definition[Command._YAML_INPUTS]))
            self.assertEqual(0, len(process_definition[Command._YAML_STORAGE]))
            self.assertEqual(len(process_content[Model._FIELD_OPTIONS]) + 7, len(process_definition[Command._YAML_OPTIONS]))  # With standard options.
            self.assertEqual(len(extras_content), len(process_definition[Command._YAML_DISPATCHERS]))

            self.assertEqual(4, mock.call_count)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{processes_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [process_content]}))
            mock.get(f"{url}{services_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [service_content]}))
            mock.get(f"{url}{data_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: data_content}))

            process_definition = command.define_process(organisation, process_name)
            self.assertIsNotNone(process_definition)

            self.assertEqual(service_name, process_definition[Command._YAML_SERVICE_NAME])
            self.assertEqual(process_name, process_definition[Command._YAML_PROCESS_NAME])
            self.assertEqual(len(process_content[Model._FIELD_INPUTS]), len(process_definition[Command._YAML_INPUTS]))
            self.assertEqual(0, len(process_definition[Command._YAML_STORAGE]))
            self.assertEqual(len(process_content[Model._FIELD_OPTIONS]) + 7, len(process_definition[Command._YAML_OPTIONS]))  # With standard options.
            self.assertEqual(len(extras_content), len(process_definition[Command._YAML_DISPATCHERS]))

            self.assertEqual(4, mock.call_count)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{processes_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [process_content]}))
            mock.get(f"{url}{services_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [service_content]}))
            mock.get(f"{url}{data_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: data_content}))
            mock.get(f"{url}{uploaded_data_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [data_content]}))
            mock.get(f"{url}{files_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [file_content]}))

            process_definition = command.define_process(organisation, process_name, download_inputs=True)
            self.assertIsNotNone(process_definition)

            self.assertEqual(service_name, process_definition[Command._YAML_SERVICE_NAME])
            self.assertEqual(process_name, process_definition[Command._YAML_PROCESS_NAME])
            self.assertEqual(0, len(process_definition[Command._YAML_INPUTS]))
            self.assertEqual(0, len(process_definition[Command._YAML_STORAGE]))
            self.assertEqual(len(process_content[Model._FIELD_OPTIONS]) + 7, len(process_definition[Command._YAML_OPTIONS]))  # With standard options.
            self.assertEqual(len(extras_content), len(process_definition[Command._YAML_DISPATCHERS]))

            self.assertEqual(10, mock.call_count)

        file_content[Model._FIELD_FILE_TYPE] = process_content[Model._FIELD_INPUTS][0][Model._FIELD_FILE_TYPE]

        with patch.object(command, '_Command__download_files') as mock_download_files:
            with requests_mock.Mocker() as mock:
                mock.get(f"{url}{processes_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [process_content]}))
                mock.get(f"{url}{services_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [service_content]}))
                mock.get(f"{url}{data_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: data_content}))
                mock.get(f"{url}{uploaded_data_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [data_content]}))
                mock.get(f"{url}{files_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [file_content]}))

                process_definition = command.define_process(organisation, process_name, download_inputs=True)
                self.assertIsNotNone(process_definition)

                self.assertEqual(service_name, process_definition[Command._YAML_SERVICE_NAME])
                self.assertEqual(process_name, process_definition[Command._YAML_PROCESS_NAME])
                self.assertEqual(1, len(process_definition[Command._YAML_INPUTS]))
                self.assertEqual(0, len(process_definition[Command._YAML_STORAGE]))
                self.assertEqual(len(process_content[Model._FIELD_OPTIONS]) + 7, len(process_definition[Command._YAML_OPTIONS]))  # With standard options.
                self.assertEqual(len(extras_content), len(process_definition[Command._YAML_DISPATCHERS]))

                self.assertEqual(10, mock.call_count)
                mock_download_files.assert_called_once()

        storage_id = command._Command__get_storage_id(process.id, 1, 3, service_ssd_id, 0)
        storage_data_path = Data._PATH_GET.format(organisation_id=organisation.id, data_id=storage_id)
        storage_files_path = Data._PATH_FILES.format(organisation_id=organisation.id, data_id=storage_id)

        with patch.object(command, '_Command__download_files') as mock_download_files:
            with requests_mock.Mocker() as mock:
                mock.get(f"{url}{processes_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [process_content]}))
                mock.get(f"{url}{services_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [service_content]}))
                mock.get(f"{url}{data_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: data_content}))
                mock.get(f"{url}{uploaded_data_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [data_content]}))
                mock.get(f"{url}{files_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [file_content]}))
                mock.get(f"{url}{storage_data_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: data_content}))
                mock.get(f"{url}{storage_files_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [file_content]}))

                process_definition = command.define_process(organisation, process_name, download_storage=True)
                self.assertIsNotNone(process_definition)

                self.assertEqual(service_name, process_definition[Command._YAML_SERVICE_NAME])
                self.assertEqual(process_name, process_definition[Command._YAML_PROCESS_NAME])
                self.assertEqual(len(process_content[Model._FIELD_INPUTS]), len(process_definition[Command._YAML_INPUTS]))
                self.assertEqual(1, len(process_definition[Command._YAML_STORAGE]))
                self.assertEqual(len(process_content[Model._FIELD_OPTIONS]) + 7, len(process_definition[Command._YAML_OPTIONS]))  # With standard options.
                self.assertEqual(len(extras_content), len(process_definition[Command._YAML_DISPATCHERS]))

                self.assertEqual(9, mock.call_count)
                mock_download_files.assert_called_once()

    def test_delete_process(self):
        """
        Test delete process.
        """
        command = Command()
        self.assertIsNotNone(command)

        url, organisation = self.__login(command)
        processes_path = Organisation._PATH_PROCESSES.format(organisation_id=organisation.id)

        with open(self.fixture_path('process.json'), 'r') as file:
            process_content = json.loads(file.read())

        process_id = process_content.get(Model._FIELD_ID)
        process_name = process_content.get(Model._FIELD_NAME)
        delete_process_path = Process._PATH_DELETE.format(organisation_id=organisation.id, process_id=process_id)

        with open(self.fixture_path('process_execution.json'), 'r') as file:
            execution_content = json.loads(file.read())

        execution_id = execution_content.get(Model._FIELD_ID)
        executions_path = Process._PATH_EXECUTIONS.format(organisation_id=organisation.id, process_id=process_id)
        delete_execution_path = ProcessExecution._PATH_DELETE.format(organisation_id=organisation.id, process_execution_id=execution_id)

        force = False

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{processes_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))

            attempted_delete = command.delete_process(organisation, process_name, force)
            self.assertFalse(attempted_delete)

            self.assertEqual(2, mock.call_count)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{processes_path}?limit=1&reverse=False&filter%5B{Model._FIELD_NAME}__{Model._FILTER_MODIFIER_CONTAINS}%5D={execution_id}",
                     text=json.dumps({Model._RESPONSE_KEY_LIST: []}))
            mock.get(f"{url}{processes_path}?limit=24&reverse=False", text=json.dumps({Model._RESPONSE_KEY_LIST: [process_content]}))
            mock.get(f"{url}{executions_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))

            attempted_delete = command.delete_process(organisation, execution_id, force)
            self.assertFalse(attempted_delete)

            self.assertEqual(3, mock.call_count)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{processes_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [process_content]}))

            with create_pipe_input() as input:
                input.send_text(f"{i18n.t('command.prompt_no')}\n")

                with create_app_session(input=input, output=DummyOutput()):
                    attempted_delete = command.delete_process(organisation, process_name, force)
                    self.assertTrue(attempted_delete)

            self.assertEqual(1, mock.call_count)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{processes_path}?limit=1&reverse=False&filter%5B{Model._FIELD_NAME}__{Model._FILTER_MODIFIER_CONTAINS}%5D={execution_id}",
                     text=json.dumps({Model._RESPONSE_KEY_LIST: []}))
            mock.get(f"{url}{processes_path}?limit=24&reverse=False", text=json.dumps({Model._RESPONSE_KEY_LIST: [process_content]}))
            mock.get(f"{url}{executions_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [execution_content]}))

            with create_pipe_input() as input:
                input.send_text(f"{i18n.t('command.prompt_no')}\n")

                with create_app_session(input=input, output=DummyOutput()):
                    attempted_delete = command.delete_process(organisation, execution_id, force)
                    self.assertTrue(attempted_delete)

            self.assertEqual(3, mock.call_count)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{processes_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [process_content]}))
            mock.delete(f"{url}{delete_process_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [process_content]}))

            with create_pipe_input() as input:
                input.send_text(f"{i18n.t('command.prompt_yes')}\n")

                with create_app_session(input=input, output=DummyOutput()):
                    attempted_delete = command.delete_process(organisation, process_name, force)
                    self.assertTrue(attempted_delete)

            self.assertEqual(2, mock.call_count)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{processes_path}?limit=1&reverse=False&filter%5B{Model._FIELD_NAME}__{Model._FILTER_MODIFIER_CONTAINS}%5D={execution_id}",
                     text=json.dumps({Model._RESPONSE_KEY_LIST: []}))
            mock.get(f"{url}{processes_path}?limit=24&reverse=False", text=json.dumps({Model._RESPONSE_KEY_LIST: [process_content]}))
            mock.get(f"{url}{executions_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [execution_content]}))
            mock.delete(f"{url}{delete_execution_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [execution_content]}))

            with create_pipe_input() as input:
                input.send_text(f"{i18n.t('command.prompt_yes')}\n")

                with create_app_session(input=input, output=DummyOutput()):
                    attempted_delete = command.delete_process(organisation, execution_id, force)
                    self.assertTrue(attempted_delete)

            self.assertEqual(4, mock.call_count)

        force = True

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{processes_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [process_content]}))
            mock.delete(f"{url}{delete_process_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [process_content]}))

            attempted_delete = command.delete_process(organisation, process_name, force)
            self.assertTrue(attempted_delete)

            self.assertEqual(2, mock.call_count)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{processes_path}?limit=1&reverse=False&filter%5B{Model._FIELD_NAME}__{Model._FILTER_MODIFIER_CONTAINS}%5D={execution_id}",
                     text=json.dumps({Model._RESPONSE_KEY_LIST: []}))
            mock.get(f"{url}{processes_path}?limit=24&reverse=False", text=json.dumps({Model._RESPONSE_KEY_LIST: [process_content]}))
            mock.get(f"{url}{executions_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [execution_content]}))
            mock.delete(f"{url}{delete_execution_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [execution_content]}))

            attempted_delete = command.delete_process(organisation, execution_id, force)
            self.assertTrue(attempted_delete)

            self.assertEqual(4, mock.call_count)

    def test_delete_upload(self):
        """
        Test delete process.
        """
        command = Command()
        self.assertIsNotNone(command)

        url, organisation = self.__login(command)
        data_path = Organisation._PATH_DATA.format(organisation_id=organisation.id)

        with open(self.fixture_path('data.json'), 'r') as file:
            data_content = json.loads(file.read())

        upload_name = data_content.get(Model._FIELD_NAME)
        upload_id = data_content.get(Model._FIELD_ID)

        delete_data_path = Data._PATH_DELETE.format(organisation_id=organisation.id, data_id=upload_id)

        force = False

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{data_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))

            attempted_delete = command.delete_upload(organisation, upload_name, force)
            self.assertFalse(attempted_delete)

            self.assertEqual(2, mock.call_count)

        upload_id = uuid.uuid4()

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{data_path}?limit=1&reverse=False&filter%5Bname__begins_with%5D={upload_id}", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))
            mock.get(f"{url}{data_path}?limit=24&reverse=False", text=json.dumps({Model._RESPONSE_KEY_LIST: [data_content]}))

            attempted_delete = command.delete_upload(organisation, upload_id, force)
            self.assertFalse(attempted_delete)

            self.assertEqual(2, mock.call_count)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{data_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [data_content]}))

            with create_pipe_input() as input:
                input.send_text(f"{i18n.t('command.prompt_no')}\n")

                with create_app_session(input=input, output=DummyOutput()):
                    attempted_delete = command.delete_upload(organisation, upload_name, force)
                    self.assertTrue(attempted_delete)

            self.assertEqual(1, mock.call_count)

        upload_id = data_content.get(Model._FIELD_ID)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{data_path}?limit=1&reverse=False&filter%5Bname__begins_with%5D={upload_id}", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))
            mock.get(f"{url}{data_path}?limit=24&reverse=False", text=json.dumps({Model._RESPONSE_KEY_LIST: [data_content]}))

            with create_pipe_input() as input:
                input.send_text(f"{i18n.t('command.prompt_no')}\n")

                with create_app_session(input=input, output=DummyOutput()):
                    attempted_delete = command.delete_upload(organisation, upload_id, force)
                    self.assertTrue(attempted_delete)

            self.assertEqual(2, mock.call_count)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{data_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [data_content]}))
            mock.delete(f"{url}{delete_data_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [data_content]}))

            with create_pipe_input() as input:
                input.send_text(f"{i18n.t('command.prompt_yes')}\n")

                with create_app_session(input=input, output=DummyOutput()):
                    attempted_delete = command.delete_upload(organisation, upload_name, force)
                    self.assertTrue(attempted_delete)

            self.assertEqual(2, mock.call_count)

        upload_id = data_content.get(Model._FIELD_ID)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{data_path}?limit=1&reverse=False&filter%5Bname__begins_with%5D={upload_id}", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))
            mock.get(f"{url}{data_path}?limit=24&reverse=False", text=json.dumps({Model._RESPONSE_KEY_LIST: [data_content]}))
            mock.delete(f"{url}{delete_data_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [data_content]}))

            with create_pipe_input() as input:
                input.send_text(f"{i18n.t('command.prompt_yes')}\n")

                with create_app_session(input=input, output=DummyOutput()):
                    attempted_delete = command.delete_upload(organisation, upload_id, force)
                    self.assertTrue(attempted_delete)

            self.assertEqual(3, mock.call_count)

        force = True

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{data_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [data_content]}))
            mock.delete(f"{url}{delete_data_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [data_content]}))

            attempted_delete = command.delete_upload(organisation, upload_name, force)
            self.assertTrue(attempted_delete)

            self.assertEqual(2, mock.call_count)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{data_path}?limit=1&reverse=False&filter%5Bname__begins_with%5D={upload_id}", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))
            mock.get(f"{url}{data_path}?limit=24&reverse=False", text=json.dumps({Model._RESPONSE_KEY_LIST: [data_content]}))
            mock.delete(f"{url}{delete_data_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [data_content]}))

            attempted_delete = command.delete_upload(organisation, upload_id, force)
            self.assertTrue(attempted_delete)

            self.assertEqual(3, mock.call_count)

        match = i18n.t('session.request_failed', message=400)
        match = re.escape(match)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{data_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [data_content]}))
            mock.delete(f"{url}{delete_data_path}", status_code=400)

            with pytest.raises(RequestError, match=match):
                command.delete_upload(organisation, upload_name, force)

            self.assertEqual(2, mock.call_count)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{data_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [data_content]}))
            mock.delete(f"{url}{delete_data_path}", status_code=400, text=json.dumps({'error_message': Command._Command__DATA_ITEM_STILL_IN_USE}))

            attempted_delete = command.delete_upload(organisation, upload_id, force)
            self.assertTrue(attempted_delete)

            self.assertEqual(2, mock.call_count)

    def test_display_process(self):
        """
        Test display process.
        """
        command = Command()
        self.assertIsNotNone(command)

        url, organisation = self.__login(command)
        processes_path = Organisation._PATH_PROCESSES.format(organisation_id=organisation.id)

        with open(self.fixture_path('process.json'), 'r') as file:
            process_content = json.loads(file.read())

        process_id = process_content.get(Model._FIELD_ID)
        process_name = process_content.get(Model._FIELD_NAME)

        with open(self.fixture_path('data.json'), 'r') as file:
            data_content = json.loads(file.read())

        data_id = data_content.get(Model._FIELD_ID)
        data_path = Data._PATH_GET.format(organisation_id=organisation.id, data_id=data_id)

        with open(self.fixture_path('extras.json'), 'r') as file:
            extras_content = json.loads(file.read())

        process_content[Model._FIELD_DISPATCHERS] = extras_content

        with open(self.fixture_path('process_execution.json'), 'r') as file:
            execution_content = json.loads(file.read())

        executions_path = Process._PATH_EXECUTIONS.format(organisation_id=organisation.id, process_id=process_id)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{processes_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))

            self.assertFalse(command.display_process(organisation, process_name))

            self.assertEqual(2, mock.call_count)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{processes_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [process_content]}))
            mock.get(f"{url}{data_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: data_content}))
            mock.get(f"{url}{executions_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))

            self.assertTrue(command.display_process(organisation, process_name))

            self.assertEqual(5, mock.call_count)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{processes_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [process_content]}))
            mock.get(f"{url}{data_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: data_content}))
            mock.get(f"{url}{executions_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [execution_content]}))

            self.assertTrue(command.display_process(organisation, process_name))

            self.assertEqual(5, mock.call_count)

        execution_content_group = execution_content.copy()
        execution_content_group[Model._FIELD_GROUP_ID] = str(uuid.uuid4())
        execution_content_group[Model._FIELD_GROUP_INDEX] = 1
        execution_content_group[Model._FIELD_GROUP_COUNT] = 2

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{processes_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [process_content]}))
            mock.get(f"{url}{data_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: data_content}))
            mock.get(f"{url}{executions_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [execution_content_group]}))

            self.assertTrue(command.display_process(organisation, process_name))

            self.assertEqual(4, mock.call_count)

    def test_display_service(self):
        """
        Test display service.
        """
        command = Command()
        self.assertIsNotNone(command)

        url, organisation = self.__login(command)
        services_path = Organisation._PATH_SERVICES.format(organisation_id=organisation.id)

        with open(self.fixture_path('service.json'), 'r') as file:
            service_content = json.loads(file.read())

        service_name = service_content.get(Model._FIELD_NAME)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{services_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))

            self.assertFalse(command.display_service(organisation, service_name))

            self.assertEqual(3, mock.call_count)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{services_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [service_content]}))

            self.assertTrue(command.display_service(organisation, service_name))

            self.assertEqual(1, mock.call_count)

    def test_download_execution(self):
        """
        Test download execution.
        """
        command = Command()
        self.assertIsNotNone(command)

        url, organisation = self.__login(command)

        with open(self.fixture_path('process.json'), 'r') as file:
            process_content = json.loads(file.read())

        process = Process(organisation._session)
        process._set_model_from_response(process_content, ProcessSchema(), organisation_id=organisation.id)

        with open(self.fixture_path('data.json'), 'r') as file:
            data_content = json.loads(file.read())

        with open(self.fixture_path('data_file.json'), 'r') as file:
            file_content = json.loads(file.read())

        with open(self.fixture_path('extras.json'), 'r') as file:
            extras_content = json.loads(file.read())

        process_content[Model._FIELD_DISPATCHERS] = extras_content

        with open(self.fixture_path('process_execution.json'), 'r') as file:
            execution_content = json.loads(file.read())

        execution_content[Model._FIELD_GROUP_ID] = str(uuid.uuid4())
        execution_content[Model._FIELD_GROUP_INDEX] = 1
        execution_content[Model._FIELD_GROUP_COUNT] = 2

        execution = ProcessExecution(organisation._session)
        execution._set_model_from_response(execution_content, ProcessExecutionSchema(), organisation_id=organisation.id)

        executions_path = Process._PATH_EXECUTIONS.format(organisation_id=organisation.id, process_id=process.id)
        execution_path = ProcessExecution._PATH_GET.format(organisation_id=organisation.id, process_execution_id=execution.id)

        with open(self.fixture_path('process_service_execution.json'), 'r') as file:
            component_content = json.loads(file.read())

        component_content[Model._FIELD_CHAIN_INDEX] = 0

        components_path = ProcessExecution._PATH_COMPONENTS.format(organisation_id=organisation.id, process_execution_id=execution.id)
        data_paths = []
        files_paths = []

        storage_id = command._Command__get_storage_id(process.id, execution_content[Model._FIELD_GROUP_INDEX], execution_content[Model._FIELD_GROUP_COUNT],
                                                      process.chains[component_content[Model._FIELD_CHAIN_INDEX]].get(Model._FIELD_SSD_ID),
                                                      component_content[Model._FIELD_CHAIN_INDEX])

        for data_id in component_content.get(Model._FIELD_INPUTS) + component_content.get(Model._FIELD_OUTPUTS) + [
            component_content.get(Model._FIELD_STATISTICS_ID), storage_id]:
            data_paths.append(Data._PATH_GET.format(organisation_id=organisation.id, data_id=data_id))
            files_paths.append(Data._PATH_FILES.format(organisation_id=organisation.id, data_id=data_id))

        download_inputs = True
        download_outputs = True
        download_storage = True
        download_statistics = True
        download_intermediate = True
        download_components = None
        wait = True

        with tempfile.TemporaryDirectory() as tmp_dir:
            with requests_mock.Mocker() as mock:
                mock.get(f"{url}{executions_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))
                mock.get(f"{url}{components_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))

                downloads, metrics = command._Command__download_execution(process, download_inputs, download_outputs, download_storage, download_statistics,
                                                                          download_intermediate, download_components, tmp_dir, wait, execution)
                self.assertIsNotNone(downloads)
                self.assertIsNotNone(metrics)

                self.assertEqual([], downloads)
                self.assertEqual([], metrics)

                self.assertEqual(2, mock.call_count)

        with tempfile.TemporaryDirectory() as tmp_dir:
            with requests_mock.Mocker() as mock:
                mock.get(f"{url}{executions_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [execution_content]}))
                mock.get(f"{url}{execution_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: execution_content}))
                mock.get(f"{url}{components_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [component_content]}))

                for data_path in data_paths:
                    mock.get(f"{url}{data_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: data_content}))

                for files_path in files_paths:
                    mock.get(f"{url}{files_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [file_content]}))

                downloads, metrics = command._Command__download_execution(process, download_inputs, download_outputs, download_storage, download_statistics,
                                                                          download_intermediate, download_components, tmp_dir, wait, execution)
                self.assertIsNotNone(downloads)
                self.assertIsNotNone(metrics)

                self.assertEqual(len(files_paths), len(downloads))
                self.assertEqual(1, len(metrics))

                dirs = os.listdir(tmp_dir)
                self.assertEqual(1, len(dirs))
                execution_dir = dirs[0]

                dirs = os.listdir(os.path.join(tmp_dir, execution_dir))
                self.assertEqual(1, len(dirs))
                component_dir = dirs[0]

                dirs = os.listdir(os.path.join(tmp_dir, execution_dir, component_dir))
                self.assertEqual(len(files_paths) - 2, len(dirs))  # No statistics file and storage not yet written.

                for dir in dirs:
                    files = os.listdir(os.path.join(tmp_dir, execution_dir, component_dir, dir))
                    self.assertEqual(2, len(files))  # 2 STAC files.

                self.assertEqual(56, mock.call_count)

    def test_download_files(self):
        """
        Test download files.
        """
        command = Command()
        self.assertIsNotNone(command)

        url, organisation = self.__login(command)

        with open(self.fixture_path('data.json'), 'r') as file:
            data_content = json.loads(file.read())

        data_id = data_content.get(Model._FIELD_ID)

        with open(self.fixture_path('data_file.json'), 'r') as file:
            file_content = json.loads(file.read())

        file = DataFile(organisation._session)
        file._set_model_from_response(file_content, DataFileSchema(), organisation_id=organisation.id, data_id=data_id)

        with patch.object(DataFile, 'download') as mock_download:
            command._Command__download_files(None)
            mock_download.assert_not_called()

        with patch.object(DataFile, 'download') as mock_download:
            command._Command__download_files([])
            mock_download.assert_not_called()

        number_of_downloads = 10
        path = '/path/to/file'
        size = 123
        url = 'https://url.to.file'
        downloads = [(file, path, size)] * number_of_downloads

        with patch.object(DataFile, 'download') as mock_download:
            with patch.object(DataFile, 'download_progress', return_value=(url, path, size)) as mock_download_progress:
                with patch.object(DataFile, 'download_complete', return_value=True) as mock_download_complete:
                    command._Command__download_files(downloads)
                    mock_download.assert_called()
                    self.assertEqual(number_of_downloads, mock_download.call_count)
                    mock_download_progress.assert_called()
                    self.assertEqual(number_of_downloads, mock_download_progress.call_count)
                    mock_download_complete.assert_called()
                    self.assertEqual(number_of_downloads, mock_download_complete.call_count)

    def test_download_process_execution(self):
        """
        Test download process execution.
        """
        command = Command()
        self.assertIsNotNone(command)

        url, organisation = self.__login(command)
        processes_path = Organisation._PATH_PROCESSES.format(organisation_id=organisation.id)

        with open(self.fixture_path('process.json'), 'r') as file:
            process_content = json.loads(file.read())

        process_id = process_content.get(Model._FIELD_ID)
        process_name = process_content.get(Model._FIELD_NAME)

        with open(self.fixture_path('process_execution.json'), 'r') as file:
            execution_content = json.loads(file.read())

        executions_path = Process._PATH_EXECUTIONS.format(organisation_id=organisation.id, process_id=process_id)

        number_of_downloads = 10
        path = '/path/to/file'
        size = 123
        downloads = [(file, path, size)] * number_of_downloads
        metrics = [{Command._METRICS_RUNTIME: 1234}] * 10

        download_inputs = False
        download_outputs = False
        download_storage = False
        download_statistics = False
        download_intermediate = False
        download_components = None
        save_metrics = False
        stac_only = False
        wait_for_execution_to_complete = False

        match = i18n.t('command.no_such_process', process=process_name)
        match = re.escape(match)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{processes_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))

            with pytest.raises(CommandError, match=match):
                command.download_process_execution(organisation, process_name, download_inputs, download_outputs, download_storage, download_statistics,
                                                   download_intermediate, download_components, save_metrics, stac_only, wait_for_execution_to_complete)

            self.assertEqual(2, mock.call_count)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{processes_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [process_content]}))
            mock.get(f"{url}{executions_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))

            process = command.download_process_execution(organisation, process_name, download_inputs, download_outputs, download_storage, download_statistics,
                                                         download_intermediate, download_components, save_metrics, stac_only, wait_for_execution_to_complete)
            self.assertIsNone(process)

            self.assertEqual(2, mock.call_count)

        with patch.object(command, '_Command__download_execution', return_value=(downloads, metrics)) as mock_download_execution:
            with patch.object(command, '_Command__download_files') as mock_download_files:
                with requests_mock.Mocker() as mock:
                    mock.get(f"{url}{processes_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [process_content]}))
                    mock.get(f"{url}{executions_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [execution_content]}))

                    process = command.download_process_execution(organisation, process_name, download_inputs, download_outputs, download_storage,
                                                                 download_statistics, download_intermediate, download_components, save_metrics, stac_only,
                                                                 wait_for_execution_to_complete)
                    self.assertIsNotNone(process)

                    self.assertEqual(2, mock.call_count)
                    mock_download_execution.assert_called_once()
                    mock_download_files.assert_called_once()

        execution_content_in_group = execution_content.copy()
        execution_content_in_group[Model._FIELD_GROUP_ID] = str(uuid.uuid4())

        with patch.object(command, '_Command__download_execution', return_value=(downloads, metrics)) as mock_download_execution:
            with patch.object(command, '_Command__download_files') as mock_download_files:
                with requests_mock.Mocker() as mock:
                    mock.get(f"{url}{processes_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [process_content]}))
                    mock.get(f"{url}{executions_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [execution_content_in_group, execution_content_in_group]}))

                    process = command.download_process_execution(organisation, process_name, download_inputs, download_outputs, download_storage,
                                                                 download_statistics, download_intermediate, download_components, save_metrics, stac_only,
                                                                 wait_for_execution_to_complete)
                    self.assertIsNotNone(process)

                    self.assertEqual(4, mock.call_count)
                    mock_download_execution.assert_called()
                    self.assertEqual(2, mock_download_execution.call_count)
                    mock_download_files.assert_called_once()

        save_metrics = True
        stac_only = True

        with patch('builtins.open', mock_open()) as mock_metrics_file:
            with patch.object(command, '_Command__download_execution', return_value=(downloads, metrics)) as mock_download_execution:
                with patch.object(command, '_Command__download_files') as mock_download_files:
                    with requests_mock.Mocker() as mock:
                        mock.get(f"{url}{processes_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [process_content]}))
                        mock.get(f"{url}{executions_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [execution_content]}))

                        process = command.download_process_execution(organisation, process_name, download_inputs, download_outputs, download_storage,
                                                                     download_statistics, download_intermediate, download_components, save_metrics, stac_only,
                                                                     wait_for_execution_to_complete)
                        self.assertIsNotNone(process)

                        self.assertEqual(2, mock.call_count)
                        mock_metrics_file.assert_called_once()
                        mock_download_execution.assert_called_once()
                        mock_download_files.assert_not_called()

    def test_download_upload(self):
        """
        Test download upload.
        """
        command = Command()
        self.assertIsNotNone(command)

        url, organisation = self.__login(command)
        data_path = Organisation._PATH_DATA.format(organisation_id=organisation.id)

        with open(self.fixture_path('data.json'), 'r') as file:
            data_content = json.loads(file.read())

        data_id = data_content.get(Model._FIELD_ID)
        data_name = data_content.get(Model._FIELD_NAME)

        with open(self.fixture_path('data_file.json'), 'r') as file:
            file_content = json.loads(file.read())

        files_path = Data._PATH_FILES.format(organisation_id=organisation.id, data_id=data_id)

        match = i18n.t('command.no_such_data_item', data=data_name)
        match = re.escape(match)

        with patch.object(command, '_Command__name_to_file_name') as mock_name_to_file_name:
            with requests_mock.Mocker() as mock:
                mock.get(f"{url}{data_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))

                with pytest.raises(CommandError, match=match):
                    command.download_upload(organisation, data_name)

                self.assertEqual(2, mock.call_count)
                mock_name_to_file_name.assert_not_called()

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, 'test')

            with patch.object(command, '_Command__name_to_file_name', return_value=path) as mock_name_to_file_name:
                with requests_mock.Mocker() as mock:
                    mock.get(f"{url}{data_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [data_content]}))
                    mock.get(f"{url}{files_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))

                    command.download_upload(organisation, data_name)

                    self.assertEqual(3, mock.call_count)
                    mock_name_to_file_name.assert_called_once()

                    dirs = os.listdir(tmp_dir)
                    self.assertEqual(1, len(dirs))

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, 'test')
            files = [file_content, file_content, file_content]

            with patch.object(command, '_Command__name_to_file_name', return_value=path) as mock_name_to_file_name:
                with patch.object(command, '_Command__download_files') as mock_download_files:
                    with requests_mock.Mocker() as mock:
                        mock.get(f"{url}{data_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [data_content]}))
                        mock.get(f"{url}{files_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: files}))

                        command.download_upload(organisation, data_name)

                        self.assertEqual(3, mock.call_count)
                        mock_download_files.assert_called()
                        self.assertEqual(1, mock_download_files.call_count)
                        mock_name_to_file_name.assert_called()
                        self.assertEqual(1, mock_name_to_file_name.call_count)

                        dirs = os.listdir(tmp_dir)
                        self.assertEqual(1, len(dirs))
                        upload_dir = os.path.join(tmp_dir, dirs[0])

                        dirs = os.listdir(upload_dir)
                        self.assertEqual(len(files) + 1, len(dirs))  # 1 STAC file per file, plus the collection.

    def test_extract_start_parameters(self):
        """
        Test extract start parameters.
        """
        command = Command()
        self.assertIsNotNone(command)

        service_or_yaml = 'Service'
        input_list = []
        option_list = []

        service_name, process_name, input_files, storage_files, options, dispatchers = command.extract_start_parameters(service_or_yaml, input_list, option_list)
        self.assertIsNotNone(service_name)
        self.assertIsNone(process_name)
        self.assertIsNotNone(input_files)
        self.assertIsNotNone(storage_files)
        self.assertIsNotNone(options)
        self.assertIsNone(dispatchers)

        self.assertEqual(service_or_yaml, service_name)
        self.assertEqual(len(input_list), len(input_files))
        self.assertEqual(0, len(storage_files))
        self.assertEqual(len(options), len(options))

        file_path = os.path.join('/', 'path', 'to')
        input_list = [
            'Input',
            os.path.join(file_path, 'file.tif'),
            {Model._FIELD_NAME: 'Input', Model._FIELD_FILE: os.path.join(file_path, 'file.tif')}
        ]

        option_list = [
            'option1=1',
            'option2=2',
            f"option3={{{Command._KEYWORD_SERVICE_NAME}}}",
            f"option4={{{Command._KEYWORD_NOW}}}",
            f"option5={{{Command._KEYWORD_TODAY}}}",
            f"option6={{{Command._KEYWORD_TOMORROW}}}"
        ]

        now = datetime.now(timezone.utc)
        days = [
            datetime(now.year, now.month, now.day, tzinfo=timezone.utc) + timedelta(days=day) for day in range(0, 7)
        ]
        keyword_day_names = {day.strftime('%A').lower(): day for day in days}

        for keyword in keyword_day_names:
            option_list.append(f"option_{len(option_list) + 1}={{{keyword}}}@12:34")

        service_name, process_name, input_files, storage_files, options, dispatchers = command.extract_start_parameters(service_or_yaml, input_list, option_list)
        self.assertIsNotNone(service_name)
        self.assertIsNone(process_name)
        self.assertIsNotNone(input_files)
        self.assertIsNotNone(storage_files)
        self.assertIsNotNone(options)
        self.assertIsNone(dispatchers)

        self.assertEqual(service_or_yaml, service_name)
        self.assertEqual(len(input_list), len(input_files))
        self.assertEqual(0, len(storage_files))
        self.assertEqual(len(options), len(options))

        for i, option in enumerate(option_list):
            elements = option.split('=')
            key = elements[0]
            value = elements[1]

            if i < 2:
                self.assertEqual(value, options[key])
            else:
                self.assertNotEqual(value, options[key])

        service_or_yaml = self.fixture_path('process.yml')

        service_name, process_name, input_files, storage_files, options, dispatchers = command.extract_start_parameters(service_or_yaml, input_list, option_list)
        self.assertIsNotNone(service_name)
        self.assertIsNotNone(process_name)
        self.assertIsNotNone(input_files)
        self.assertIsNotNone(storage_files)
        self.assertIsNotNone(options)
        self.assertIsNotNone(dispatchers)

    def test_get_data(self):
        """
        Test get data.
        """
        command = Command()
        self.assertIsNotNone(command)

        url, organisation = self.__login(command)
        data_path = Organisation._PATH_DATA.format(organisation_id=organisation.id)

        with open(self.fixture_path('data.json'), 'r') as file:
            data_content = json.loads(file.read())

        data_name = data_content.get(Model._FIELD_NAME)

        match = i18n.t('command.no_such_data_item', data=data_name)
        match = re.escape(match)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{data_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))

            with pytest.raises(CommandError, match=match):
                command.get_data(organisation, data_name)

            self.assertEqual(2, mock.call_count)

        data_id = uuid.uuid4()

        match = i18n.t('command.no_such_data_item', data=data_id)
        match = re.escape(match)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{data_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))

            with pytest.raises(CommandError, match=match):
                command.get_data(organisation, data_id)

            self.assertEqual(2, mock.call_count)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{data_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [data_content]}))

            command.get_data(organisation, data_name)

            self.assertEqual(1, mock.call_count)

        data_id = data_content.get(Model._FIELD_ID)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{data_path}?limit=1&reverse=False&filter%5Bname__begins_with%5D={data_id}", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))
            mock.get(f"{url}{data_path}?limit=24&reverse=False", text=json.dumps({Model._RESPONSE_KEY_LIST: [data_content]}))

            command.get_data(organisation, data_id)

            self.assertEqual(2, mock.call_count)

    def test_get_process_or_execution(self):
        """
        Test get process or execution.
        """
        command = Command()
        self.assertIsNotNone(command)

        url, organisation = self.__login(command)
        processes_path = Organisation._PATH_PROCESSES.format(organisation_id=organisation.id)

        with open(self.fixture_path('process.json'), 'r') as file:
            process_content = json.loads(file.read())

        process_id = process_content.get(Model._FIELD_ID)
        process_name = process_content.get(Model._FIELD_NAME)

        with open(self.fixture_path('process_execution.json'), 'r') as file:
            execution_content = json.loads(file.read())

        execution_id = execution_content.get(Model._FIELD_ID)

        executions_path = Process._PATH_EXECUTIONS.format(organisation_id=organisation.id, process_id=process_id)

        match = i18n.t('command.no_such_process', process=process_name)
        match = re.escape(match)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{processes_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))

            with pytest.raises(CommandError, match=match):
                command.get_process_or_execution(organisation, process_name)

            self.assertEqual(2, mock.call_count)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{processes_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [process_content]}))

            process, execution = command.get_process_or_execution(organisation, process_name)
            self.assertIsNotNone(process)
            self.assertIsNone(execution)

            self.assertEqual(process_name, process.name)

            self.assertEqual(1, mock.call_count)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{processes_path}?limit=1&reverse=False&filter%5B{Model._FIELD_NAME}__{Model._FILTER_MODIFIER_CONTAINS}%5D={process_id}",
                     text=json.dumps({Model._RESPONSE_KEY_LIST: []}))
            mock.get(f"{url}{processes_path}?limit=24&reverse=False", text=json.dumps({Model._RESPONSE_KEY_LIST: [process_content]}))

            process, execution = command.get_process_or_execution(organisation, process_id)
            self.assertIsNotNone(process)
            self.assertIsNone(execution)

            self.assertEqual(process_name, process.name)

            self.assertEqual(2, mock.call_count)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{processes_path}?limit=1&reverse=False&filter%5B{Model._FIELD_NAME}__{Model._FILTER_MODIFIER_CONTAINS}%5D={execution_id}",
                     text=json.dumps({Model._RESPONSE_KEY_LIST: []}))
            mock.get(f"{url}{processes_path}?limit=24&reverse=False", text=json.dumps({Model._RESPONSE_KEY_LIST: [process_content]}))
            mock.get(f"{url}{executions_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [execution_content]}))

            process, execution = command.get_process_or_execution(organisation, execution_id)
            self.assertIsNotNone(process)
            self.assertIsNotNone(execution)

            self.assertEqual(process_name, process.name)
            self.assertEqual(execution_id, str(execution.id))

            self.assertEqual(3, mock.call_count)

    def test_get_service(self):
        """
        Test get service.
        """
        command = Command()
        self.assertIsNotNone(command)

        url, organisation = self.__login(command)
        services_path = Organisation._PATH_SERVICES.format(organisation_id=organisation.id)
        own_services_path = Organisation._PATH_OWN_SERVICES.format(organisation_id=organisation.id)

        with open(self.fixture_path('service.json'), 'r') as file:
            service_content = json.loads(file.read())

        service_id = service_content.get(Model._FIELD_ID)
        service_ssd_id = service_content.get(Model._FIELD_SSD_ID)
        service_name = service_content.get(Model._FIELD_NAME)

        match = i18n.t('command.no_such_service', service=service_name)
        match = re.escape(match)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{services_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))
            mock.get(f"{url}{own_services_path}?limit=24&reverse=False", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))

            with pytest.raises(CommandError, match=match):
                command.get_service(organisation, service_name)

            self.assertEqual(3, mock.call_count)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{services_path}?limit=1&reverse=False&filter%5B{Model._FIELD_NAME}__{Model._FILTER_MODIFIER_BEGINS_WITH}%5D={service_name}",
                     text=json.dumps({Model._RESPONSE_KEY_LIST: []}))
            mock.get(f"{url}{services_path}?limit=24&reverse=False", text=json.dumps({Model._RESPONSE_KEY_LIST: [service_content]}))

            service = command.get_service(organisation, service_name)
            self.assertIsNotNone(service)

            self.assertEqual(service_name, service.name)

            self.assertEqual(2, mock.call_count)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{services_path}?limit=1&reverse=False&filter%5B{Model._FIELD_NAME}__{Model._FILTER_MODIFIER_BEGINS_WITH}%5D={service_id}",
                     text=json.dumps({Model._RESPONSE_KEY_LIST: []}))
            mock.get(f"{url}{services_path}?limit=24&reverse=False", text=json.dumps({Model._RESPONSE_KEY_LIST: [service_content]}))

            service = command.get_service(organisation, service_id)
            self.assertIsNotNone(service)

            self.assertEqual(service_name, service.name)

            self.assertEqual(2, mock.call_count)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{services_path}?limit=1&reverse=False&filter%5B{Model._FIELD_NAME}__{Model._FILTER_MODIFIER_BEGINS_WITH}%5D={service_ssd_id}",
                     text=json.dumps({Model._RESPONSE_KEY_LIST: []}))
            mock.get(f"{url}{services_path}?limit=24&reverse=False", text=json.dumps({Model._RESPONSE_KEY_LIST: [service_content]}))

            service = command.get_service(organisation, service_ssd_id)
            self.assertIsNotNone(service)

            self.assertEqual(service_name, service.name)

            self.assertEqual(2, mock.call_count)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{services_path}?limit=1&reverse=False&filter%5B{Model._FIELD_NAME}__{Model._FILTER_MODIFIER_BEGINS_WITH}%5D={service_name}",
                     text=json.dumps({Model._RESPONSE_KEY_LIST: []}))
            mock.get(f"{url}{services_path}?limit=24&reverse=False", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))
            mock.get(f"{url}{own_services_path}?limit=24&reverse=False", text=json.dumps({Model._RESPONSE_KEY_LIST: [service_content]}))

            service = command.get_service(organisation, service_name)
            self.assertIsNotNone(service)

            self.assertEqual(service_name, service.name)

            self.assertEqual(3, mock.call_count)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{services_path}?limit=1&reverse=False&filter%5B{Model._FIELD_NAME}__{Model._FILTER_MODIFIER_BEGINS_WITH}%5D={service_id}",
                     text=json.dumps({Model._RESPONSE_KEY_LIST: []}))
            mock.get(f"{url}{services_path}?limit=24&reverse=False", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))
            mock.get(f"{url}{own_services_path}?limit=24&reverse=False", text=json.dumps({Model._RESPONSE_KEY_LIST: [service_content]}))

            service = command.get_service(organisation, service_id)
            self.assertIsNotNone(service)

            self.assertEqual(service_name, service.name)

            self.assertEqual(3, mock.call_count)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{services_path}?limit=1&reverse=False&filter%5B{Model._FIELD_NAME}__{Model._FILTER_MODIFIER_BEGINS_WITH}%5D={service_ssd_id}",
                     text=json.dumps({Model._RESPONSE_KEY_LIST: []}))
            mock.get(f"{url}{services_path}?limit=24&reverse=False", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))
            mock.get(f"{url}{own_services_path}?limit=24&reverse=False", text=json.dumps({Model._RESPONSE_KEY_LIST: [service_content]}))

            service = command.get_service(organisation, service_ssd_id)
            self.assertIsNotNone(service)

            self.assertEqual(service_name, service.name)

            self.assertEqual(3, mock.call_count)

    def test_list_processes(self):
        """
        Test list processes.
        """
        command = Command()
        self.assertIsNotNone(command)

        url, organisation = self.__login(command)
        processes_path = Organisation._PATH_PROCESSES.format(organisation_id=organisation.id)

        with open(self.fixture_path('process.json'), 'r') as file:
            process_content = json.loads(file.read())

        process_id = process_content.get(Model._FIELD_ID)

        with open(self.fixture_path('process_execution.json'), 'r') as file:
            execution_content = json.loads(file.read())

        executions_path = Process._PATH_EXECUTIONS.format(organisation_id=organisation.id, process_id=process_id)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{processes_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))

            command.list_processes(organisation)

            self.assertEqual(1, mock.call_count)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{processes_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [process_content]}))
            mock.get(f"{url}{executions_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [execution_content]}))

            command.list_processes(organisation)

            self.assertEqual(2, mock.call_count)

        execution_content_group = execution_content.copy()
        execution_content_group[Model._FIELD_GROUP_ID] = str(uuid.uuid4())
        execution_content_group[Model._FIELD_GROUP_INDEX] = 1
        execution_content_group[Model._FIELD_GROUP_COUNT] = 2

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{processes_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [process_content]}))
            mock.get(f"{url}{executions_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [execution_content_group]}))

            command.list_processes(organisation)

            self.assertEqual(2, mock.call_count)

    def test_list_services(self):
        """
        Test list services.
        """
        command = Command()
        self.assertIsNotNone(command)

        url, organisation = self.__login(command)
        services_path = Organisation._PATH_SERVICES.format(organisation_id=organisation.id)

        with open(self.fixture_path('service.json'), 'r') as file:
            service_content = json.loads(file.read())

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{services_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))

            command.list_services(organisation)

            self.assertEqual(1, mock.call_count)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{services_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [service_content]}))

            command.list_services(organisation)

            self.assertEqual(1, mock.call_count)

    def test_list_uploads(self):
        """
        Test list uploads.
        """
        command = Command()
        self.assertIsNotNone(command)

        url, organisation = self.__login(command)
        data_path = Organisation._PATH_DATA.format(organisation_id=organisation.id)

        with open(self.fixture_path('data.json'), 'r') as file:
            data_content = json.loads(file.read())

        data_id = data_content.get(Model._FIELD_ID)

        with open(self.fixture_path('data_file.json'), 'r') as file:
            file_content = json.loads(file.read())

        files_path = Data._PATH_FILES.format(organisation_id=organisation.id, data_id=data_id)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{data_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))

            command.list_uploads(organisation)

            self.assertEqual(1, mock.call_count)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{data_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [data_content]}))
            mock.get(f"{url}{files_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))

            command.list_uploads(organisation)

            self.assertEqual(2, mock.call_count)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{data_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [data_content]}))
            mock.get(f"{url}{files_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [file_content, file_content, file_content]}))

            command.list_uploads(organisation)

            self.assertEqual(2, mock.call_count)

    def test_login(self):
        """
        Test login.
        """
        command = Command()
        self.assertIsNotNone(command)

        deployment = 'rubbish'

        match = i18n.t('command.no_such_deployment', deployment=deployment)
        match = re.escape(match)

        with pytest.raises(CommandError, match=match):
            command.login(deployment, None, None, False)

        deployment = Command._DEPLOYMENT_STAGE
        email = 'test@test.com'
        password = 'password'

        url = Command.DEPLOYMENTS[deployment][Command._DEPLOYMENT_KEY_URL]

        match = i18n.t('session.login_failed')
        match = re.escape(match)

        with patch('keyring.delete_password') as mock_delete_password:
            with patch('keyring.get_password', return_value=None) as mock_get_password:
                with patch('keyring.set_password') as mock_set_password:
                    with requests_mock.Mocker() as mock:
                        mock.post(f"{url}/users/login", text='{}')

                        with create_pipe_input() as input:
                            for _ in range(3):
                                input.send_text(f"{email}\n")
                                input.send_text(f"{password}\n")

                            with create_app_session(input=input, output=DummyOutput()):
                                with pytest.raises(RequestError, match=match):
                                    command.login(deployment, email, None, False)

                        mock_delete_password.assert_not_called()
                        mock_get_password.assert_called_once()
                        mock_set_password.assert_not_called()
                        self.assertEqual(1, mock.call_count)

        match = i18n.t('session.login_failed')
        match = re.escape(match)

        with patch('keyring.delete_password') as mock_delete_password:
            with patch('keyring.get_password', return_value=None) as mock_get_password:
                with patch('keyring.set_password') as mock_set_password:
                    with requests_mock.Mocker() as mock:
                        mock.post(f"{url}/users/login", text='{}')

                        with create_pipe_input() as input:
                            for _ in range(3):
                                input.send_text(f"{password}\n")

                            with create_app_session(input=input, output=DummyOutput()):
                                with pytest.raises(RequestError, match=match):
                                    command.login(deployment, email, None, False)

                        mock_delete_password.assert_not_called()
                        mock_get_password.assert_called_once()
                        mock_set_password.assert_not_called()
                        self.assertEqual(1, mock.call_count)

        key = b'-----BEGIN RSA PRIVATE KEY-----\nMIICXAIBAAKBgQCqGKukO1De7zhZj6+H0qtjTkVxwTCpvKe4eCZ0FPqri0cb2JZfXJ/DgYSF6vUp\nwmJG8wVQZKjeGcjDOL5UlsuusFncCzWBQ7RKNUSesmQRMSGkVb1/3j+skZ6UtW+5u09lHNsj6tQ5\n1s1SPrCBkedbNf0Tp0GbMJDyR4e9T04ZZwIDAQABAoGAFijko56+qGyN8M0RVyaRAXz++xTqHBLh\n3tx4VgMtrQ+WEgCjhoTwo23KMBAuJGSYnRmoBZM3lMfTKevIkAidPExvYCdm5dYq3XToLkkLv5L2\npIIVOFMDG+KESnAFV7l2c+cnzRMW0+b6f8mR1CJzZuxVLL6Q02fvLi55/mbSYxECQQDeAw6fiIQX\nGukBI4eMZZt4nscy2o12KyYner3VpoeE+Np2q+Z3pvAMd/aNzQ/W9WaI+NRfcxUJrmfPwIGm63il\nAkEAxCL5HQb2bQr4ByorcMWm/hEP2MZzROV73yF41hPsRC9m66KrheO9HPTJuo3/9s5p+sqGxOlF\nL0NDt4SkosjgGwJAFklyR1uZ/wPJjj611cdBcztlPdqoxssQGnh85BzCj/u3WqBpE2vjvyyvyI5k\nX6zk7S0ljKtt2jny2+00VsBerQJBAJGC1Mg5Oydo5NwD6BiROrPxGo2bpTbu/fhrT8ebHkTz2epl\nU9VQQSQzY1oZMVX8i1m5WUTLPz2yLJIBQVdXqhMCQBGoiuSoSjafUhV7i1cEGpb88h5NBYZzWXGZ\n37sJ5QsW+sJyoNde3xH8vdXhzU7eT82D6X/scw9RZz+/6rCJ4p0=\n-----END RSA PRIVATE KEY-----'
        user_id = str(uuid.uuid4())
        access_token = 'token'
        id_token = jwt.encode({'sub': user_id}, key=key, algorithm='RS256')
        body = {'access_token': access_token, 'id_token': id_token}

        with open(self.fixture_path('user.json'), 'r') as file:
            user_content = json.loads(file.read())

        user_no_organisation_content = user_content.copy()
        user_no_organisation_content['organisations'] = []

        match = i18n.t('command.no_such_organisation', organisation=None)
        match = re.escape(match)

        with patch('keyring.delete_password') as mock_delete_password:
            with patch('keyring.get_password', return_value=None) as mock_get_password:
                with patch('keyring.set_password') as mock_set_password:
                    with requests_mock.Mocker() as mock:
                        mock.post(f"{url}/users/login", text=json.dumps(body))
                        mock.get(f"{url}{User._PATH_GET.format(user_id=user_id)}", text=json.dumps({Model._RESPONSE_KEY_MODEL: user_no_organisation_content}))

                        with create_pipe_input() as input:
                            input.send_text(f"{password}\n")
                            input.send_text('\n')

                            with create_app_session(input=input, output=DummyOutput()):
                                with pytest.raises(CommandError, match=match):
                                    command.login(deployment, email, None, False)

                        mock_delete_password.assert_not_called()
                        mock_get_password.assert_called_once()
                        mock_set_password.assert_called_once()
                        self.assertEqual(2, mock.call_count)

        with open(self.fixture_path('organisation1.json'), 'r') as file:
            organisation1_content = json.loads(file.read())

        organisation1_id = organisation1_content.get('id')
        organisation1_name = organisation1_content.get(Model._FIELD_NAME)

        with open(self.fixture_path('organisation2.json'), 'r') as file:
            organisation2_content = json.loads(file.read())

        organisation2_id = organisation2_content.get(Model._FIELD_ID)
        organisation2_name = organisation2_content.get(Model._FIELD_NAME)

        with patch('keyring.delete_password') as mock_delete_password:
            with patch('keyring.get_password', return_value=None) as mock_get_password:
                with patch('keyring.set_password') as mock_set_password:
                    with requests_mock.Mocker() as mock:
                        mock.post(f"{url}/users/login", text=json.dumps(body))
                        mock.get(f"{url}{User._PATH_GET.format(user_id=user_id)}", text=json.dumps({Model._RESPONSE_KEY_MODEL: user_content}))
                        mock.get(f"{url}{Organisation._PATH_GET.format(organisation_id=organisation1_id)}",
                                 text=json.dumps({Model._RESPONSE_KEY_MODEL: organisation1_content}))
                        mock.get(f"{url}{Organisation._PATH_GET.format(organisation_id=organisation2_id)}",
                                 text=json.dumps({Model._RESPONSE_KEY_MODEL: organisation2_content}))

                        with create_pipe_input() as input:
                            input.send_text(f"{password}\n")
                            input.send_text('\n')

                            with create_app_session(input=input, output=DummyOutput()):
                                organisation, stage, region = command.login(deployment, email, None, False)
                                self.assertIsNotNone(organisation)
                                self.assertIsNotNone(stage)
                                self.assertIsNotNone(region)

                                self.assertEqual(organisation1_name, organisation.name)
                                self.assertEqual(deployment, stage)
                                self.assertEqual(Command.DEPLOYMENTS[deployment][Command._DEPLOYMENT_KEY_REGION], region)

                        mock_delete_password.assert_not_called()
                        mock_get_password.assert_called_once()
                        mock_set_password.assert_called_once()
                        self.assertEqual(5, mock.call_count)

        with patch('keyring.delete_password') as mock_delete_password:
            with patch('keyring.get_password', return_value=None) as mock_get_password:
                with patch('keyring.set_password') as mock_set_password:
                    with requests_mock.Mocker() as mock:
                        mock.post(f"{url}/users/login", text=json.dumps(body))
                        mock.get(f"{url}{User._PATH_GET.format(user_id=user_id)}", text=json.dumps({Model._RESPONSE_KEY_MODEL: user_content}))
                        mock.get(f"{url}{Organisation._PATH_GET.format(organisation_id=organisation1_id)}",
                                 text=json.dumps({Model._RESPONSE_KEY_MODEL: organisation1_content}))
                        mock.get(f"{url}{Organisation._PATH_GET.format(organisation_id=organisation2_id)}",
                                 text=json.dumps({Model._RESPONSE_KEY_MODEL: organisation2_content}))

                        with create_pipe_input() as input:
                            input.send_text(f"{password}\n")

                            with create_app_session(input=input, output=DummyOutput()):
                                organisation, stage, region = command.login(deployment, email, organisation2_name, False)
                                self.assertIsNotNone(organisation)
                                self.assertIsNotNone(stage)
                                self.assertIsNotNone(region)

                                self.assertEqual(organisation2_name, organisation.name)
                                self.assertEqual(deployment, stage)
                                self.assertEqual(Command.DEPLOYMENTS[deployment][Command._DEPLOYMENT_KEY_REGION], region)

                        mock_delete_password.assert_not_called()
                        mock_get_password.assert_called_once()
                        mock_set_password.assert_called_once()
                        self.assertEqual(4, mock.call_count)

        with patch('keyring.delete_password') as mock_delete_password:
            with patch('keyring.get_password', return_value=password) as mock_get_password:
                with patch('keyring.set_password') as mock_set_password:
                    with requests_mock.Mocker() as mock:
                        mock.post(f"{url}/users/login", text=json.dumps(body))
                        mock.get(f"{url}{User._PATH_GET.format(user_id=user_id)}", text=json.dumps({Model._RESPONSE_KEY_MODEL: user_content}))
                        mock.get(f"{url}{Organisation._PATH_GET.format(organisation_id=organisation1_id)}",
                                 text=json.dumps({Model._RESPONSE_KEY_MODEL: organisation1_content}))
                        mock.get(f"{url}{Organisation._PATH_GET.format(organisation_id=organisation2_id)}",
                                 text=json.dumps({Model._RESPONSE_KEY_MODEL: organisation2_content}))

                        organisation, stage, region = command.login(deployment, email, organisation2_name, False)
                        self.assertIsNotNone(organisation)
                        self.assertIsNotNone(stage)
                        self.assertIsNotNone(region)

                        self.assertEqual(organisation2_name, organisation.name)
                        self.assertEqual(deployment, stage)
                        self.assertEqual(Command.DEPLOYMENTS[deployment][Command._DEPLOYMENT_KEY_REGION], region)

                        mock_delete_password.assert_not_called()
                        mock_get_password.assert_called_once()
                        mock_set_password.assert_called_once()
                        self.assertEqual(4, mock.call_count)

        try:
            keyring.delete_password(Command._KEYRING_DEPLOYMENT_FORMAT.format(deployment=deployment), email)
        except PasswordDeleteError:
            pass

        with requests_mock.Mocker() as mock:
            mock.post(f"{url}/users/login", text=json.dumps(body))
            mock.get(f"{url}{User._PATH_GET.format(user_id=user_id)}", text=json.dumps({Model._RESPONSE_KEY_MODEL: user_content}))
            mock.get(f"{url}{Organisation._PATH_GET.format(organisation_id=organisation1_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: organisation1_content}))
            mock.get(f"{url}{Organisation._PATH_GET.format(organisation_id=organisation2_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: organisation2_content}))

            with create_pipe_input() as input:
                input.send_text(f"{password}\n")

                with create_app_session(input=input, output=DummyOutput()):
                    organisation, stage, region = command.login(deployment, email, organisation2_name, False)
                    self.assertIsNotNone(organisation)
                    self.assertIsNotNone(stage)
                    self.assertIsNotNone(region)

                    self.assertEqual(organisation2_name, organisation.name)
                    self.assertEqual(deployment, stage)
                    self.assertEqual(Command.DEPLOYMENTS[deployment][Command._DEPLOYMENT_KEY_REGION], region)

                    self.assertEqual(4, mock.call_count)

        self.assertEqual(password, keyring.get_password(Command._KEYRING_DEPLOYMENT_FORMAT.format(deployment=deployment), email))

        with requests_mock.Mocker() as mock:
            mock.post(f"{url}/users/login", text=json.dumps(body))
            mock.get(f"{url}{User._PATH_GET.format(user_id=user_id)}", text=json.dumps({Model._RESPONSE_KEY_MODEL: user_content}))
            mock.get(f"{url}{Organisation._PATH_GET.format(organisation_id=organisation1_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: organisation1_content}))
            mock.get(f"{url}{Organisation._PATH_GET.format(organisation_id=organisation2_id)}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: organisation2_content}))

            with create_pipe_input() as input:
                input.send_text(f"{password}\n")

                with create_app_session(input=input, output=DummyOutput()):
                    organisation, stage, region = command.login(deployment, email, organisation2_name, True)
                    self.assertIsNotNone(organisation)
                    self.assertIsNotNone(stage)
                    self.assertIsNotNone(region)

                    self.assertEqual(organisation2_name, organisation.name)
                    self.assertEqual(deployment, stage)
                    self.assertEqual(Command.DEPLOYMENTS[deployment][Command._DEPLOYMENT_KEY_REGION], region)

                    self.assertEqual(4, mock.call_count)

        self.assertIsNone(keyring.get_password(Command._KEYRING_DEPLOYMENT_FORMAT.format(deployment=deployment), email))

    def test_remove_process_and_inputs(self):
        """
        Test remove process and its inputs.
        """
        command = Command()
        self.assertIsNotNone(command)

        url, organisation = self.__login(command)
        data_path = Organisation._PATH_DATA.format(organisation_id=organisation.id)

        with open(self.fixture_path('process.json'), 'r') as file:
            process_content = json.loads(file.read())

        process = Process(organisation._session)
        process._set_model_from_response(process_content, ProcessSchema(), organisation_id=organisation.id)
        process_delete_path = Process._PATH_DELETE.format(organisation_id=organisation.id, process_id=process.id)

        with open(self.fixture_path('data.json'), 'r') as file:
            data_content = json.loads(file.read())

        data_id = data_content.get(Model._FIELD_ID)
        data_get_path = Data._PATH_GET.format(organisation_id=organisation.id, data_id=data_id)
        data_delete_path = Data._PATH_DELETE.format(organisation_id=organisation.id, data_id=data_id)

        match = i18n.t('models.model.not_persisted')
        match = re.escape(match)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{data_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [data_content]}))
            mock.get(f"{url}{data_get_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: data_content}))

            with pytest.raises(ModelError, match=match):
                command.remove_process_and_inputs(organisation, process)

            self.assertEqual(4, mock.call_count)

        process._Model__persisted = True

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{data_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [data_content]}))
            mock.get(f"{url}{data_get_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: data_content}))
            mock.delete(f"{url}{process_delete_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content}))
            mock.delete(f"{url}{data_delete_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: data_content}))

            command.remove_process_and_inputs(organisation, process)

            self.assertEqual(7, mock.call_count)

    def test_start_process(self):
        """
        Test start process.
        """
        command = Command()
        self.assertIsNotNone(command)

        url, organisation = self.__login(command)
        services_path = Organisation._PATH_SERVICES.format(organisation_id=organisation.id)
        own_services_path = Organisation._PATH_OWN_SERVICES.format(organisation_id=organisation.id)
        new_process_path = Process._PATH_NEW.format(organisation_id=organisation.id)

        with open(self.fixture_path('process_new.json'), 'r') as file:
            process_content = json.loads(file.read())

        process_name = process_content.get(Model._FIELD_NAME)

        with open(self.fixture_path('service.json'), 'r') as file:
            service_content = json.loads(file.read())

        with open(self.fixture_path('extras.json'), 'r') as file:
            extras_content = json.loads(file.read())

        service_name = service_content.get(Model._FIELD_NAME)
        input_files = []
        storage_files = []
        options = []
        dispatchers = []
        wait_for_start = False

        match = i18n.t('command.no_such_service', service=service_name)
        match = re.escape(match)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{services_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))
            mock.get(f"{url}{own_services_path}?limit=24&reverse=False", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))

            with pytest.raises(CommandError, match=match):
                command.start_process(organisation, service_name, process_name, input_files, storage_files, options, dispatchers, wait_for_start)

            self.assertEqual(3, mock.call_count)

        with patch.object(command, '_Command__provision_process') as mock_provision_process:
            with patch.object(Process, 'execute') as mock_process_execute:
                with requests_mock.Mocker() as mock:
                    mock.get(f"{url}{services_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [service_content]}))
                    mock.get(f"{url}{new_process_path}",
                             text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content, Model._RESPONSE_KEY_EXTRAS: {Model._FIELD_DISPATCHERS: extras_content}}))

                    command.start_process(organisation, service_name, process_name, input_files, storage_files, options, dispatchers, wait_for_start)

                    mock_process_execute.assert_called_once()
                    mock_provision_process.assert_called_once()

                    self.assertEqual(2, mock.call_count)

        input_files = [1]
        storage_files = [2]
        wait_for_start = True

        with patch.object(command, '_Command__provision_process') as mock_provision_process:
            with patch.object(command, '_Command__upload_or_find_inputs', return_value=[]) as mock_upload_or_find_inputs:
                with patch.object(command, '_Command__upload_storage', return_value=[]) as mock_upload_storage:
                    with patch.object(Process, 'execute') as mock_process_execute:
                        with patch.object(Process, 'wait_for_next_execution') as mock_wait_for_next_execution:
                            with requests_mock.Mocker() as mock:
                                mock.get(f"{url}{services_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [service_content]}))
                                mock.get(f"{url}{new_process_path}",
                                         text=json.dumps(
                                             {Model._RESPONSE_KEY_MODEL: process_content, Model._RESPONSE_KEY_EXTRAS: {Model._FIELD_DISPATCHERS: extras_content}}))

                                command.start_process(organisation, service_name, process_name, input_files, storage_files, options, dispatchers, wait_for_start)

                                mock_provision_process.assert_called_once()
                                mock_wait_for_next_execution.assert_called_once()
                                mock_upload_or_find_inputs.assert_called_once()
                                mock_upload_storage.assert_called_once()
                                mock_process_execute.assert_called_once()

                                self.assertEqual(2, mock.call_count)

    def test_template_service(self):
        """
        Test template service.
        """
        command = Command()
        self.assertIsNotNone(command)

        url, organisation = self.__login(command)
        services_path = Organisation._PATH_SERVICES.format(organisation_id=organisation.id)
        own_services_path = Organisation._PATH_OWN_SERVICES.format(organisation_id=organisation.id)

        with open(self.fixture_path('service.json'), 'r') as file:
            service_content = json.loads(file.read())

        service_name = service_content.get(Model._FIELD_NAME)

        with open(self.fixture_path('process_new.json'), 'r') as file:
            process_content = json.loads(file.read())

        with open(self.fixture_path('extras.json'), 'r') as file:
            extras_content = json.loads(file.read())

        new_process_path = Process._PATH_NEW.format(organisation_id=organisation.id)

        match = i18n.t('command.no_such_service', service=service_name)
        match = re.escape(match)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{services_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))
            mock.get(f"{url}{own_services_path}?limit=24&reverse=False", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))

            with pytest.raises(CommandError, match=match):
                command.template_service(organisation, service_name)

            self.assertEqual(3, mock.call_count)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{services_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [service_content]}))
            mock.get(f"{url}{new_process_path}",
                     text=json.dumps({Model._RESPONSE_KEY_MODEL: process_content, Model._RESPONSE_KEY_EXTRAS: {Model._FIELD_DISPATCHERS: extras_content}}))

            service_definition = command.template_service(organisation, service_name)
            self.assertIsNotNone(service_definition)

            self.assertEqual(service_name, service_definition[Command._YAML_SERVICE_NAME])
            self.assertTrue(service_definition[Command._YAML_PROCESS_NAME].startswith(service_name))
            self.assertEqual(len(process_content[Model._FIELD_INPUTS]), len(service_definition[Command._YAML_INPUTS]))
            self.assertEqual(len(process_content[Model._FIELD_OPTIONS]) + 7, len(service_definition[Command._YAML_OPTIONS]))  # With standard options.
            self.assertEqual(len(extras_content), len(service_definition[Command._YAML_DISPATCHERS]))

            self.assertEqual(2, mock.call_count)

    def test_upload(self):
        """
        Test delete upload.
        """
        command = Command()
        self.assertIsNotNone(command)

        url, organisation = self.__login(command)
        new_path = Data._PATH_NEW.format(organisation_id=organisation.id)
        create_path = Data._PATH_CREATE.format(organisation_id=organisation.id)

        with open(self.fixture_path('data.json'), 'r') as file:
            data_content = json.loads(file.read())

        data_id = data_content.get(Model._FIELD_ID)
        add_file_path = Data._PATH_ADD_FILE.format(organisation_id=organisation.id, data_id=data_id)
        files_path = Data._PATH_FILES.format(organisation_id=organisation.id, data_id=data_id)

        with open(self.fixture_path('data_file.json'), 'r') as file:
            file_content = json.loads(file.read())

        upload_file_url = 'https://upload.com/test'
        add_file_content1 = {Model._RESPONSE_KEY_EXTRAS: {Data._RESPONSE_KEY_FILE: str(uuid.uuid4()), Data._RESPONSE_KEY_URL: upload_file_url}}
        add_file_content2 = {Model._RESPONSE_KEY_EXTRAS: {Data._RESPONSE_KEY_FILE: str(uuid.uuid4()), Data._RESPONSE_KEY_URL: upload_file_url}}

        upload_name = 'Upload'
        file_type = 'rubbish'
        files = []

        match = i18n.t('command.unknown_file_type', file_type=file_type)
        match = re.escape(match)

        with pytest.raises(CommandError, match=match):
            command.upload(organisation, upload_name, file_type, files)

        file_type = fusion_platform.FILE_TYPE_OTHER

        match = i18n.t('command.no_upload_files')
        match = re.escape(match)

        with pytest.raises(CommandError, match=match):
            command.upload(organisation, upload_name, file_type, files)

        files = ['/path/to/file']

        match = i18n.t('command.missing_file', file=files[0])
        match = re.escape(match)

        with pytest.raises(CommandError, match=match):
            command.upload(organisation, upload_name, file_type, files)

        file_type = fusion_platform.FILE_TYPE_GEOTIFF

        files = [self.fixture_path('data.json'), self.fixture_path('data_file.json')]

        match = i18n.t('command.invalid_file_extension', file=files[0], extension='.json', file_type=file_type)
        match = re.escape(match)

        with pytest.raises(CommandError, match=match):
            command.upload(organisation, upload_name, file_type, files)

        file_type = fusion_platform.FILE_TYPE_GEOJSON

        with patch('os.path.getsize', return_value=123) as mock_getsize:
            with patch('os.path.exists', return_value=True) as mock_exists:
                with patch('builtins.open', mock_open(read_data='_' * 1024)) as mock_upload_file:
                    with requests_mock.Mocker() as mock:
                        mock.get(f"{url}{new_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: data_content}))
                        mock.post(f"{url}{create_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: data_content}))
                        mock.post(f"{url}{add_file_path}", [
                            {'text': json.dumps(add_file_content1), 'status_code': 200},
                            {'text': json.dumps(add_file_content2), 'status_code': 200}
                        ])
                        mock.put(upload_file_url, status_code=200)
                        mock.get(f"{url}{files_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [file_content]}))

                        command.upload(organisation, upload_name, file_type, files)

                        self.assertEqual(7, mock.call_count)
                        mock_getsize.assert_called()
                        self.assertEqual(len(files), mock_getsize.call_count)
                        mock_exists.assert_called()
                        self.assertEqual(2 * len(files), sum([1 for call in mock_exists.call_args_list if
                                                              (len(call.args) == 1) and (call.args[0].startswith(self.fixture_path('')))]))
                        mock_upload_file.assert_called()
                        self.assertEqual(len(files), sum([1 for call in mock_upload_file.call_args_list if
                                                          (len(call.args) == 2) and (call.args[0].startswith(self.fixture_path('')))]))

    def test_upload_or_find_inputs(self):
        """
        Test upload or find inputs.
        """
        command = Command()
        self.assertIsNotNone(command)

        url, organisation = self.__login(command)
        data_path = Organisation._PATH_DATA.format(organisation_id=organisation.id)
        new_path = Data._PATH_NEW.format(organisation_id=organisation.id)
        create_path = Data._PATH_CREATE.format(organisation_id=organisation.id)

        with open(self.fixture_path('data.json'), 'r') as file:
            data_content = json.loads(file.read())

        data_id = data_content.get(Model._FIELD_ID)
        add_file_path = Data._PATH_ADD_FILE.format(organisation_id=organisation.id, data_id=data_id)
        files_path = Data._PATH_FILES.format(organisation_id=organisation.id, data_id=data_id)

        with open(self.fixture_path('data_file.json'), 'r') as file:
            file_content = json.loads(file.read())

        upload_file_url = 'https://upload.com/test'
        add_file_content = {Model._RESPONSE_KEY_EXTRAS: {Data._RESPONSE_KEY_FILE: str(uuid.uuid4()), Data._RESPONSE_KEY_URL: upload_file_url}}

        process_name = 'Test'
        input_files = []
        file_types = None

        data_items = command._Command__upload_or_find_inputs(organisation, process_name, input_files, file_types)
        self.assertIsNotNone(data_items)
        self.assertEqual([], data_items)

        file_path = os.path.join('/', 'path', 'to')
        input_files = [
            'Input',
            {Model._FIELD_NAME: 'Input', Model._FIELD_FILE: os.path.join(file_path, 'file.tif')},
            os.path.join(file_path, 'file.tif'),
            os.path.join(file_path, 'file.tiff'),
            os.path.join(file_path, 'file.jp2'),
            os.path.join(file_path, 'file.dem'),
            os.path.join(file_path, 'file.json'),
            os.path.join(file_path, 'file.geojson'),
            os.path.join(file_path, 'file.kml'),
            os.path.join(file_path, 'file.kmz'),
            os.path.join(file_path, 'file.csv'),
            os.path.join(file_path, 'file.zip'),
            os.path.join(file_path, 'file.jpeg'),
            os.path.join(file_path, 'file.jpg'),
            os.path.join(file_path, 'file.png'),
            os.path.join(file_path, 'file.pdf')
        ]

        match = i18n.t('command.no_such_input', input_name=input_files[0])
        match = re.escape(match)

        with requests_mock.Mocker() as mock:
            mock.get(f"{url}{data_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: []}))

            with pytest.raises(CommandError, match=match):
                command._Command__upload_or_find_inputs(organisation, process_name, input_files, file_types)

            self.assertEqual(1, mock.call_count)

        file_types = [
            'Input',
            fusion_platform.FILE_TYPE_GEOTIFF,
            fusion_platform.FILE_TYPE_GEOTIFF,
            fusion_platform.FILE_TYPE_GEOTIFF,
            fusion_platform.FILE_TYPE_JPEG2000,
            fusion_platform.FILE_TYPE_DEM,
            fusion_platform.FILE_TYPE_GEOJSON,
            fusion_platform.FILE_TYPE_GEOJSON,
            fusion_platform.FILE_TYPE_KML,
            fusion_platform.FILE_TYPE_KMZ,
            fusion_platform.FILE_TYPE_CSV,
            fusion_platform.FILE_TYPE_ESRI_SHAPEFILE,
            fusion_platform.FILE_TYPE_JPEG,
            fusion_platform.FILE_TYPE_JPEG,
            fusion_platform.FILE_TYPE_PNG,
            fusion_platform.FILE_TYPE_PDF
        ]

        with patch('os.path.getsize', return_value=123) as mock_getsize:
            with patch('os.path.exists', return_value=True) as mock_exists:
                with patch('builtins.open', mock_open(read_data='_' * 1024)) as mock_upload_file:
                    with requests_mock.Mocker() as mock:
                        mock.get(f"{url}{data_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [data_content]}))
                        mock.get(f"{url}{new_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: data_content}))
                        mock.post(f"{url}{create_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: data_content}))
                        mock.post(f"{url}{add_file_path}", text=json.dumps(add_file_content))
                        mock.put(upload_file_url, status_code=200)
                        mock.get(f"{url}{files_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [file_content]}))

                        data_items = command._Command__upload_or_find_inputs(organisation, process_name, input_files, file_types)
                        self.assertIsNotNone(data_items)
                        self.assertEqual(len(input_files), len(data_items))

                        self.assertEqual(76, mock.call_count)
                        mock_getsize.assert_called()
                        self.assertEqual(len(input_files) - 1, mock_getsize.call_count)  # We find 1.
                        mock_exists.assert_called()
                        self.assertEqual(len(input_files) - 1, sum([1 for call in mock_exists.call_args_list if
                                                                    (len(call.args) == 1) and (call.args[0].startswith(file_path))]))  # We find 1.
                        mock_upload_file.assert_called()
                        self.assertEqual(len(input_files) - 1, sum([1 for call in mock_upload_file.call_args_list if
                                                                    (len(call.args) == 2) and (call.args[0].startswith(file_path))]))  # We find 1.

    def test_upload_storage(self):
        """
        Test upload or find inputs.
        """
        command = Command()
        self.assertIsNotNone(command)

        url, organisation = self.__login(command)
        new_path = Data._PATH_NEW.format(organisation_id=organisation.id)
        create_path = Data._PATH_CREATE.format(organisation_id=organisation.id)

        with open(self.fixture_path('data.json'), 'r') as file:
            data_content = json.loads(file.read())

        data_id = data_content.get(Model._FIELD_ID)
        add_file_path = Data._PATH_ADD_FILE.format(organisation_id=organisation.id, data_id=data_id)
        files_path = Data._PATH_FILES.format(organisation_id=organisation.id, data_id=data_id)

        with open(self.fixture_path('data_file.json'), 'r') as file:
            file_content = json.loads(file.read())

        upload_file_url = 'https://upload.com/test'
        add_file_content = {Model._RESPONSE_KEY_EXTRAS: {Data._RESPONSE_KEY_FILE: str(uuid.uuid4()), Data._RESPONSE_KEY_URL: upload_file_url}}

        with open(self.fixture_path('process.json'), 'r') as file:
            process_content = json.loads(file.read())

        process = Process(organisation._session)
        process._set_model_from_response(process_content, ProcessSchema(), organisation_id=organisation.id)

        storage_files = {}

        command._Command__upload_storage(organisation, storage_files, process)

        file_path = os.path.join('/', 'path', 'to')
        storage_files = {
            f"{1}_{2}_{uuid.uuid4()}_{1}": os.path.join(file_path, Command._STORAGE_NAME),
            f"{1}_{2}_{uuid.uuid4()}_{2}": os.path.join(file_path, Command._STORAGE_NAME),
            f"{1}_{2}_{uuid.uuid4()}_{3}": os.path.join(file_path, Command._STORAGE_NAME)
        }

        with patch('os.remove') as mock_remove:
            with patch('os.path.getsize', return_value=123) as mock_getsize:
                with patch('os.path.exists', return_value=True) as mock_exists:
                    with patch('shutil.copy') as mock_shutil_copy:
                        with patch('builtins.open', mock_open(read_data='_' * 1024)) as mock_upload_file:
                            with requests_mock.Mocker() as mock:
                                mock.get(f"{url}{new_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: data_content}))
                                mock.post(f"{url}{create_path}", text=json.dumps({Model._RESPONSE_KEY_MODEL: data_content}))
                                mock.post(f"{url}{add_file_path}", text=json.dumps(add_file_content))
                                mock.put(upload_file_url, status_code=200)
                                mock.get(f"{url}{files_path}", text=json.dumps({Model._RESPONSE_KEY_LIST: [file_content]}))

                                command._Command__upload_storage(organisation, storage_files, process)

                                self.assertEqual(15, mock.call_count)

                                self.assertEqual(15, mock.call_count)
                                mock_remove.assert_called()
                                self.assertEqual(len(storage_files), mock_remove.call_count)
                                mock_getsize.assert_called()
                                self.assertEqual(len(storage_files), mock_getsize.call_count)
                                mock_exists.assert_called()
                                self.assertEqual(len(storage_files) * 2, sum([1 for call in mock_exists.call_args_list if
                                                                              (len(call.args) == 1) and (
                                                                                  call.args[0].endswith(Command._STORAGE_NAME))]))  # 2 calls to exists.
                                mock_shutil_copy.assert_called()
                                self.assertEqual(len(storage_files), sum([1 for call in mock_shutil_copy.call_args_list if
                                                                          (len(call.args) == 2) and (call.args[0].endswith(Command._STORAGE_NAME))]))
                                mock_upload_file.assert_called()
                                self.assertEqual(len(storage_files), sum([1 for call in mock_upload_file.call_args_list if
                                                                          (len(call.args) == 2) and (call.args[0].endswith(Command._STORAGE_NAME))]))
