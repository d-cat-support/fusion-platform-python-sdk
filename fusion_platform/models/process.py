"""
Process model class file.

author: Matthew Casey

&copy; [Digital Content Analysis Technology Ltd](https://www.d-cat.co.uk)
"""

from datetime import datetime, timedelta, timezone
from functools import partial
import i18n
from marshmallow import Schema, EXCLUDE
from time import sleep

import fusion_platform
from fusion_platform.common.utilities import value_from_read_only
from fusion_platform.models import fields
from fusion_platform.models.data import Data
from fusion_platform.models.model import Model, ModelError
from fusion_platform.models.process_execution import ProcessExecution
from fusion_platform.session import Session


# Define a schema class used to coerce option values. See Option#__coerce_value.

class OptionDataTypeSchema(Schema):
    """
    Defines a Marshmallow schema which can be used to coerce any option value into its underlying Python data type.
    """

    # List out all the allowed field types using their corresponding data type names.
    numeric = fields.Float(allow_none=True)
    currency = fields.Decimal(allow_none=True)
    boolean = fields.Boolean(allow_none=True)
    datetime = fields.DateTime(allow_none=True)
    string = fields.String(allow_none=True)
    constrained = fields.String(allow_none=True)


# Define a model class for an option which overrides the representation to display more relevant information.

class Option(Model):
    """
    Model option class.
    """

    # Validation parsing for constrained values.
    _VALIDATION_DELIMITER = ';'
    _VALIDATION_EQUALS = '='
    _VALIDATION_FORMAT = 'format'
    _VALIDATION_ITEM_DELIMITER = ','
    _VALIDATION_NAMES = 'names'
    _VALIDATION_VALUES = 'values'

    @classmethod
    def __coerce_value(cls, value, data_type):
        """
        Attempts to coerce a value into its corresponding data type.

        Args:
            value: The value to coerce.
            data_type: The required data type.

        Returns:
            The coerced value of the correct data type.
        """
        # Deal with None values.
        if (value is None) or (value == str(None)) or (value == 'null'):
            return None
        else:
            # Use the option schema to attempt to load the value using its data type as a name.
            model = OptionDataTypeSchema().load({data_type: value})
            return model.get(data_type)

    @classmethod
    def __extract_constrained_validation(cls, validation):
        """
        Extracts the constrained values from a constrained option validation.

        Args:
            validation: The constrained option validation.

        Returns:
            A tuple (constrained_names, constrained_values) of the extracted elements or (None, None) if the constrained values cannot be extracted.
        """
        # Extract the elements.
        elements = validation.split(Option._VALIDATION_DELIMITER)
        constrained_names = None
        constrained_values = None

        if len(elements) <= 2:
            for element in elements:
                values = element.split(Option._VALIDATION_EQUALS)

                if len(values) > 0:
                    lhs = values[0].lower()
                    rhs = Option._VALIDATION_EQUALS.join(values[1:])

                    try:
                        if lhs == Option._VALIDATION_VALUES:
                            constrained_values = rhs.split(Option._VALIDATION_ITEM_DELIMITER)

                        if lhs == Option._VALIDATION_NAMES:
                            constrained_names = rhs.split(Option._VALIDATION_ITEM_DELIMITER)
                    except:
                        pass  # Cannot be parsed.

        return constrained_names, constrained_values

    @classmethod
    def __extract_datetime_validation(cls, validation):
        """
        Extracts the datetime format from a datatime option validation.

        Args:
            validation: The datatime option validation.

        Returns:
            The datetime format, or None if it cannot be extracted.
        """
        # Extract the elements.
        elements = validation.split(Option._VALIDATION_DELIMITER)
        format = None

        if len(elements) <= 3:
            for element in elements:
                values = element.split(Option._VALIDATION_EQUALS)

                if len(values) > 0:
                    lhs = values[0].lower()
                    rhs = Option._VALIDATION_EQUALS.join(values[1:])

                    try:
                        if lhs == Option._VALIDATION_FORMAT:
                            format = rhs
                    except:
                        pass  # Cannot be parsed.

        return format

    @classmethod
    def get_option_value(cls, option, value, coerce_value):
        """
        Checks the supplied value for an option, coercing it if needed, and returns the value that can to into the model.

        Args:
            option: The option object for the option to set.
            value: The value for the option.
            coerce_value: Coerce the supplied value to be the correct type?

        Raises:
            ModelError: if the value has a different type to the option.

        Returns:
            The correct string representation of the option.
        """
        # Check that the option has the same data type as the value.
        data_type = option.get(cls._FIELD_DATA_TYPE)
        existing_value = cls.__coerce_value(option[cls._FIELD_VALUE], data_type)

        # Optionally coerce the supplied value, now that we know its data type.
        if coerce_value:
            value = cls.__coerce_value(value, data_type)

        class_matches = isinstance(value, existing_value.__class__)

        # Supplied ints can be used for floats.
        if isinstance(value, int) and isinstance(existing_value, float):
            class_matches = True

        if (value is not None) and (existing_value is not None) and (not class_matches):
            raise ModelError(i18n.t('models.process.option_wrong_type', type=existing_value.__class__))

        validation = option.get(cls._FIELD_VALIDATION)

        return cls.__value_to_option(value, data_type, validation)

    @classmethod
    def options_iterator(cls, options):
        """
        Provides an iterator through a list of options.

        Returns:
            An iterator through the options.
        """
        for option in options:
            # We first have to remove the mapping proxy so that we can wrap the dictionary in a model.
            option = value_from_read_only(option)

            # If the option is a constrained data type, then add in the constrained names and values from the validation.
            if option.get(cls._FIELD_DATA_TYPE) == fusion_platform.DATA_TYPE_CONSTRAINED:
                option[cls._FIELD_CONSTRAINED_NAMES], option[cls._FIELD_CONSTRAINED_VALUES] = cls.__extract_constrained_validation(
                    option.get(cls._FIELD_VALIDATION, ''))

            # Coerce the value to be of the correct data type.
            option[cls._FIELD_VALUE] = cls.__coerce_value(option.get(cls._FIELD_VALUE), option.get(cls._FIELD_DATA_TYPE))

            # Encapsulate the dictionary within a model (which does not talk to the API).
            model = Option(None, schema=ProcessOptionSchema())
            model._set_model(option)

            yield model

    @classmethod
    def __value_to_option(cls, value, data_type, validation):
        """
        Converts a Python option value into a string depending upon its data type and validation parameters.

        Args:
            value: The value to convert.
            data_type: The option data type.
            validation: The optional validation for the option.

        Returns:
            The correct string representation of the option.
        """
        if value is None:
            return None
        elif isinstance(value, bool):
            return str(value).lower()
        if data_type == fusion_platform.DATA_TYPE_DATETIME:
            return datetime.strftime(value, cls.__extract_datetime_validation(validation))
        else:
            return str(value)

    def __repr__(self):
        """
        Returns:
            A string representation of the object.
        """
        constrained_values = i18n.t('models.process.option.representation_constrained_values',
                                    constrained_values=self.constrained_values) if self.data_type == fusion_platform.DATA_TYPE_CONSTRAINED else ''
        required = i18n.t('models.process.option.representation_required') if self.required else ''

        return i18n.t('models.process.option.representation', title=self.title, name=self.name, data_type=self.data_type, constrained_values=constrained_values,
                      required=required, value=self.value, description=self.description)


# Define a model class for an input which overrides the representation to display more relevant information.

class Input(Model):
    """
    Model input class.
    """

    def __repr__(self):
        """
        Returns:
            A string representation of the object.
        """
        name = i18n.t('models.process.input.representation_name', name=self.name) if hasattr(self, self.__class__._FIELD_NAME) else ''
        id = i18n.t('models.process.input.representation_id', id=self.id) if hasattr(self, self.__class__._FIELD_ID) else ''

        return i18n.t('models.process.input.representation', title=self.title, file_type=self.file_type, name=name, id=id, description=self.description)


# Define a model class for a dispatcher which overrides the representation to display more relevant information.

class Dispatcher(Model):
    """
    Model dispatcher class.
    """

    @property
    def options(self):
        """
        Provides an iterator through the dispatcher's options.

        Returns:
            An iterator through the options.
        """
        return Option.options_iterator(self._model.get(self.__class__._FIELD_OPTIONS, []))

    def __repr__(self):
        """
        Returns:
            A string representation of the object.
        """
        dispatch_intermediate = self.dispatch_intermediate if hasattr(self, self.__class__._FIELD_DISPATCH_INTERMEDIATE) else False

        return i18n.t('models.process.dispatcher.representation', name=self.name, ssd_id=self.ssd_id, dispatch_intermediate=dispatch_intermediate,
                      documentation_summary=self.documentation_summary)


# Define the model schema classes. These are maintained from the API definitions.

class ProcessChainOptionSchema(Schema):
    """
    Nested schema class for SSD chain option.
    """
    name = fields.String(required=True)
    value = fields.String(allow_none=True)
    data_type = fields.String(required=True)
    validation = fields.String(allow_none=True)

    class Meta:
        """
        When loading an object, make sure we exclude any unknown fields, rather than raising an exception, and put fields in their definition order.
        """
        unknown = EXCLUDE
        ordered = True


class ProcessChainSchema(Schema):
    """
    Nested schema class for SSD chain.
    """
    ssd_id = fields.UUID(required=True)
    service_id = fields.UUID(required=True)
    inputs = fields.List(fields.UUID(allow_none=True), allow_none=True)
    outputs = fields.List(fields.UUID(required=True), allow_none=True)
    options = fields.List(fields.Nested(ProcessChainOptionSchema()), allow_none=True)
    intermediate = fields.Boolean(allow_none=True)

    class Meta:
        """
        When loading an object, make sure we exclude any unknown fields, rather than raising an exception, and put fields in their definition order.
        """
        unknown = EXCLUDE
        ordered = True


class ProcessExecutionStatusSchema(Schema):
    """
    Nested schema class for execution status.
    """
    process_execution_id = fields.UUID(required=True)
    group_id = fields.UUID(allow_none=True)
    group_index = fields.Integer(allow_none=True)
    group_count = fields.Integer(allow_none=True)
    job_status = fields.String(required=True)
    abort_reason = fields.String(allow_none=True)
    exit_type = fields.String(allow_none=True)
    started_at = fields.DateTime(required=True)
    ended_at = fields.DateTime(allow_none=True)
    delete_warning_status = fields.String(required=True)
    delete_expiry = fields.DateTime(required=True)
    notified = fields.Boolean(allow_none=True)

    class Meta:
        """
        When loading an object, make sure we exclude any unknown fields, rather than raising an exception, and put fields in their definition order.
        """
        unknown = EXCLUDE
        ordered = True


class ProcessSelectorSchema(Schema):
    """
    Nested schema class for selector, category, data type, unit and format.
    """
    selector = fields.String(required=True)
    category = fields.String(required=True)
    data_type = fields.String(required=True)
    unit = fields.String(allow_none=True)
    validation = fields.String(allow_none=True)

    class Meta:
        """
        When loading an object, make sure we exclude any unknown fields, rather than raising an exception, and put fields in their definition order.
        """
        unknown = EXCLUDE
        ordered = True


class ProcessInputSchema(Schema):
    """
    Nested schema class for the processes inputs.
    """
    ssd_id = fields.UUID(required=True)
    input = fields.Integer(required=True)
    file_type = fields.String(required=True)
    resolution = fields.Integer(allow_none=True)
    selectors = fields.List(fields.Nested(ProcessSelectorSchema()), allow_none=True)
    id = fields.UUID(required=True)
    model = fields.String(required=True)
    change_trigger = fields.Boolean(required=True)
    change_hash = fields.String(allow_none=True)
    title = fields.String(allow_none=True)
    description = fields.String(allow_none=True)

    name = fields.String(allow_none=True)  # Changed to add this field for displaying the input name.

    class Meta:
        """
        When loading an object, make sure we exclude any unknown fields, rather than raising an exception, and put fields in their definition order.
        """
        unknown = EXCLUDE
        ordered = True


class ProcessOptionSchema(Schema):
    """
    Nested schema class for options which are provided to the SSD images when run.
    """
    ssd_id = fields.UUID(required=True)
    name = fields.String(required=True)
    value = fields.String(allow_none=True)
    required = fields.Boolean(required=True)
    data_type = fields.String(required=True)
    validation = fields.String(allow_none=True)
    mutually_exclusive = fields.String(allow_none=True)
    advanced = fields.Boolean(allow_none=True)
    title = fields.String(allow_none=True)
    description = fields.String(allow_none=True)

    constrained_names = fields.List(fields.String(required=True), allow_none=True, metadata={'title': i18n.t('models.process.option.constrained_names.title'),
                                                                                             'description': i18n.t(
                                                                                                 'models.process.option.constrained_names.description')})  # Added this field to gold extracted data.
    constrained_values = fields.List(fields.String(required=True), allow_none=True, metadata={'title': i18n.t('models.process.option.constrained_values.title'),
                                                                                              'description': i18n.t(
                                                                                                  'models.process.option.constrained_values.description')})  # Added this field to gold extracted data.

    class Meta:
        """
        When loading an object, make sure we exclude any unknown fields, rather than raising an exception, and put fields in their definition order.
        """
        unknown = EXCLUDE
        ordered = True


class ProcessDispatcherSchema(Schema):
    """
    Nested schema class for dispatchers.
    """
    ssd_id = fields.UUID(required=True)
    name = fields.String(required=True)
    dispatch_intermediate = fields.Boolean(allow_none=True)
    documentation_summary = fields.String(allow_none=True)
    documentation_description = fields.String(allow_none=True)
    options = fields.List(fields.Nested(ProcessOptionSchema()), allow_none=True, metadata={'hide': True})  # Changed to hide as an attribute.

    class Meta:
        """
        When loading an object, make sure we exclude any unknown fields, rather than raising an exception, and put fields in their definition order.
        """
        unknown = EXCLUDE
        ordered = True


class ProcessSchema(Schema):
    """
    Schema class for process model.

    Each process model has the following fields (and nested fields):

    .. include::process.md
    """
    id = fields.UUID(required=True, metadata={'read_only': True})  # Changed to prevent this being updated.

    created_at = fields.DateTime(required=True, metadata={'read_only': True})  # Changed to prevent this being updated.
    updated_at = fields.DateTime(required=True, metadata={'read_only': True})  # Changed to prevent this being updated.

    organisation_id = fields.UUID(required=True, metadata={'read_only': True})  # Changed to prevent this being updated.
    ssd_id = fields.UUID(required=True, metadata={'read_only': True})  # Changed to prevent this being updated.
    service_id = fields.UUID(required=True, metadata={'read_only': True})  # Changed to prevent this being updated.
    name = fields.String(required=True)

    inputs = fields.List(fields.Nested(ProcessInputSchema()), allow_none=True, metadata={'hide': True})  # Changed to hide as an attribute.
    options = fields.List(fields.Nested(ProcessOptionSchema()), allow_none=True, metadata={'hide': True})  # Changed to hide as an attribute.
    chains = fields.List(fields.Nested(ProcessChainSchema()), allow_none=True, metadata={'read_only': True})  # Changed to prevent this being updated.

    # Removed maximum_bounds.

    run_type = fields.String(required=True)
    repeat_count = fields.Integer(required=True)
    repeat_start = fields.DateTime(required=True)
    repeat_end = fields.DateTime(allow_none=True)
    repeat_gap = fields.RelativeDelta(allow_none=True)
    repeat_offset = fields.TimeDelta(allow_none=True)

    process_status = fields.String(required=True, metadata={'read_only': True})  # Changed to prevent this being updated.
    process_status_at = fields.DateTime(required=True, metadata={'read_only': True})  # Changed to prevent this being updated.
    process_status_changed_by = fields.UUID(allow_none=True, metadata={'read_only': True})  # Changed to prevent this being updated.

    output_storage_period = fields.Integer(allow_none=True)
    test_run = fields.Boolean(required=True, metadata={'read_only': True})  # Changed to prevent this being updated.

    dispatchers = fields.List(fields.Nested(ProcessDispatcherSchema()), allow_none=True, metadata={'hide': True})  # Changed to hide as an attribute.

    # Removed prices.
    price = fields.Decimal(required=True, metadata={'read_only': True})  # Changed to prevent this being updated.

    deletable = fields.String(allow_none=True, metadata={'read_only': True})  # Changed to prevent this being updated.
    has_executions = fields.String(required=True, metadata={'hide': True})  # Changed to hide as an attribute.
    has_executions_organisation_id = fields.String(required=True, metadata={'hide': True})  # Changed to hide as an attribute.
    executions = fields.List(fields.Nested(ProcessExecutionStatusSchema()), allow_none=True, metadata={'hide': True})  # Changed to hide as an attribute.
    non_aggregator_count = fields.Integer(allow_none=True, metadata={'read_only': True})  # Changed to prevent this being updated.
    aggregator_count = fields.Integer(allow_none=True, metadata={'read_only': True})  # Changed to prevent this being updated.
    # Removed creator.

    # Removed search.

    available_dispatchers = fields.List(fields.Nested(ProcessDispatcherSchema()), allow_none=True, metadata={'hide': True})  # Added pseudo-field.

    class Meta:
        """
        When loading an object, make sure we exclude any unknown fields, rather than raising an exception, and put fields in their definition order.
        """
        unknown = EXCLUDE
        ordered = True


class Process(Model):
    """
    Process model class providing attributes and methods to manipulate process item details.
    """

    # Override the schema.
    _SCHEMA = ProcessSchema()

    # Override the base model class name.
    _BASE_MODEL_CLASS_NAME = 'Organisation'  # A string to prevent circular imports.

    # Base path.
    _PATH_ROOT = '/organisations/{organisation_id}/processes'
    _PATH_BASE = f"{_PATH_ROOT}/{{process_id}}"

    # Override the standard model paths.
    _PATH_COPY = f"{_PATH_BASE}/copy"
    _PATH_CREATE = _PATH_ROOT
    _PATH_DELETE = _PATH_BASE
    _PATH_GET = _PATH_BASE
    _PATH_NEW = f"{_PATH_ROOT}/new"
    _PATH_PATCH = _PATH_BASE

    # Add in the custom model paths.
    _PATH_EXECUTE = f"{_PATH_BASE}/execute"
    _PATH_EXECUTIONS = f"{_PATH_BASE}/executions"
    _PATH_STOP = f"{_PATH_BASE}/stop"

    # Define the expected model and list extras.
    _EXTRAS_MODEL = [(Model._FIELD_DISPATCHERS, Model._FIELD_AVAILABLE_DISPATCHERS)]
    _EXTRAS_LIST = [(Model._FIELD_DISPATCHERS, Model._FIELD_AVAILABLE_DISPATCHERS)]

    # Process status values.
    _PROCESS_STATUS_EXECUTE = 'execute'
    _PROCESS_STATUS_STOP = 'stop'

    # The maximum number of seconds to wait after an execution was meant to start.
    _EXECUTE_WAIT_TOLERANCE = 900

    # Allowed file type substitutions.
    # @formatter:off
    _FILE_TYPE_SUBSTITUTIONS = {
        fusion_platform.FILE_TYPE_GEOTIFF: [fusion_platform.FILE_TYPE_GEOTIFF, fusion_platform.FILE_TYPE_DEM, fusion_platform.FILE_TYPE_JPEG2000],
        fusion_platform.FILE_TYPE_JPEG2000: [fusion_platform.FILE_TYPE_JPEG2000],
        fusion_platform.FILE_TYPE_DEM: [fusion_platform.FILE_TYPE_DEM],
        fusion_platform.FILE_TYPE_GEOJSON: [fusion_platform.FILE_TYPE_GEOJSON, fusion_platform.FILE_TYPE_KML, fusion_platform.FILE_TYPE_KMZ, fusion_platform.FILE_TYPE_ESRI_SHAPEFILE],
        fusion_platform.FILE_TYPE_KML: [fusion_platform.FILE_TYPE_KML],
        fusion_platform.FILE_TYPE_KMZ: [fusion_platform.FILE_TYPE_KMZ],
        fusion_platform.FILE_TYPE_CSV: [fusion_platform.FILE_TYPE_CSV],
        fusion_platform.FILE_TYPE_ESRI_SHAPEFILE: [fusion_platform.FILE_TYPE_ESRI_SHAPEFILE],
        fusion_platform.FILE_TYPE_JPEG: [fusion_platform.FILE_TYPE_JPEG],
        fusion_platform.FILE_TYPE_PNG: [fusion_platform.FILE_TYPE_PNG],
        fusion_platform.FILE_TYPE_PDF: [fusion_platform.FILE_TYPE_PDF],
        fusion_platform.FILE_TYPE_GZIP: [fusion_platform.FILE_TYPE_GZIP],
        fusion_platform.FILE_TYPE_ZIP: [fusion_platform.FILE_TYPE_ZIP],
        fusion_platform.FILE_TYPE_OTHER: [fusion_platform.FILE_TYPE_OTHER],
    }
    # @formatter:on

    def add_dispatcher(self, number=None, name=None):
        """
        Adds a dispatcher to the process. Dispatchers can be selected from the list of available dispatchers. An exception is raised if the process is in the
        execute status or the dispatcher does not exist.

        Args:
            number: The dispatcher number to add, starting from 1 for the first in the available dispatchers. Either the number or the name must be provided.
            name: The dispatcher name to add. Either the number or the name must be provided.

        Raises:
            ModelError: if the process is the execute status.
            ModelError: if the dispatcher does not exist.
            ModelError: if the model could not be updated and validated by the Fusion Platform<sup>&reg;</sup>.
        """
        # Make sure the arguments are provided.
        if (number is None) and (name is None):
            raise ModelError(i18n.t('models.process.dispatcher_not_specified'))

        # Make sure the process is not in the execute state.
        if hasattr(self, self.__class__._FIELD_PROCESS_STATUS) and (self.process_status == Process._PROCESS_STATUS_EXECUTE):
            raise ModelError(i18n.t('models.process.no_change_executing'))

        # Find the corresponding dispatcher.
        dispatchers = self._model.get(self.__class__._FIELD_AVAILABLE_DISPATCHERS) if self._model.get(
            self.__class__._FIELD_AVAILABLE_DISPATCHERS) is not None else []
        found_dispatcher = None

        for i, item in enumerate(dispatchers):
            found = (number is not None) and (number == (i + 1))
            found = (name is not None) and (name == item.get(self.__class__._FIELD_NAME)) if not found else found

            if found:
                found_dispatcher = item
                break

        if found_dispatcher is None:
            raise ModelError(i18n.t('models.process.cannot_find_dispatcher'))

        # Add the dispatcher to the end of the existing list.
        dispatchers = list(self._model.get(self.__class__._FIELD_DISPATCHERS, []))  # Convert read-only tuple to list, so we can modify it.
        dispatchers.append(found_dispatcher)

        # Update the dispatchers in the model.
        self._set_field([self.__class__._FIELD_DISPATCHERS], dispatchers)

        # Now update the model, persisting as needed.
        super(Process, self).update()

    @property
    def available_dispatchers(self):
        """
        Provides an iterator through the process' available dispatchers.

        Returns:
            An iterator through the available dispatchers.
        """
        return self.__dispatchers(
            self._model.get(self.__class__._FIELD_AVAILABLE_DISPATCHERS) if self._model.get(self.__class__._FIELD_AVAILABLE_DISPATCHERS) is not None else [])

    def copy(self, name):
        """
        Creates a new template process from an existing process object. This process is not persisted to the Fusion Platform<sup>&reg;</sup>.

        Args:
            name: The name of the copy.

        Returns:
            The new template process object.

        Raises:
            RequestError: if the copy fails.
            ModelError: if the model could not be created and validated by the Fusion Platform<sup>&reg;</sup>.
        """
        # Get a new template for the process model using the process as the source of the copy.
        process = Process(self._session)

        # Copy the process model.
        response = self._session.request(path=self._get_path(self.__class__._PATH_COPY), method=Session.METHOD_GET)

        # Assume that the resulting model is held within the expected key within the resulting dictionary.
        if Model._RESPONSE_KEY_MODEL not in response:
            raise ModelError(i18n.t('models.process.failed_copy'))

        # Make sure we have an organisation id.
        modified_response = response.get(Model._RESPONSE_KEY_MODEL, {})
        modified_response['organisation_id'] = self.organisation_id

        # Extract the extras.
        extracted_extras = self.__class__._extract_extras(response, extras=self.__class__._EXTRAS_LIST)

        for key, value in extracted_extras.items():
            modified_response[key] = value

        # Load the response into the model. We ignore missing required fields and those which are None.
        process._set_model_from_response(modified_response, partial=True)

        # Update the options because these are not copied across to the new model, even though they are returned in the response.
        options = modified_response.get('options', [])
        options = [] if options is None else options

        for option in options:
            # Set the option value. The value may be a string, rather than the required type, but that will automatically be converted.
            if (option.get(self.__class__._FIELD_NAME) is not None) and (option.get(self.__class__._FIELD_VALUE) is not None):
                process.__set_option(name=option.get(self.__class__._FIELD_NAME), value=option.get(self.__class__._FIELD_VALUE), coerce_value=True)

        # And now the same for the inputs. Here we also validate each input by retrieving it.
        inputs = modified_response.get('inputs', [])
        inputs = [] if inputs is None else inputs

        for i, input in enumerate(inputs):
            # See if we can find the associated model.
            if input.get(self.__class__._FIELD_ID) is not None:
                data = Data._model_from_api_id(self._session, organisation_id=self.organisation_id, data_id=input.get(self.__class__._FIELD_ID))
                process.__set_input(number=i + 1, data=data)

        # Set the name.
        process.update(name=name)

        # Return the copy.
        return process

    def create(self, **kwargs):
        """
        Attempts to persist the template process in the Fusion Platform<sup>&reg;</sup> so that it can be executed.

        Args:
            kwargs: The model attributes which override those already in the template.

        Raises:
            RequestError: if the create fails.
            ModelError: if the model could not be created and validated by the Fusion Platform<sup>&reg;</sup>.
        """
        # Attempt to issue the create.
        self._create(**kwargs)

    def __dispatchers(self, dispatchers):
        """
        Provides an iterator through dispatchers.

        Returns:
            An iterator through the dispatchers.
        """
        for dispatcher in dispatchers:
            # We first have to remove the mapping proxy so that we can wrap the dictionary in an object.
            dispatcher = value_from_read_only(dispatcher)

            # Encapsulate the dictionary within a model (which does not talk to the API).
            model = Dispatcher(None, schema=ProcessDispatcherSchema())
            model._set_model(dispatcher)

            yield model

    @property
    def dispatchers(self):
        """
        Provides an iterator through the process' dispatchers.

        Returns:
            An iterator through the dispatchers.
        """
        return self.__dispatchers(self._model.get(self.__class__._FIELD_DISPATCHERS) if self._model.get(self.__class__._FIELD_DISPATCHERS) is not None else [])

    def execute(self, wait=False):
        """
        Attempts to execute the created process in the Fusion Platform<sup>&reg;</sup>. Optionally waits for the next execution to start, and then for it to complete.

        Args:
            wait: Optionally wait for the next execution to start and complete? Default False.

        Raises:
            RequestError: if the execute fails.
            ModelError: if any execution fails.
        """
        # Send the request and load the resulting model.
        self._send_and_load(self._get_path(self.__class__._PATH_EXECUTE), method=Session.METHOD_POST)

        if wait:
            # If we are waiting for the execution to complete, wait for the next execution to start...
            self.wait_for_next_execution()

            # ...and for all the executions to complete. Note that we wait for all executions to complete, even if at least one has failed.
            exception = None

            for execution in self.executions:
                try:
                    execution.check_complete(wait=wait)
                except ModelError as e:
                    # Keep the first exception raised.
                    if exception is None:
                        exception = e

            # Raise any exception.
            if exception is not None:
                raise exception

    @property
    def executions(self):
        """
        Provides an iterator through the process's executions.

        Returns:
            An iterator through the execution objects.
        
        Raises:
            RequestError: if any get fails.
            ModelError: if a model could not be loaded or validated from the Fusion Platform<sup>&reg;</sup>.
        """
        return ProcessExecution._models_from_api_path(self._session, self._get_path(self.__class__._PATH_EXECUTIONS), reverse=True,
                                                      load_extras=False)  # Most recent first.

    def find_executions(self, id=None, group_id=None):
        """
        Searches for the process's executions with the specified id and/or group id, returning the first object found and an iterator.

        Args:
            id: The execution id to search for.
            group_id: The execution group id to search for.

        Returns:
            The first found execution object, or None if not found, and an iterator through the found execution objects.
        
        Raises:
            RequestError if any get fails.
            ModelError if a model could not be loaded or validated from the Fusion Platform<sup>&reg;</sup>.
        """
        filter = self.__class__._build_filter(
            [(self.__class__._FIELD_ID, self.__class__._FILTER_MODIFIER_EQ, id), (self.__class__._FIELD_GROUP_ID, self.__class__._FILTER_MODIFIER_EQ, group_id)])

        # Build the partial find generator and execute it.
        find = partial(ProcessExecution._models_from_api_path, self._session, self._get_path(self.__class__._PATH_EXECUTIONS), filter=filter, load_extras=False)
        return self.__class__._first_and_generator(find)

    @property
    def inputs(self):
        """
        Provides an iterator through the process' inputs.

        Returns:
            An iterator through the inputs.
        """
        for input in self._model.get(self.__class__._FIELD_INPUTS, []):
            # We first have to remove the mapping proxy so that we can wrap the dictionary in a model.
            input = value_from_read_only(input)

            # See if we can find the associated model.
            if input.get(self.__class__._FIELD_ID) is not None:
                data = Data._model_from_api_id(self._session, organisation_id=self.organisation_id, id=input.get(self.__class__._FIELD_ID))
                input[self.__class__._FIELD_NAME] = data.name

            # Encapsulate the dictionary within a model (which does not talk to the API).
            model = Input(None, schema=ProcessInputSchema())
            model._set_model(input)

            yield model

    @property
    def options(self):
        """
        Provides an iterator through the process' options.

        Returns:
            An iterator through the options.
        """
        return Option.options_iterator(self._model.get(self.__class__._FIELD_OPTIONS, []))

    def remove_dispatcher(self, number):
        """
        Removes the dispatcher service with the corresponding number from the process.

        Args:
            number: The number to remove, starting from 1 for the first dispatcher.

        Raises:
            ModelError: if the process is the execute status.
            ModelError: if the dispatcher does not exist.
            ModelError: if the model could not be updated and validated by the Fusion Platform<sup>&reg;</sup>.
        """
        # Make sure the argument is provided.
        if number is None:
            raise ModelError(i18n.t('models.process.dispatcher_not_specified'))

        # Make sure the process is not in the execute state.
        if hasattr(self, self.__class__._FIELD_PROCESS_STATUS) and (self.process_status == Process._PROCESS_STATUS_EXECUTE):
            raise ModelError(i18n.t('models.process.no_change_executing'))

        # Find the corresponding dispatcher.
        found_dispatcher_index = None
        found_dispatcher = None

        for i, item in enumerate(self._model.get(self.__class__._FIELD_DISPATCHERS, [])):
            found = (number is not None) and (number == (i + 1))

            if found:
                found_dispatcher_index = i
                found_dispatcher = item
                break

        if found_dispatcher is None:
            raise ModelError(i18n.t('models.process.cannot_find_dispatcher'))

        # Remove the dispatcher from the existing list.
        dispatchers = list(self._model.get(self.__class__._FIELD_DISPATCHERS, []))  # Convert read-only tuple to list, so we can modify it.
        dispatchers.pop(found_dispatcher_index)

        # Update the dispatchers in the model.
        self._set_field([self.__class__._FIELD_DISPATCHERS], dispatchers)

        # Now update the model, persisting as needed.
        super(Process, self).update()

    def __set_dispatcher(self, number, option_name=None, value=None, coerce_value=False, **kwargs):
        """
        Sets the specified option for the and kwargs for the dispatcher. An exception is raised if the process is in the execute status, the dispatcher does not
        exist or the option value has the wrong type.

        Args:
            number: The dispatcher number to update, starting from 1 for the first dispatcher.
            option_name: The option name for the dispatcher to set.
            value: The value for the option.
            coerce_value: Optionally coerce the supplied value to be the correct type. Default False.

        Raises:
            RequestError: if the update fails.
            ModelError: if the process is in the execute state.
            ModelError: if the value has a different type to the option.
        """
        # Make sure the argument is provided.
        if number is None:
            raise ModelError(i18n.t('models.process.dispatcher_not_specified'))

        # Make sure the process is not in the execute state.
        if hasattr(self, self.__class__._FIELD_PROCESS_STATUS) and (self.process_status == Process._PROCESS_STATUS_EXECUTE):
            raise ModelError(i18n.t('models.process.no_change_executing'))

        # Find the corresponding dispatcher.
        found_dispatcher_index = None
        found_dispatcher = None

        for i, item in enumerate(self._model.get(self.__class__._FIELD_DISPATCHERS, [])):
            found = (number is not None) and (number == (i + 1))

            if found:
                found_dispatcher_index = i
                found_dispatcher = item
                break

        if found_dispatcher is None:
            raise ModelError(i18n.t('models.process.cannot_find_dispatcher'))

        # Get the dispatcher so that it can be modified.
        dispatchers = list(self._model.get(self.__class__._FIELD_DISPATCHERS, []))  # Convert read-only tuple to list, so we can access it.
        dispatcher = dict(dispatchers[found_dispatcher_index])  # Convert read-only tuple to dict, so we can modify it.

        # Optionally, find the corresponding option.
        if (option_name is not None) or (value is not None):
            options = list(dispatcher.get(self.__class__._FIELD_OPTIONS, []))  # Convert read-only tuple to list, so we can modify it.
            options = [dict(option) for option in options]  # Convert read-only mapping to dict, so we can modify it.
            found_option_index = None
            found_option = None

            for i, item in enumerate(options):
                found = (option_name is not None) and (option_name == item.get(self.__class__._FIELD_NAME))

                if found:
                    found_option_index = i
                    found_option = item
                    break

            if found_option is None:
                raise ModelError(i18n.t('models.process.cannot_find_option'))

            # We can now update the option. All options are expressed as strings with the correct format.
            option_value = Option.get_option_value(found_option, value, coerce_value)
            found_option[self.__class__._FIELD_VALUE] = option_value
            dispatcher[self.__class__._FIELD_OPTIONS] = options
            dispatcher[self.__class__._FIELD_OPTIONS][found_option_index] = found_option

        # Modify any of the dispatcher attributes. We do not allow updates to read-only or hidden fields.
        schema = ProcessDispatcherSchema()

        for key in kwargs:
            if (Model._METADATA_READ_ONLY not in schema.fields[key].metadata) and (Model._METADATA_HIDE not in schema.fields[key].metadata):
                dispatcher[key] = kwargs[key]

        # Update the dispatchers in the model.
        self._set_field([self.__class__._FIELD_DISPATCHERS, found_dispatcher_index], dispatcher)

    def __set_input(self, number=None, input=None, data=None):
        """
        Sets the specified input for the process to the data item. An exception is raised if the process is in the execute status, the input does not exist, is not
        ready to be used or has the wrong file type.

        Args:
            number: The input number to set, starting from 1 for the first input. Either the number or the input must be provided.
            input: The input object for the input to set. Either the number or the input must be provided.
            data: The data object to use for the input.

        Raises:
            ModelError: if the process is the execute status.
            ModelError: if the input does not exist.
            ModelError: if the data object is ready to be used in a process.
            ModelError: if the data object has a different file type to the input.
        """
        # Make sure the arguments are provided.
        if (number is None) and (input is None):
            raise ModelError(i18n.t('models.process.input_not_specified'))

        if (data is None) or (not isinstance(data, Data)):
            raise ModelError(i18n.t('models.process.data_not_specified'))

        # Make sure the process is not in the execute state.
        if hasattr(self, self.__class__._FIELD_PROCESS_STATUS) and (self.process_status == Process._PROCESS_STATUS_EXECUTE):
            raise ModelError(i18n.t('models.process.no_change_executing'))

        # Find the corresponding input.
        found_input_index = None
        found_input = None

        for i, item in enumerate(self._model.get(self.__class__._FIELD_INPUTS, [])):
            found = (number is not None) and (number == (i + 1))
            found = (input is not None) and (str(input.ssd_id) == str(item.get(self.__class__._FIELD_SSD_ID))) and (
                    input.input == item.get(self.__class__._FIELD_INPUT)) if not found else found

            if found:
                found_input_index = i
                found_input = item
                break

        if found_input is None:
            raise ModelError(i18n.t('models.process.cannot_find_input'))

        # Check that all the files in the data object are ready to be used. Along the way, pick out the first file type.
        found_file_type = None
        ready = True

        for file in data.files:
            found_file_type = file.file_type if found_file_type is None else found_file_type

            if not hasattr(file, self.__class__._FIELD_PUBLISHABLE):
                ready = False

        if not ready:
            raise ModelError(i18n.t('models.process.data_not_ready'))

        # Check the file type against the allowed list of substitutions.
        if found_file_type not in Process._FILE_TYPE_SUBSTITUTIONS.get(found_input.get(self.__class__._FIELD_FILE_TYPE), []):
            raise ModelError(i18n.t('models.process.wrong_file_type', expected=found_input.get(self.__class__._FIELD_FILE_TYPE), actual=found_file_type))

        # We can now update the input.
        self._set_field([self.__class__._FIELD_INPUTS, found_input_index, self.__class__._FIELD_ID], data.id)

    def __set_option(self, name=None, option=None, value=None, coerce_value=False):
        """
        Sets the specified option for the process to the value. An exception is raised if the process is in the execute status, the option does not exist or the
        value has the wrong type.

        Args:
            name: The option name to set. Either the name or the option must be provided.
            option: The option object for the option to set. Either the name or the option must be provided.
            value: The value for the option.
            coerce_value: Optionally coerce the supplied value to be the correct type. Default False.

        Raises:
            ModelError: if the process is the execute status.
            ModelError: if the value has a different type to the option.
        """
        # Make sure the arguments are provided.
        if (name is None) and (option is None):
            raise ModelError(i18n.t('models.process.option_not_specified'))

        # Make sure the process is not in the execute state.
        if hasattr(self, self.__class__._FIELD_PROCESS_STATUS) and (self.process_status == Process._PROCESS_STATUS_EXECUTE):
            raise ModelError(i18n.t('models.process.no_change_executing'))

        # Find the corresponding option.
        found_option_index = None
        found_option = None

        for i, item in enumerate(self._model.get(self.__class__._FIELD_OPTIONS, [])):
            found = (name is not None) and (name == item.get(self.__class__._FIELD_NAME))
            found = (option is not None) and (str(option.ssd_id) == str(item.get(self.__class__._FIELD_SSD_ID))) and (
                    option.name == item.get(self.__class__._FIELD_NAME)) if not found else found

            if found:
                found_option_index = i
                found_option = item
                break

        if found_option is None:
            raise ModelError(i18n.t('models.process.cannot_find_option'))

        # We can now update the option. All options are expressed as strings with the correct format.
        option_value = Option.get_option_value(found_option, value, coerce_value)
        self._set_field([self.__class__._FIELD_OPTIONS, found_option_index, self.__class__._FIELD_VALUE], option_value)

    def stop(self):
        """
        Stops the process from being executed. This will abort any executions which are in progress and prevent any scheduled executions from taking place.

        Raises:
            RequestError: if the stop fails.
        """
        # Send the request and load the resulting model.
        self._send_and_load(self._get_path(self.__class__._PATH_STOP), method=Session.METHOD_POST)

    def update(self, input_number=None, input=None, data=None, dispatcher_number=None, option_name=None, option=None, value=None, coerce_value=False, **kwargs):
        """
        Attempts to update the model object with the given values. This assumes the model is updated using a PATCH RESTful request. This assumes that the patch body
        contains key names which include the name of the model class. Overridden to prevent changes if the process is being executed and to handle the special cases
        of setting inputs, options and dispatchers.

        Args:
            input_number: The input number to set, starting from 1 for the first input. Either the number or the input must be provided when setting an input.
            input: The input object for the input to set. Either the number or the input must be provided when setting an input.
            data: The data object to use for an input.
            dispatcher_number: The dispatcher number to update, starting from 1 for the first dispatcher. If used then options and kwargs are for the dispatcher.
            option_name: The option name to set. Either the name or the option must be provided when setting an option.
            option: The option object for the option to set. Either the name or the option must be provided when setting an option.
            value: The value for the option.
            coerce_value: Optionally coerce the supplied value to be the correct type. Default False.
            kwargs: The model attributes which are to be patched.

        Raises:
            RequestError: if the update fails.
            ModelError: if the process is in the execute state.
            ModelError: if the model could not be loaded or validated from the Fusion Platform<sup>&reg;</sup>.
        """
        # Make sure the process is not in the execute state.
        if hasattr(self, self.__class__._FIELD_PROCESS_STATUS) and (self.process_status == Process._PROCESS_STATUS_EXECUTE):
            raise ModelError(i18n.t('models.process.no_change_executing'))

        update_kwargs = kwargs

        # Deal with the special case of inputs.
        if (input_number is not None) or (input is not None):
            self.__set_input(number=input_number, input=input, data=data)

        # Deal with the special case of dispatchers.
        if dispatcher_number is not None:  # Options and kwargs are for the dispatcher.
            self.__set_dispatcher(number=dispatcher_number, option_name=option_name, value=value, coerce_value=coerce_value, **kwargs)

            # The kwargs have been used on the dispatcher, so are not for the process.
            update_kwargs = {}

        else:  # Options and kwargs are for the process.
            # Deal with the special case of options.
            if (option_name is not None) or (option is not None):
                self.__set_option(name=option_name, option=option, value=value, coerce_value=coerce_value)

        # Now update the model, persisting as needed.
        super(Process, self).update(**update_kwargs)

    def wait_for_next_execution(self):
        """
        Waits for the next execution of the process to start, according to its schedule. If executions are already started, this method will return immediately.
        Otherwise, this method will block until the next scheduled execution has started.

        Raises:
            RequestError: if any request fails.
            ModelError: if a model could not be loaded or validated from the Fusion Platform<sup>&reg;</sup>.
        """
        # Wait until we find the next execution.
        while True:
            # Load in the most recent version of the model.
            self.get(organisation_id=self.organisation_id)

            # Check that the model is executing. It may have stopped on error.
            if hasattr(self, self.__class__._FIELD_PROCESS_STATUS) and (self.process_status == Process._PROCESS_STATUS_STOP):
                raise ModelError(i18n.t('models.process.execution_stopped'))

            # Check whether we have the next execution listed in the model. We sort the list to find the most recent.
            self._logger.debug('checking for next execution')
            executions = []

            if self._model.get(self.__class__._FIELD_HAS_EXECUTIONS, False):
                executions = [item for item in self._model.get(self.__class__._FIELD_EXECUTIONS, [])]  # Turn the read-only field into a list we can sort.
                executions = sorted(executions, key=lambda item: item.get(self.__class__._FIELD_STARTED_AT), reverse=True)  # Sort by most recent first.

            execution = executions[0] if len(executions) > 0 else None

            # If the execution is in a group, then make sure that all the executions in the group have started.
            if (execution is not None) and (execution.get(self.__class__._FIELD_GROUP_ID) is not None):
                group = [item for item in executions if item.get(self.__class__._FIELD_GROUP_ID) == execution.get(self.__class__._FIELD_GROUP_ID)]
                execution = None if (len(group) < execution.get(self.__class__._FIELD_GROUP_COUNT)) else execution

            # Ignore any execution older than when the next execution is expected. This assumes that the process repeat start is maintained correctly, and that it
            # is set after any corresponding executions have been created for the current repeat start.
            execution = None if (execution is not None) and (execution.get(self.__class__._FIELD_STARTED_AT) < self.repeat_start) else execution

            # Stop if we have an execution which is beyond the repeat start date.
            if execution is not None:
                self._logger.debug('execution %s found', execution.get(self.__class__._FIELD_ID))
                break

            # If we have no recent executions, and longer than the allowed period has elapsed since the next execution was meant to start, then raise an exception.
            if (execution is None) and (self.repeat_start + timedelta(seconds=Process._EXECUTE_WAIT_TOLERANCE)) < datetime.now(timezone.utc):
                raise ModelError(i18n.t('models.process.execution_should_have_started'))

            # We are waiting, so block for a short while.
            sleep(self.__class__._API_UPDATE_WAIT_PERIOD)
