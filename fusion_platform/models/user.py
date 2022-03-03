#
# User model class file.
#
# @author Matthew Casey
#
# (c) Digital Content Analysis Technology Ltd 2022
#

from marshmallow import Schema, EXCLUDE

from fusion_platform.models import fields
from fusion_platform.models.model import Model
from fusion_platform.models.organisation import Organisation
from fusion_platform.session import Session


# Define the model schema classes. These are maintained from the API definitions.

class UserOrganisationSchema(Schema):
    """
    Nested schema class for organisation.
    """

    id = fields.UUID(required=True)
    last = fields.Boolean(required=True)

    class Meta:
        """
        When loading an object, make sure we exclude any unknown fields, rather than raising an exception, and put fields in their definition order.
        """
        unknown = EXCLUDE
        ordered = True


class UserSchema(Schema):
    """
    Schema class for user model. Abridged from API to provide only key fields.
    """
    id = fields.UUID(required=True, read_only=True)  # Changed to prevent this being updated.

    created_at = fields.DateTime(required=True, read_only=True)  # Changed to prevent this being updated.
    updated_at = fields.DateTime(required=True, read_only=True)  # Changed to prevent this being updated.

    email = fields.Email(required=True, read_only=True)  # Changed to prevent this being updated.
    # Removed email_verified.
    given_name = fields.String(required=True)
    family_name = fields.String(required=True)
    telephone = fields.String(allow_none=True)

    role = fields.Integer(allow_none=True)  # Changed to optional.

    # Removed location_ip_address.
    # Removed location_ip_country.

    default_output_storage_period = fields.Integer(required=True)

    time_zone = fields.String(required=True)
    locale = fields.String(required=True)
    units = fields.String(required=True)

    notification_service_status = fields.List(fields.String(required=True), allow_none=True)
    notification_account = fields.List(fields.String(required=True), allow_none=True)
    notification_processing_chain = fields.List(fields.String(required=True), allow_none=True)
    notification_new_features = fields.List(fields.String(required=True), allow_none=True)
    notification_contact = fields.List(fields.String(required=True), allow_none=True)

    organisations = fields.List(fields.Nested(UserOrganisationSchema()), allow_none=True, hide=True)  # Changed to hide as an attribute.

    last_request_at = fields.DateTime(allow_none=True, read_only=True)  # Changed to prevent this being updated.

    class Meta:
        """
        When loading an object, make sure we exclude any unknown fields, rather than raising an exception, and put fields in their definition order.
        """
        unknown = EXCLUDE
        ordered = True


class User(Model):
    """
    User model class providing attributes and methods to manipulate user details.
    """

    # Override the schema.
    _SCHEMA = UserSchema()

    # Base path.
    _PATH_BASE = '/users/{user_id}'

    # Override the standard model paths.
    _PATH_DELETE = _PATH_BASE
    _PATH_GET = _PATH_BASE
    _PATH_PATCH = _PATH_BASE

    # Add in the custom model paths.
    _PATH_CHANGE_PASSWORD = f"{_PATH_BASE}/change_password"

    def change_password(self, old, new):
        """
        Changes the user password. The new password must conform to the current password policy.

        :param old: The old password.
        :param new: The new password.
        :raises RequestError if the update fails.
        """
        body = {self.__class__.__name__: {'old_password': old, 'new_password': new}}
        self._session.request(path=self._get_path(self.__class__._PATH_CHANGE_PASSWORD), method=Session.METHOD_POST, body=body)

    @property
    def organisations(self):
        """
        Provides an iterator through the organisations which the user belongs to.

        :return: An iterator through the organisations.
        :raises RequestError if any get fails.
        :raises ModelError if a model could not be loaded or validated from the Fusion Platform(r).
        """
        return Organisation._models_from_api_ids(self._session, [{self.__class__.FIELD_ID: organisation.get(self.__class__.FIELD_ID)} for organisation in
                                                                 self._model.get('organisations', [])])
