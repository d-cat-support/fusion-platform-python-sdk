"""
Data file model class file.

author: Matthew Casey

&copy; [Digital Content Analysis Technology Ltd](https://www.d-cat.co.uk)
"""

import i18n
from marshmallow import Schema, EXCLUDE
import os

import fusion_platform
from fusion_platform.common.raise_thread import RaiseThread
from fusion_platform.common.utilities import datetime_parse, dict_nested_get
from fusion_platform.models import fields
from fusion_platform.models.model import Model, ModelError


# Define the model schema classes. These are maintained from the API definitions.

class DataFileSelectorSchema(Schema):
    """
    Nested schema class for selector, category, data type, unit, format and statistics.
    """
    selector = fields.String(required=True)
    category = fields.String(allow_none=True)
    data_type = fields.String(allow_none=True)
    unit = fields.String(allow_none=True)
    validation = fields.String(allow_none=True)

    area = fields.Decimal(allow_none=True)
    length = fields.Decimal(allow_none=True)
    points = fields.Integer(allow_none=True)

    initial_values = fields.List(fields.String(required=True), allow_none=True)
    minimum = fields.Decimal(allow_none=True)
    maximum = fields.Decimal(allow_none=True)
    mean = fields.Decimal(allow_none=True)
    sd = fields.Decimal(allow_none=True)

    histogram_minimum = fields.Decimal(allow_none=True)
    histogram_maximum = fields.Decimal(allow_none=True)
    histogram = fields.List(fields.Decimal(required=True), allow_none=True)

    class Meta:
        """
        When loading an object, make sure we exclude any unknown fields, rather than raising an exception, and put fields in their definition order.
        """
        unknown = EXCLUDE
        ordered = True


class DataFileSchema(Schema):
    """
    Schema class for data file model.

    Each data file model has the following fields (and nested fields):

    .. include::data_file.md
    """
    id = fields.UUID(required=True, metadata={'read_only': True})  # Changed to prevent this being updated.

    created_at = fields.DateTime(required=True, metadata={'read_only': True})  # Changed to prevent this being updated.
    updated_at = fields.DateTime(required=True, metadata={'read_only': True})  # Changed to prevent this being updated.

    organisation_id = fields.UUID(allow_none=True, metadata={'read_only': True, 'title': i18n.t('models.data_file.organisation_id.title'), 'description': i18n.t(
        'models.data_file.organisation_id.description')})  # Added parameter so that it can be used.
    data_id = fields.UUID(required=True, metadata={'read_only': True})  # Changed to prevent this being updated.
    # Removed organisation_id_file_type.

    file_id = fields.UUID(required=True, metadata={'read_only': True})  # Changed to prevent this being updated.
    preview_file_id = fields.UUID(allow_none=True, metadata={'read_only': True})  # Changed to prevent this being updated.
    file_type = fields.String(required=True, metadata={'read_only': True})  # Changed to prevent this being updated.
    file_name = fields.String(allow_none=True, metadata={'read_only': True})  # Changed to prevent this being updated.

    resolution = fields.Integer(allow_none=True, metadata={'read_only': True})  # Changed to prevent this being updated.
    crs = fields.String(allow_none=True, metadata={'read_only': True})  # Changed to prevent this being updated.
    bounds = fields.List(fields.Decimal(required=True), allow_none=True, metadata={'read_only': True})  # Changed to prevent this being updated.
    area = fields.Decimal(allow_none=True, metadata={'read_only': True})  # Changed to prevent this being updated.
    length = fields.Decimal(allow_none=True, metadata={'read_only': True})  # Changed to prevent this being updated.
    points = fields.Integer(allow_none=True, metadata={'read_only': True})  # Changed to prevent this being updated.

    size = fields.Integer(allow_none=True, metadata={'read_only': True})  # Changed to prevent this being updated.
    error = fields.Boolean(allow_none=True, metadata={'read_only': True})  # Changed to prevent this being updated.
    publishable = fields.Boolean(allow_none=True, metadata={'read_only': True})  # Changed to prevent this being updated.

    alternative = fields.UUID(allow_none=True, metadata={'read_only': True})  # Changed to prevent this being updated.
    source = fields.UUID(allow_none=True, metadata={'read_only': True})  # Changed to prevent this being updated.

    selectors = fields.List(fields.Nested(DataFileSelectorSchema()), allow_none=True, metadata={'read_only': True})  # Changed to prevent this being updated.

    downloads = fields.Integer(allow_none=True, metadata={'read_only': True})  # Changed to prevent this being updated.
    geojson = fields.String(allow_none=True, metadata={'read_only': True})  # Changed to prevent this being updated.

    title = fields.String(allow_none=True, metadata={'read_only': True})  # Changed to prevent this being updated.
    description = fields.String(allow_none=True, metadata={'read_only': True})  # Changed to prevent this being updated.

    class Meta:
        """
        When loading an object, make sure we exclude any unknown fields, rather than raising an exception, and put fields in their definition order.
        """
        unknown = EXCLUDE
        ordered = True


class DataFile(Model):
    """
    DataFile model class providing attributes and methods to manipulate data file details.
    """

    # Override the schema.
    _SCHEMA = DataFileSchema()

    # Override the base model class name.
    _BASE_MODEL_CLASS_NAME = 'Data'  # A string to prevent circular imports.

    # No standard model paths as data file objects cannot be retrieved directly from the API.

    # Add in the custom model paths.
    _PATH_DOWNLOAD_FILE = '/organisations/{organisation_id}/data/{data_id}/download_file/{file_id}'

    # Plus query parameters.
    _QUERY_PREVIEW = 'preview'

    # Geospatial file types.
    _GEOSPATIAL_RASTER = 'raster'
    _GEOSPATIAL_VECTOR = 'vector'

    # File type information - a tuple of typical extension and whether the file type is a geospatial vector, raster or not.
    # @formatter:off
    _FILE_TYPES = {
        fusion_platform.FILE_TYPE_GEOTIFF: ('tif', _GEOSPATIAL_RASTER),
        fusion_platform.FILE_TYPE_JPEG2000: ('jpeg', _GEOSPATIAL_RASTER),
        fusion_platform.FILE_TYPE_DEM: ('dem', _GEOSPATIAL_RASTER),
        fusion_platform.FILE_TYPE_GEOJSON: ('json', _GEOSPATIAL_VECTOR),
        fusion_platform.FILE_TYPE_KML: ('kml', _GEOSPATIAL_VECTOR),
        fusion_platform.FILE_TYPE_KMZ: ('kmz', _GEOSPATIAL_VECTOR),
        fusion_platform.FILE_TYPE_CSV: ('csv', None),
        fusion_platform.FILE_TYPE_ESRI_SHAPEFILE: ('zip', _GEOSPATIAL_VECTOR),
        fusion_platform.FILE_TYPE_JPEG: ('jpg', None),
        fusion_platform.FILE_TYPE_PNG: ('png', None),
        fusion_platform.FILE_TYPE_PDF: ('pdf', None),
        fusion_platform.FILE_TYPE_GZIP: ('gz', None),
        fusion_platform.FILE_TYPE_ZIP: ('zip', None),
        fusion_platform.FILE_TYPE_OTHER: ('*', None),
    }
    # @formatter:on

    # STAC file name constants. We do not use ".json" because this is used by services and specific file types. Similarly, the name starts with "." to hide it.
    _STAC_COLLECTION_FILE_NAME = '.collection.stac'
    _STAC_ITEM_FILE_NAME_FORMAT = '.{file_name}.stac'

    def __init__(self, session):
        """
        Initialises the object.

        Args:
            session: The linked session object for interfacing with the Fusion Platform<sup>&reg;</sup>.
        """
        super(DataFile, self).__init__(session)

        # Initialise the fields.
        self.__download_progress = None
        self.__download_thread = None

    def download(self, path, preview=False, wait=False):
        """
        Downloads the file to the specified path. Optionally waits for the download to complete.

        Args:
            path: The local path to download the file to.
            preview: Optionally specify that the preview (PNG) of the file should be downloaded instead of the main file.
            wait: Optionally wait for the download to complete? Default False.

        Raises:
            RequestError: if the download fails.
        """
        # Make sure no download is currently in progress.
        if self.__download_thread is not None:
            raise ModelError(i18n.t('models.data_file.download_already_in_progress'))

        # Obtain the download URL.
        url = self.download_url(preview=preview)

        # Start the download in a separate thread.
        self.__download_progress = (url, path, 0)
        self.__download_thread = RaiseThread(target=self._session.download_file, args=(url, path, self.__download_callback))
        self.__download_thread.start()

        # Optionally wait for completion.
        self.download_complete(wait=wait)  # Ignore response.

    def __download_callback(self, url, destination, size):
        """
        Callback method used to receive progress from download. Updates the download progress.

        Args:
            url: The URL to download as a file.
            destination: The destination file path.
            size: The total size in bytes so far downloaded.
        """
        self.__download_progress = (url, destination, size)

    def download_complete(self, wait=False):
        """
        Checks whether the download has completed. If an error has occurred during the download, then this will raise a corresponding exception. Optionally waits
        for the download to complete.

        Args:
            wait: Optionally wait for the download to complete? Default False.

        Returns:
            True if the download is complete.

        Raises:
            RequestError: if any request fails.
            ModelError: if no download is in progress.
        """
        # Make sure a download is in progress.
        if self.__download_thread is None:
            raise ModelError(i18n.t('models.data_file.no_download'))

        # Check the download thread. This will raise an exception if an error has occurred.
        finished = False

        try:
            # Join will return immediately because of the timeout, but will raise an exception if something has gone wrong.
            self.__download_thread.join(timeout=None if wait else 0)

            # Check if the thread is still running after the join.
            finished = not self.__download_thread.is_alive()

        except:
            # Something went wrong. Make sure we mark the download as finished and re-raise the error.
            finished = True
            raise

        finally:
            # Make sure we clear the progress and thread if it has finished.
            if finished:
                self.__download_progress = None
                self.__download_thread = None

        return finished

    def download_progress(self):
        """
        Returns current download progress.

        Returns:
            A tuple of the URL, destination and total number of bytes downloaded so far.

        Raises:
            ModelError: if no download is in progress.
        """
        # Make sure a download is in progress.
        if self.__download_thread is None:
            raise ModelError(i18n.t('models.data_file.no_download'))

        return self.__download_progress

    def download_url(self, preview=False):
        """
        Obtains a URL which can be used to download the file. This URL is only valid for up to 1 hour.

        Args:
            preview: Optionally specify that the preview (PNG) URL for the file should be obtained instead of the URL for the main file.

        Raises:
            RequestError: if the request fails.
        """
        response = self._session.request(path=self._get_path(self.__class__._PATH_DOWNLOAD_FILE, file_id=self.file_id, organisation_id=self.organisation_id),
                                         query_parameters={DataFile._QUERY_PREVIEW: preview})

        # Assume that the URL held within the expected key within the resulting dictionary.
        url = dict_nested_get(response, [self.__class__._RESPONSE_KEY_EXTRAS, self.__class__._RESPONSE_KEY_URL])

        if url is None:
            raise ModelError(i18n.t('models.data_file.failed_download_url'))

        return url

    def get_stac_item(self, item_file_name_format=_STAC_ITEM_FILE_NAME_FORMAT, collection_file_name=_STAC_COLLECTION_FILE_NAME):
        """
        Converts the data file representation into a STAC item.

        Args:
            item_file_name_format: The optional item file name format string, where the "file_name" placeholder is replaced with the item's file name.
            collection_file_name: The optional owning collection file name.

        Returns:
            A tuple of the STAC item definition as a dictionary and the item file name used in the definition.
        """

        # Obtain all the relevant information.
        bounds = self.bounds if hasattr(self, Model._FIELD_BOUNDS) else None
        crs = self.crs if hasattr(self, Model._FIELD_CRS) else None
        file_name = self.file_name if hasattr(self, Model._FIELD_FILE_NAME) else None
        size = self.size if hasattr(self, Model._FIELD_SIZE) else None

        # Attempt to find the file type to get its extension and geospatial type. Default to "Other" if not found.
        found_file_type = DataFile._FILE_TYPES.get(self.file_type)

        if found_file_type is None:
            found_file_type = DataFile._FILE_TYPES.get(fusion_platform.FILE_TYPE_OTHER)

        geospatial = found_file_type[1]

        # Get the file extension.
        extension = os.path.splitext(file_name)[1] if file_name is not None else None
        extension = found_file_type[0] if extension is None else extension

        if (extension is None) or (extension == '*'):
            extension = ''
        else:
            extension = f".{extension}" if not extension.startswith('.') else extension

        # Work out a suitable name for the file if one is not available.
        if file_name is None:
            file_name = f"{self.id}{extension}"

        item_file_name = item_file_name_format.format(file_name=file_name)

        # Start to build the STAC extensions list.
        stac_extensions = ['https://stac-extensions.github.io/processing/v1.2.0/schema.json']  # For properties#processing.[software,version].

        # Get the bounding box and geometry, if there is one.
        bbox = []
        geometry = {}

        if (bounds is not None) and (len(bounds) >= 4):
            bbox = bounds
            geometry = {'type': 'Polygon', 'coordinates': [[[bbox[0], bbox[1]], [bbox[2], bbox[1]], [bbox[2], bbox[3]], [bbox[0], bbox[3]], [bbox[0], bbox[1]]]]}

        # Get the datetime from the filename, if possible. We try various iterations of sections the file name until we find something.
        for file_part in file_name.split('_'):
            extracted_datetime = datetime_parse(file_part) or datetime_parse(f"{file_part}T00:00:00Z")  # Assume UTC.

            if extracted_datetime is not None:
                break

        if extracted_datetime is None:
            extracted_datetime = self.created_at

        # Start to build the properties.
        properties = {'processing.software': i18n.t('fusion_platform.sdk'), 'processing.version': fusion_platform.__version__, 'datetime': extracted_datetime}

        # Add in the CRS, if there is one.
        if crs is not None:
            properties['proj:epsg'] = crs
            stac_extensions.append('https://stac-extensions.github.io/projection/v1.1.0/schema.json')  # For properties#proj:epsg.

        # Build the links.
        links = [{'rel': 'self', 'href': item_file_name, 'type': 'application/json'}]

        # Add in the optional owning collection.
        if collection_file_name is not None:
            links.append({'rel': 'root', 'href': collection_file_name, 'type': 'application/json'})
            links.append({'rel': 'parent', 'href': collection_file_name, 'type': 'application/json'})

        # Start to build the asset from the associated file.
        asset = {'href': file_name, 'roles': []}

        # Extract out the relevant values depending upon the file type.
        raster_bands = None
        eo_bands = None

        if (geospatial == DataFile._GEOSPATIAL_RASTER) and hasattr(self, Model._FIELD_SELECTORS) and (self.selectors is not None):
            for selector in self.selectors:
                raster_band = {}
                eo_band = {}

                if hasattr(self, Model._FIELD_RESOLUTION):
                    raster_band['spatial_resolution'] = self.resolution

                if selector.get(Model._FIELD_UNIT) is not None:
                    raster_band['unit'] = selector.get(Model._FIELD_UNIT)

                if (selector.get(Model._FIELD_MINIMUM) is not None) and (selector.get(Model._FIELD_MAXIMUM) is not None) and (
                        selector.get(Model._FIELD_MEAN) is not None) and (selector.get(Model._FIELD_SD) is not None):
                    raster_band['statistics'] = {
                        'minimum': selector.get(Model._FIELD_MINIMUM),
                        'maximum': selector.get(Model._FIELD_MAXIMUM),
                        'mean': selector.get(Model._FIELD_MEAN),
                        'stddev': selector.get(Model._FIELD_SD)
                    }

                if (selector.get(Model._FIELD_HISTOGRAM_MINIMUM) is not None) and (selector.get(Model._FIELD_HISTOGRAM_MAXIMUM) is not None) and (
                        selector.get(Model._FIELD_HISTOGRAM) is not None):
                    raster_band['histogram'] = {
                        'count': len(selector.get(Model._FIELD_HISTOGRAM)),
                        'min': selector.get(Model._FIELD_HISTOGRAM_MINIMUM),
                        'max': selector.get(Model._FIELD_HISTOGRAM_MAXIMUM),
                        'buckets': selector.get(Model._FIELD_HISTOGRAM),
                    }

                if selector.get(Model._FIELD_CATEGORY) is not None:
                    eo_band['name'] = selector.get(Model._FIELD_CATEGORY)

                raster_bands = [raster_band] if raster_bands is None else [raster_band] + raster_bands
                eo_bands = [eo_band] if eo_bands is None else [eo_band] + eo_bands

            stac_extensions.append('https://stac-extensions.github.io/eo/v1.1.0/schema.json')  # For assets#eo:bands.
            stac_extensions.append('https://stac-extensions.github.io/raster/v1.1.0/schema.json')  # For assets#raster:bands.

        if raster_bands is not None:
            asset['raster:bands'] = raster_bands
            asset['eo:bands'] = eo_bands

        # Add in the file size, if there is one.
        if size is not None:
            asset['file:size'] = size
            stac_extensions.append('https://stac-extensions.github.io/file/v2.1.0/schema.json')  # For assets#file:size.

        # Build the STAC item.
        return {
            'type': 'Feature',
            'stac_version': '1.0.0',
            'stac_extensions': stac_extensions,
            'id': self.id,
            'bbox': bbox,
            'geometry': geometry,
            'properties': properties,
            'links': links,
            'assets': {'asset': asset}
        }, item_file_name
