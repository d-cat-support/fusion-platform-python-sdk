"""
Session class file.

author: Matthew Casey

&copy; [Digital Content Analysis Technology Ltd](https://www.d-cat.co.uk)
"""

import i18n
import json
import jwt
import logging
import os
import requests
from tenacity import before_sleep_log, retry, retry_if_exception_type, stop_after_attempt, wait_random_exponential
from tqdm.utils import CallbackIOWrapper

import fusion_platform
from fusion_platform.base import Base
from fusion_platform.common.utilities import json_default


class SessionError(Exception):
    """
    Base exception raised on request failure.
    """
    pass


class RequestError(SessionError):
    """
    Exception raised on request failure.
    """
    pass


class RetryableRequestError(RequestError):
    """
    Exception raised on request failure which is retryable.
    """
    pass


class ValueError(SessionError):
    """
    Exception raised on login failure.
    """
    pass


class UploadCallback:
    """
    Provides a callback mechanism for uploads using the CallbackIOWrapper.
    """

    def __init__(self, url, source, callback):
        """
        Initialises the object.

        Args:
            url: The URL being uploaded to.
            source: The source file path.
            callback: The callback method used to receive upload progress.
        """
        self.__url = url
        self.__source = source
        self.__callback = callback
        self.__upload_size = 0

    def callback(self, size):
        """
        Receives the upload callback every time data is read from the associated file.

        Args:
            size: The number of bytes which have been read from the associated file.
        """
        self.__upload_size += size
        self.__callback(self.__url, self.__source, self.__upload_size)


class Session(Base):
    """
    Provides a session for use in interfacing with the Fusion Platform<sup>&reg;</sup> API.
    """

    # HTTP methods.
    METHOD_DELETE = 'DELETE'
    METHOD_GET = 'GET'
    METHOD_POST = 'POST'
    METHOD_PATCH = 'PATCH'
    METHOD_PUT = 'PUT'

    # Default Fusion Platform<sup>&reg;</sup> API endpoint.
    API_URL_DEFAULT = 'https://api.thefusionplatform.com'

    # Mask keys.
    _MASK_KEYS = ['password', 'old_password', 'new_password', 'access_token', 'id_token', 'refresh_token']

    # Download temporary file name extension.
    DOWNLOAD_EXTENSION = '.download'

    def __init__(self):
        """
        Initialises the object.
        """
        super(Session, self).__init__()

        # Initialise the private fields.
        self.__user_id = None
        self.__bearer_token = None
        self.__api_url = Session.API_URL_DEFAULT

    def download_file(self, url, destination, callback=None):
        """
        Downloads a file to the destination path. The destination directories are created if they do not exist. The optional callback function receives three
        arguments which are the URL, destination and the number of bytes downloaded so far.

        Args:
            url: The URL to download as a file.
            destination: The destination file path.
            callback: The optional callback method used to receive download progress.
        """
        # Make sure the destination directory exists.
        directory = os.path.dirname(destination.strip())

        if len(directory) > 0:
            os.makedirs(directory, exist_ok=True)

        try:
            # Download the file in chunks to a temporarily named file.
            self._logger.info('downloading %s -> %s', url, destination)
            response = requests.get(url, stream=True)

            # Raise any errors.
            if not response:
                raise RequestError(i18n.t('session.request_failed', message=response))

            # Download the content to file as a series of chunks.
            temporary_destination = f"{destination}{Session.DOWNLOAD_EXTENSION}"
            download_size = 0

            with open(temporary_destination, 'wb') as file:
                for chunk in response.iter_content(chunk_size=1024 * 1024 * 10):
                    file.write(chunk)
                    download_size += len(chunk)
                    self._logger.debug('downloaded %d bytes', download_size)

                    if callback is not None:
                        callback(url, destination, download_size)

            # Rename the downloaded file.
            if os.path.exists(temporary_destination):
                os.rename(temporary_destination, destination)

            self._logger.info('downloaded %s', destination)

        except RequestError:
            raise

        except Exception as e:
            message = str(e)
            message = e.__class__.__name__ if (e is None) or (len(str(e).strip()) <= 0) else message
            raise RequestError(i18n.t('session.request_failed', message=message)) from e

    def __filter_nested_dictionary(self, dictionary):
        """
        Recursively filters a nested dictionary to mask out any keys which should be masked.

        Args:
            dictionary: The nested dictionary to mask.

        Returns:
            The masked nested dictionary.
        """
        if (dictionary is not None) and isinstance(dictionary, dict):
            return {key: '*****' if key in Session._MASK_KEYS else self.__filter_nested_dictionary(value) for key, value in dictionary.items()}
        else:
            return dictionary

    def login(self, email=None, user_id=None, password=None, api_url=None):
        """
        Attempts to log into the Fusion Platform<sup>&reg;</sup> to return a user model for the active session.

        Args:
        email: The user account email address. Either an email address or a user id must be provided.
        user_id: The user account user id. Either an email address or a user id must be provided.
        password: The password for the user account.
        api_url: The optional custom API URL to use. Defaults to the production Fusion Platform<sup>&reg;</sup>.

        Returns:
            The corresponding user id on successful login.

        Raises:
            ValueError: on incorrect parameters.
            RequestError: on login failure.
        """
        # Make sure we have all the required parameters.
        if (email is None) and (user_id is None):
            raise ValueError(i18n.t('session.missing_email_user_id'))

        if password is None:
            raise ValueError(i18n.t('session.missing_password'))

        # Set any custom API URL.
        if api_url is not None:
            self.__api_url = api_url

        # Login.
        self._logger.debug('logging in...')
        body = {'User': {'email': email, 'user_id': user_id, 'password': password}}
        response = self.request(path='/users/login', method=Session.METHOD_POST, body=body)

        id_token = response.get('id_token')

        if id_token is not None:
            self.__user_id = jwt.decode(id_token, options={'verify_signature': False}).get('sub')

        self.__bearer_token = response.get('access_token')

        if (self.__user_id is None) or (self.__bearer_token is None):
            raise RequestError(i18n.t('session.login_failed'))

        self._logger.debug('logged in')

    @retry(wait=wait_random_exponential(multiplier=1, min=1, max=5), stop=stop_after_attempt(10), reraise=True,
           retry=retry_if_exception_type(RetryableRequestError),
           before_sleep=before_sleep_log(logging.getLogger(fusion_platform.FUSION_PLATFORM_LOGGER), logging.INFO))
    def request(self, path='/', query_parameters=None, method=METHOD_GET, body=None):
        """
        Sends a request to the Fusion Platform<sup>&reg;</sup> using the specified path, method and JSON payload. This method will use the authentication bearer token, if
        available.

        Args:
            path: The optional path. Default '/'.
            query_parameters: The optional query parameters as a dictionary.
            method: The optional RESTful method type. Default GET.
            body: The optional body. Default None.

        Returns:
            The decoded response body.

        Raises:
            RequestError: if the request failed.
        """
        payload = None

        # Optionally add the bearer token.
        headers = {'Content-Type': 'application/json'}

        if self.__bearer_token is not None:
            headers['Authorization'] = f"Bearer {self.__bearer_token}"

        try:
            # Issue the request.
            self._logger.info('request %s: %s%s(%s) -> %s', method, self.__api_url, path, query_parameters, self.__filter_nested_dictionary(body))
            json_body = json.dumps(body, default=json_default) if body is not None else None
            with requests.request(method, f"{self.__api_url}{path}", params=query_parameters, data=json_body, headers=headers) as response:
                self._logger.debug('response headers: %s', response.headers)

                # Raise any errors.
                if not response:
                    message = str(response.status_code)

                    try:
                        message = response.json().get('error_message')
                        self._logger.error(message)
                    except:
                        pass  # Ignore the inability to extract the error message.

                    raise RequestError(i18n.t('session.request_failed', message=message))

                payload = response.json()
                self._logger.debug('response: %s', self.__filter_nested_dictionary(payload))

        except RequestError:  # Suggests a fatal error which cannot be retried.
            raise

        except (requests.ConnectionError, requests.Timeout) as e:  # Suggests an intermittent error which can be retried.
            message = str(e)
            message = e.__class__.__name__ if (e is None) or (len(str(e).strip()) <= 0) else message
            raise RetryableRequestError(i18n.t('session.request_failed', message=message)) from e

        except Exception as e:  # Suggests a fatal error which cannot be retried.
            message = str(e)
            message = e.__class__.__name__ if (e is None) or (len(str(e).strip()) <= 0) else message
            raise RequestError(i18n.t('session.request_failed', message=message)) from e

        # Return the payload.
        return payload

    def upload_file(self, url, source, callback=None):
        """
        Uploads a file from the source path.

        Args:
            url: The URL to download as a file.
            source: The source file path.
            callback: The optional callback method used to receive upload progress.
        """
        try:
            # Upload the file as a data stream.
            self._logger.info('uploading %s -> %s', url, source)

            with open(source, 'rb') as file:
                # Wrap the file reader with a callback to give progress.
                file = CallbackIOWrapper(UploadCallback(url, source, callback).callback, file, 'read') if callback is not None else file
                response = requests.put(url, data=file)

                # Raise any errors.
                if not response:
                    raise RequestError(i18n.t('session.request_failed', message=response))

            self._logger.info('uploaded %s', source)

        except RequestError:
            raise

        except Exception as e:
            message = str(e)
            message = e.__class__.__name__ if (e is None) or (len(str(e).strip()) <= 0) else message
            raise RequestError(i18n.t('session.request_failed', message=message)) from e

    @property
    def user_id(self):
        """
        Returns:
            The user id.
        """
        return self.__user_id
