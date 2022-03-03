#
# Compiled translations.
#
# @author Matthew Casey
#
# (c) Digital Content Analysis Technology Ltd 2022
#

# Do not modify this file manually as it is built automatically by the localisations.py script.

import i18n

# @formatter:off
i18n.add_translation('session.request_failed', 'API request failed: %{message}', 'en')
i18n.add_translation('session.login_failed', 'Login failed', 'en')
i18n.add_translation('session.missing_password', 'Password must be specified', 'en')
i18n.add_translation('session.missing_email_user_id', 'Either an email address or a user id must be specified', 'en')
i18n.add_translation('fusion_platform.support', 'Support: support@d-cat.co.uk', 'en')
i18n.add_translation('fusion_platform.version_date', 'Date: %{version_date}', 'en')
i18n.add_translation('fusion_platform.version', 'Version: %{version}', 'en')
i18n.add_translation('fusion_platform.sdk', 'Fusion Platform(r) SDK', 'en')
i18n.add_translation('models.data_file.failed_download_url', 'Failed to get URL from download file response', 'en')
i18n.add_translation('models.data_file.no_download', 'No download is in progress', 'en')
i18n.add_translation('models.data_file.download_already_in_progress', 'Cannot download file as the download is already in progress', 'en')
i18n.add_translation('models.data.no_create', 'No create is in progress', 'en')
i18n.add_translation('models.data.failed_add_file_not_unique', 'Failed to add file as the id is not unique', 'en')
i18n.add_translation('models.data.failed_add_file_url', 'Failed to get URL from add file response', 'en')
i18n.add_translation('models.data.failed_add_file_id', 'Failed to get id from add file response', 'en')
i18n.add_translation('models.process_execution.execution_failed', 'Execution has failed', 'en')
i18n.add_translation('models.fields.uuid.invalid_uuid', 'Not a valid utf-8 string', 'en')
i18n.add_translation('models.fields.url.invalid_url', 'Not a valid URL', 'en')
i18n.add_translation('models.fields.tuple.invalid', 'Not a valid tuple', 'en')
i18n.add_translation('models.fields.timedelta.invalid', 'Not a valid period of time', 'en')
i18n.add_translation('models.fields.string.invalid_utf8', 'Not a valid utf-8 string', 'en')
i18n.add_translation('models.fields.string.invalid', 'Not a valid string', 'en')
i18n.add_translation('models.fields.relativedelta.invalid', 'Not a valid relative period of time', 'en')
i18n.add_translation('models.fields.nested.type', 'Invalid type', 'en')
i18n.add_translation('models.fields.list.invalid', 'Not a valid list', 'en')
i18n.add_translation('models.fields.ip.invalid_ip', 'Not a valid IP address', 'en')
i18n.add_translation('models.fields.integer.too_large', 'Integer too large', 'en')
i18n.add_translation('models.fields.integer.invalid', 'Not a valid integer', 'en')
i18n.add_translation('models.fields.float.special', 'Special numeric values (nan or infinity) are not permitted.', 'en')
i18n.add_translation('models.fields.float.too_large', 'Float too large', 'en')
i18n.add_translation('models.fields.float.invalid', 'Not a valid float', 'en')
i18n.add_translation('models.fields.email.invalid', 'Not a valid email address', 'en')
i18n.add_translation('models.fields.dict.invalid', 'Not a valid dictionary', 'en')
i18n.add_translation('models.fields.decimal.special', 'Special numeric values (nan or infinity) are not permitted', 'en')
i18n.add_translation('models.fields.decimal.too_large', 'Decimal too large', 'en')
i18n.add_translation('models.fields.decimal.invalid', 'Not a valid decimal', 'en')
i18n.add_translation('models.fields.datetime.format', '\'{input}\' cannot be formatted as a {obj_type}', 'en')
i18n.add_translation('models.fields.datetime.invalid_awareness', 'Not a valid {awareness} {obj_type}', 'en')
i18n.add_translation('models.fields.datetime.invalid', 'Not a valid {obj_type}', 'en')
i18n.add_translation('models.fields.boolean.invalid', 'Not a valid boolean', 'en')
i18n.add_translation('models.model.update_empty_body', 'Update cannot be requested as there are no attributes to be used (read-only attributes have been removed)', 'en')
i18n.add_translation('models.model.create_empty_body', 'Create cannot be requested as there are no attributes to be used (read-only attributes have been removed)', 'en')
i18n.add_translation('models.model.failed_model_validation', 'Failed to validate model: %{message}', 'en')
i18n.add_translation('models.model.failed_model_new', 'Failed to get model template from response', 'en')
i18n.add_translation('models.model.failed_model_send_and_load', 'Failed to request and load model', 'en')
i18n.add_translation('models.model.no_such_keys', 'No such keys %{keys}', 'en')
i18n.add_translation('models.model.readonly_property', 'Property %{property} is read-only and cannot be set', 'en')
i18n.add_translation('models.model.not_persisted', 'Model is not persisted in the Fusion Platform(r)', 'en')
i18n.add_translation('models.model.already_persisted', 'Model is already persisted in the Fusion Platform(r)', 'en')
i18n.add_translation('models.process.execution_should_have_started', 'Process execution should have started by now', 'en')
i18n.add_translation('models.process.not_executable', 'Process is not executable', 'en')
i18n.add_translation('models.process.wrong_file_type', 'File type of supplied data object (%{actual}) does not match the file type for the input (%{expected})', 'en')
i18n.add_translation('models.process.data_not_ready', 'Data object is not ready to be used in a process', 'en')
i18n.add_translation('models.process.option_wrong_type', 'Option value should be of type %{type}', 'en')
i18n.add_translation('models.process.cannot_find_option', 'No such option', 'en')
i18n.add_translation('models.process.cannot_find_input', 'No such input', 'en')
i18n.add_translation('models.process.option_not_specified', 'Option name or object must be provided to set option', 'en')
i18n.add_translation('models.process.data_not_specified', 'Data object must be provided to set input', 'en')
i18n.add_translation('models.process.input_not_specified', 'Input number or object must be provided to set input', 'en')
i18n.add_translation('models.process.no_change_executing', 'Process cannot be modified as it is currently executing', 'en')
# @formatter:on
