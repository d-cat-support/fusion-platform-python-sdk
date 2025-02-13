"""
Data model class file.

author: Matthew Casey

&copy; [Digital Content Analysis Technology Ltd](https://www.d-cat.co.uk)
"""

import i18n
from marshmallow import Schema, EXCLUDE
import os
from time import sleep

from fusion_platform.common.raise_thread import RaiseThread
from fusion_platform.common.utilities import dict_nested_get
from fusion_platform.models import fields
from fusion_platform.models.data_file import DataFile
from fusion_platform.models.model import Model, ModelError
from fusion_platform.session import Session


# Define the model schema classes. These are maintained from the API definitions.

class DataSchema(Schema):
    """
    Schema class for data model.

    Each data has the following fields (and nested fields):

    .. include::data.md
    """
    id = fields.UUID(required=True, metadata={'read_only': True})  # Changed to prevent this being updated.

    created_at = fields.DateTime(required=True, metadata={'read_only': True})  # Changed to prevent this being updated.
    updated_at = fields.DateTime(required=True, metadata={'read_only': True})  # Changed to prevent this being updated.

    organisation_id = fields.UUID(required=True, metadata={'read_only': True})  # Changed to prevent this being updated.
    name = fields.String(required=True)

    # Removed lock.
    unlinked = fields.String(allow_none=True, metadata={'read_only': True})  # Changed to prevent this being updated.
    unfulfilled = fields.Boolean(allow_none=True, metadata={'read_only': True})  # Changed to prevent this being updated.

    bounds = fields.List(fields.Decimal(required=True), allow_none=True, metadata={'read_only': True})  # Changed to prevent this being updated.
    file_with_preview = fields.UUID(allow_none=True, metadata={'read_only': True})  # Changed to prevent this being updated.

    # Removed uploaded.
    uploaded_organisation_id = fields.UUID(allow_none=True, metadata={'read_only': True})  # Changed to prevent this being updated.
    deletable = fields.String(allow_none=True, metadata={'read_only': True})  # Changed to prevent this being updated.

    # Removed creator.

    # Removed search.

    class Meta:
        """
        When loading an object, make sure we exclude any unknown fields, rather than raising an exception, and put fields in their definition order.
        """
        unknown = EXCLUDE
        ordered = True


class Data(Model):
    """
    Data model class providing attributes and methods to manipulate data item details.
    """

    # Override the schema.
    _SCHEMA = DataSchema()

    # Override the base model class name.
    _BASE_MODEL_CLASS_NAME = 'Organisation'  # A string to prevent circular imports.

    # Base path.
    _PATH_ROOT = '/organisations/{organisation_id}/data'
    _PATH_BASE = f"{_PATH_ROOT}/{{data_id}}"

    # Override the standard model paths.
    _PATH_COPY = f"{_PATH_BASE}/copy"
    _PATH_CREATE = _PATH_ROOT
    _PATH_DELETE = _PATH_BASE
    _PATH_GET = _PATH_BASE
    _PATH_NEW = f"{_PATH_ROOT}/new"
    _PATH_PATCH = _PATH_BASE

    # Add in the custom model paths.
    _PATH_ADD_FILE = f"{_PATH_BASE}/add_file"
    _PATH_FILES = f"{_PATH_BASE}/files"

    # Response keys.
    _RESPONSE_KEY_FILE = 'file'

    def __init__(self, session):
        """
        Initialises the object.

        Args:
            session: The linked session object for interfacing with the Fusion Platform<sup>&reg;</sup>.
        """
        super(Data, self).__init__(session)

        # Initialise the fields.
        self.__upload_progress = {}
        self.__upload_threads = {}

    def __add_file(self, file_type, file):
        """
        Attempts to add a file to the data object and then starts its upload. The file is uploaded using a thread.

        Args:
            file_type: The type of file to add.
            file: The path to the file to add.

        Raises:
            RequestError: if the add fails.
        """
        # Make sure the file exists.
        if not os.path.exists(file):
            raise ModelError(i18n.t('models.data.failed_add_missing_file', file=file))

        # Add the file to the data model.
        body = {self.__class__.__name__: {'name': os.path.basename(file), 'file_type': file_type}}
        response = self._session.request(path=self._get_path(self.__class__._PATH_ADD_FILE), method=Session.METHOD_POST, body=body)

        # Assume that the file id is held within the expected key within the resulting dictionary.
        file_id = dict_nested_get(response, [self.__class__._RESPONSE_KEY_EXTRAS, self.__class__._RESPONSE_KEY_FILE])

        if file_id is None:
            raise ModelError(i18n.t('models.data.failed_add_file_id'))

        # Assume that the URL held within the expected key within the resulting dictionary.
        url = dict_nested_get(response, [self.__class__._RESPONSE_KEY_EXTRAS, self.__class__._RESPONSE_KEY_URL])

        if url is None:
            raise ModelError(i18n.t('models.data.failed_add_file_url'))

        # Make sure the file is unique so that we can keep track of it.
        if file_id in self.__upload_threads:
            raise ModelError(i18n.t('models.data.failed_add_file_not_unique'))

        # Create and start a thread for the upload.
        self.__upload_progress[file] = (file, 0)  # Indexed by file path, not file id.
        thread = None

        try:
            thread = RaiseThread(target=self._session.upload_file, args=(url, file, self.__upload_callback))
            thread.start()

        finally:
            # Make sure we record the thread so we can monitor it, even if it fails.
            self.__upload_threads[file_id] = thread

    def check_analysis_complete(self, wait=False):
        """
        Checks that the analysis of all files associated with this data object is complete. Optionally waits for the analysis to complete.

        Args:
            wait: Optionally wait for the analysis to complete? Default False.

        Returns:
            True if the analysis is complete for all files.

        Raises:
            RequestError: if any get fails.
            ModelError: if a model could not be loaded or validated from the Fusion Platform<sup>&reg;</sup>.
        """
        while True:
            complete = True

            # Load in each of the file models and check that every file has been uploaded, and has a publishable or error field to indicate that the analysis is
            # complete.
            for file in self.files:
                self._logger.debug('file %s: %s', file.file_name, file.attributes)

                has_fields = hasattr(file, self.__class__._FIELD_SIZE) and (
                        hasattr(file, self.__class__._FIELD_PUBLISHABLE) or hasattr(file, self.__class__._FIELD_ERROR))

                if not has_fields:
                    self._logger.debug('file %s not yet analysed', file.file_name)
                    complete = False
                    break

            # Break the loop if we are not waiting or are complete.
            if (not wait) or complete:
                break

            # We are waiting, so block for a short while.
            sleep(self.__class__._API_UPDATE_WAIT_PERIOD)

        return complete

    def copy(self, name):
        """
        Creates a data object as a copy of the current object for the same organisation and with the same files. The copy is treated as if it has been uploaded,
        even if the source data object was created by the platform and not uploaded.

        Args:
            name: The name of the copy.

        Returns:
            The created copy.

        Raises:
            RequestError: if the copy fails.
            ModelError: if the model could not be created and validated by the Fusion Platform<sup>&reg;</sup>.
        """
        # Copy the data model.
        body = {self.__class__.__name__: {'name': name}}
        response = self._session.request(path=self._get_path(self.__class__._PATH_COPY), method=Session.METHOD_POST, body=body)

        # Assume that the copy data id is held within the expected key within the resulting dictionary.
        copy_data_id = dict_nested_get(response, [self.__class__._RESPONSE_KEY_MODEL, self.__class__._FIELD_ID])

        if copy_data_id is None:
            raise ModelError(i18n.t('models.data.failed_copy_id'))

        # Return the copy.
        return self.__class__._model_from_api_id(self._session, organisation_id=self.organisation_id, id=copy_data_id)

    def _create(self, name, file_type, files, wait=False, **kwargs):
        """
        Attempts to create the model object with the given values. This assumes the model template has been loaded first using the _new method, and that the model
        is then created using a POST RESTful request. This assumes that the post body contains key names which include the name of the model class.

        This method is overridden to also upload the corresponding files and optionally wait for the upload and analysis to complete.

        Args:
            name: The name of the data object.
            file_type: The type of files that the data object will hold.
            files: The list of file paths to be uploaded.
            wait: Optionally wait for the upload and analysis to complete? Default False.
            kwargs: The model attributes which override those already in the template.

        Returns:
            The created data object.

        Raises:
            RequestError: if the create fails.
            ModelError: if the model could not be created and validated by the Fusion Platform<sup>&reg;</sup>.
        """
        # Use the super method to create the data item with the correct attributes. This will raise an exception if anything fails.
        super(Data, self)._create(name=name, **kwargs)

        # Add each of the files, assuming that each is of the same file type, and start its upload in a thread.
        try:
            for file in files:
                self.__add_file(file_type, file)

        finally:
            # Optionally wait for completion. We must complete this even if an exception has occurred because there may be multiple files. However, we only do this
            # if any threads were started.
            if len(self.__upload_threads) > 0:
                self.create_complete(wait=wait)  # Ignore response.

    def create_complete(self, wait=False):
        """
        Checks whether the data object file(s) upload and analysis have completed. If an error has occurred during the upload and analysis, then this will raise
        a corresponding exception. Optionally waits for the upload and analysis to complete.

        Note, a failure of one file upload will not stop the upload of other files. Therefore, if an exception is raised, further calls to this method are required
        until all upload and analysis (or errored) has completed and this method returns True.

        Args:
            wait: Optionally wait for the upload and analysis to complete? Default False.

        Returns:
            True if the upload and analysis are complete for all files.

        Raises:
            RequestError: if any request fails.
            ModelError: if the upload or analysis failed.
        """
        # Make sure a create is in progress.
        if len(self.__upload_threads) <= 0:
            raise ModelError(i18n.t('models.data.no_create'))

        # Check the upload threads. This will raise an exception if an error has occurred.
        first_error = None

        for file_id, thread in self.__upload_threads.items():
            if thread is not None:
                thread_finished = False

                try:
                    # Join will return immediately because of the timeout, but will raise an exception if something has gone wrong.
                    thread.join(timeout=None if wait else 0)

                    # Check if the thread is still running after the join.
                    thread_finished = not thread.is_alive()

                except Exception as e:
                    # Something went wrong. Make sure we mark the upload as finished.
                    thread_finished = True

                    # If we are waiting for everything to complete, then we must not re-raise the error here so that everything else can be completed first.
                    # Instead, we save the error off and raise it later.
                    if wait:
                        first_error = e if first_error is None else first_error
                    else:
                        raise

                finally:
                    # Make sure we clear the thread if it has finished.
                    if thread_finished:
                        self.__upload_threads[file_id] = None

        # Have all the uploads finished?
        uploads_finished = all([value is None for value in self.__upload_threads.values()])

        # Now check whether the analysis has completed. We do this in a loop so that we can wait until completion, but break out if we are not waiting. If an
        # error occurs, then we assume that the analysis is complete to prevent indefinitely waiting.
        complete = False

        try:
            if uploads_finished:
                complete = self.check_analysis_complete(wait=wait)

        except Exception as e:
            # An error occurred, make sure we treat this as complete to prevent an indefinite loop.
            complete = True

            # If we already have an error to raise, make sure we do not overwrite it.
            first_error = e if first_error is None else first_error

        finally:
            if complete:
                # Tidy up any finished threads. This will allow us to indicate that everything is complete.
                self.__upload_threads = {file_id: thread for file_id, thread in self.__upload_threads.items() if thread is not None}

        # If we encountered an error, make sure we raise it.
        if first_error is not None:
            raise first_error

        return len(self.__upload_threads) <= 0

    @property
    def files(self):
        """
        Provides an iterator through the data object's files.

        Returns:
            An iterator through the data object's files.

        Raises:
            RequestError: if any get fails.
            ModelError: if a model could not be loaded or validated from the Fusion Platform<sup>&reg;</sup>.
        """
        return DataFile._models_from_api_path(self._session, self._get_path(self.__class__._PATH_FILES), organisation_id=self.organisation_id)

    def get_stac_collection(self, items, collection_file_name=DataFile._STAC_COLLECTION_FILE_NAME, owner=None, created_at=None, detail=None):
        """
        Converts the data representation into a STAC collection with the specified STAC item file names.

        Args:
            items: The list of items to be put into the collection. This should be a tuple of (STAC item, item_file_name).
            collection_file_name: The optional collection file name.
            owner: The optional owner of the collection. Default None.
            created_at: Optionally when the collection was created. Default None.
            detail: The optional collection detail as a dictionary. Default None.

        Returns:
            A tuple of the STAC collection definition as a dictionary and the collection file name used in the definition.
        """
        stac_extensions = []

        # Form the providers.
        provider = {
            'name': i18n.t('fusion_platform.organisation'),
            'roles': ['producer', 'licensor'],
            'url': i18n.t('fusion_platform.url')
        }

        # Add in the optional processing information, if any.
        if owner is not None:
            provider['processing:lineage'] = owner

        if created_at is not None:
            provider['processing.datetime'] = created_at

        if detail is not None:
            provider['processing:software'] = detail

        if (owner is not None) or (created_at is not None) or (detail is not None):
            stac_extensions.append('https://stac-extensions.github.io/processing/v1.2.0/schema.json')

        # Form the links.
        links = [
            {'rel': 'self', 'href': collection_file_name, 'type': 'application/json'},
            {'rel': 'root', 'href': collection_file_name, 'type': 'application/json'},
        ]

        # Add in the files calculating the maximal spatial and temporal extents.
        bbox = None
        interval_start = None
        interval_end = None

        for item, item_file_name in items:
            # So that we can extract things correctly, turn any mapping proxy into a dict (and relevant sub-mapping proxies).
            item = dict(item)

            if item.get('properties') is not None:
                item['properties'] = dict(item.get('properties'))

            # Calculate the spatial extent.
            item_bbox = item.get('bbox')

            if (bbox is None) or (len(bbox) < 4):
                bbox = item_bbox

            if (bbox is not None) and (len(bbox) >= 4) and (item_bbox is not None) and (len(item_bbox) >= 4):
                bbox = [min(bbox[0], item_bbox[0]), min(bbox[1], item_bbox[1]), max(bbox[2], item_bbox[2]), max(bbox[3], item_bbox[3])]

            # Calculate the temporal extent.
            item_datetime = dict_nested_get(item, ['properties', 'datetime'])
            interval_start = item_datetime if interval_start is None else min(interval_start, item_datetime)
            interval_end = item_datetime if interval_end is None else max(interval_end, item_datetime)

            # Add in the link.
            links.append({'rel': 'item', 'href': item_file_name, 'type': 'application/geo+json'})

        # Build the STAC collection.
        return {
            'type': 'Collection',
            'stac_version': '1.0.0',
            'stac_extensions': stac_extensions,
            'id': self.id,
            'description': self.name,
            'license': 'proprietary',
            'providers': [provider],
            'extent': {'spatial': {'bbox': [bbox]}, 'temporal': {'interval': [[interval_start, interval_end]]}},
            'links': links
        }, collection_file_name

    def __upload_callback(self, url, source, size):
        """
        Callback method used to receive progress from upload. Updates the upload progress.

        Args:
            url: The URL to upload as a file.
            source: The source file path.
            size: The total size in bytes so far uploaded.
        """
        self.__upload_progress[source] = (source, size)

    def upload_progress(self):
        """
        Returns current upload progress.

        Returns:
            A list of tuples of the source and total number of bytes uploaded so far.

        Raises:
            ModelError: if no upload is in progress.
        """
        # Make sure at least one upload is in progress.
        if (self.__upload_threads is None) or (len(self.__upload_threads) == 0):
            raise ModelError(i18n.t('models.data.no_upload'))

        return list(self.__upload_progress.values())
