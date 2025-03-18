"""
Compiled translations.

author: Matthew Casey

&copy; [Digital Content Analysis Technology Ltd](https://www.d-cat.co.uk)
"""

# Do not modify this file manually as it is built automatically by the localisations.py script.

import i18n

# @formatter:off
i18n.add_translation('command.validate_constrained_error', 'Not one of %{constrained}', 'en')
i18n.add_translation('command.unknown_command', 'Unknown command \'%{command}\'', 'en')
i18n.add_translation('command.no_process_or_service', 'No such service, process or execution \'%{process_or_service}\'', 'en')
i18n.add_translation('command.no_such_service', 'No such service \'%{service}\'', 'en')
i18n.add_translation('command.no_such_process', 'No such process or execution \'%{process}\'', 'en')
i18n.add_translation('command.no_such_organisation', 'No such organisation \'%{organisation}\'', 'en')
i18n.add_translation('command.no_such_input', 'No such input \'%{input_name}\'', 'en')
i18n.add_translation('command.no_executions', 'No executions for process \'%{process}\'', 'en')
i18n.add_translation('command.invalid_login_response', 'Incorrect username or password', 'en')
i18n.add_translation('command.log_execution_group', ' (group \'%{group_id}\' %{group_index} of %{group_count})', 'en')
i18n.add_translation('command.log_execution_duration', ' - %{minutes} minute(s)', 'en')
i18n.add_translation('command.log_execution_period', ' (%{started_at}%{ended_at})', 'en')
i18n.add_translation('command.log_execution_ended_at', ' -> %{ended_at}', 'en')
i18n.add_translation('command.log_execution_warning', 'warning%{exit_type}%{abort_reason}', 'en')
i18n.add_translation('command.log_execution_failed', 'failed%{exit_type}%{abort_reason}', 'en')
i18n.add_translation('command.log_execution_exit_type', ' (%{exit_type})', 'en')
i18n.add_translation('command.log_execution_abort_reason', ': %{abort_reason}', 'en')
i18n.add_translation('command.log_execution_stopped', 'stopped', 'en')
i18n.add_translation('command.log_execution_progress', 'processing %{progress}%%', 'en')
i18n.add_translation('command.log_execution_success', 'success', 'en')
i18n.add_translation('command.log_actions', 'Actions:', 'en')
i18n.add_translation('command.log_assumptions', 'Assumptions:', 'en')
i18n.add_translation('command.log_description', 'Description:', 'en')
i18n.add_translation('command.log_summary', 'Summary:', 'en')
i18n.add_translation('command.log_dispatchers', 'Dispatchers:', 'en')
i18n.add_translation('command.log_options', 'Options:', 'en')
i18n.add_translation('command.log_outputs', 'Outputs:', 'en')
i18n.add_translation('command.log_inputs', 'Inputs:', 'en')
i18n.add_translation('command.log_execution', 'Execution \'%{id}\'%{period}: %{status}%{duration}%{group}', 'en')
i18n.add_translation('command.log_service', 'Service \'%{service}\'', 'en')
i18n.add_translation('command.log_process', 'Process \'%{process}\'', 'en')
i18n.add_translation('command.log_field', '%{field}: %{value}', 'en')
i18n.add_translation('command.log_subdivider', '................................................................................................', 'en')
i18n.add_translation('command.log_divider', '------------------------------------------------------------------------------------------------', 'en')
i18n.add_translation('command.log_bookend', '************************************************************************************************', 'en')
i18n.add_translation('command.wait_for_completion', ' and waiting for completion', 'en')
i18n.add_translation('command.wait_for_next', 'Waiting for next execution...', 'en')
i18n.add_translation('command.using_storage', 'Uploading storage \'%{filename}\' with id %{storage_id} to \'%{storage_name}\'', 'en')
i18n.add_translation('command.using_service', 'Using service \'%{service}\'', 'en')
i18n.add_translation('command.using_organisation', 'Using organisation \'%{organisation}\'', 'en')
i18n.add_translation('command.upload_storage', 'Uploading %{files} storage file(s)...', 'en')
i18n.add_translation('command.upload_inputs', 'Uploading %{inputs} input file(s)...', 'en')
i18n.add_translation('command.storage_name', '%{process} Storage %{group_index} %{chain_index}', 'en')
i18n.add_translation('command.start_process', 'Starting \'%{process}\' from service \'%{service}\'', 'en')
i18n.add_translation('command.remove_process', 'Removing input \'%{process}\'', 'en')
i18n.add_translation('command.remove_input', 'Removing input \'%{input}\'', 'en')
i18n.add_translation('command.prompt_yes', 'Yes', 'en')
i18n.add_translation('command.prompt_no', 'No', 'en')
i18n.add_translation('command.prompt_option', '%{title} (\'%{name}\', %{data_type}%{constrained_values}%{required})', 'en')
i18n.add_translation('command.password', 'Password', 'en')
i18n.add_translation('command.organisation', 'Organisation', 'en')
i18n.add_translation('command.find_inputs', 'Finding %{inputs} input file(s)...', 'en')
i18n.add_translation('command.executing', 'Executing...', 'en')
i18n.add_translation('command.email', 'Email', 'en')
i18n.add_translation('command.download_process_execution', 'Downloading \'%{process}\' (inputs %{inputs}, outputs %{outputs}, storage %{storage}, intermediate %{intermediate}, metrics %{metrics}, components %{components})', 'en')
i18n.add_translation('command.download_process', 'Downloading process \'%{process}\' to %{output}', 'en')
i18n.add_translation('command.download_files', 'Downloading %{files} file(s)...', 'en')
i18n.add_translation('command.download_executions', 'Gathering files%{wait} for %{executions} execution(s)...', 'en')
i18n.add_translation('command.download_execution', 'Downloading execution %{execution} to %{output}', 'en')
i18n.add_translation('command.define_storage', 'Defining storage file(s) for %{slices} slice(s)...', 'en')
i18n.add_translation('command.define_process', 'Defining \'%{process}\' (inputs %{inputs}, storage %{storage})', 'en')
i18n.add_translation('command.define_inputs', 'Defining %{files} input file(s)...', 'en')
i18n.add_translation('command.dispatch_intermediate', 'Dispatch intermediate components?', 'en')
i18n.add_translation('command.add_dispatcher', 'Add %{dispatcher} dispatcher?', 'en')
i18n.add_translation('command.download.process_help', 'the name of the process, the process id or execution id to download', 'en')
i18n.add_translation('command.download.process_long', 'process', 'en')
i18n.add_translation('command.download.help', 'downloads the inputs and/or outputs for each process', 'en')
i18n.add_translation('command.download.command', 'download', 'en')
i18n.add_translation('command.define.process_help', 'the name of the process, the process id or execution id to build the YAML file', 'en')
i18n.add_translation('command.define.process_long', 'process', 'en')
i18n.add_translation('command.define.help', 'outputs a YAML file for each existing process', 'en')
i18n.add_translation('command.define.command', 'define', 'en')
i18n.add_translation('command.start.no_wait_for_completion_help', 'do not wait for the execution to complete (default %%(default)s)\'', 'en')
i18n.add_translation('command.start.no_wait_for_completion_long', '--no_wait_for_completion', 'en')
i18n.add_translation('command.start.no_wait_for_completion_short', '-n', 'en')
i18n.add_translation('command.start.metrics_help', 'save process metrics to file (default %%(default)s)', 'en')
i18n.add_translation('command.start.metrics_long', '--metrics', 'en')
i18n.add_translation('command.start.metrics_short', '-t', 'en')
i18n.add_translation('command.start.component_help', 'to only download specific components, use the exact name of the component', 'en')
i18n.add_translation('command.start.component_long', '--component', 'en')
i18n.add_translation('command.start.component_short', '-c', 'en')
i18n.add_translation('command.start.intermediate_help', 'download the process inputs and/or outputs for all intermediate services (default %%(default)s)', 'en')
i18n.add_translation('command.start.intermediate_long', '--intermediate', 'en')
i18n.add_translation('command.start.intermediate_short', '-m', 'en')
i18n.add_translation('command.start.storage_help', 'downloads the storage (default %%(default)s)', 'en')
i18n.add_translation('command.start.storage_long', '--storage', 'en')
i18n.add_translation('command.start.storage_short', '-s', 'en')
i18n.add_translation('command.start.outputs_help', 'downloads the outputs (default %%(default)s)', 'en')
i18n.add_translation('command.start.outputs_long', '--outputs', 'en')
i18n.add_translation('command.start.outputs_short', '-o', 'en')
i18n.add_translation('command.start.inputs_help', 'downloads the inputs (default %%(default)s)', 'en')
i18n.add_translation('command.start.inputs_long', '--inputs', 'en')
i18n.add_translation('command.start.inputs_short', '-i', 'en')
i18n.add_translation('command.start.remove_help', 'removes the process and inputs after download (default %%(default)s)', 'en')
i18n.add_translation('command.start.remove_long', '--remove', 'en')
i18n.add_translation('command.start.remove_short', '-r', 'en')
i18n.add_translation('command.start.download_help', 'download the process inputs and/or outputs', 'en')
i18n.add_translation('command.start.download_long', '--download', 'en')
i18n.add_translation('command.start.download_short', '-d', 'en')
i18n.add_translation('command.start.wait_for_start_help', 'wait for the process to start (default %%(default)s)\'', 'en')
i18n.add_translation('command.start.wait_for_start_long', '--wait_for_start', 'en')
i18n.add_translation('command.start.wait_for_start_short', '-w', 'en')
i18n.add_translation('command.start.options_help', 'the list of options to be applied as \'option=value\'', 'en')
i18n.add_translation('command.start.options_long', '--options', 'en')
i18n.add_translation('command.start.options_short', '-p', 'en')
i18n.add_translation('command.start.input_list_help', 'the list of inputs to be used as either filenames or pre-existing input names', 'en')
i18n.add_translation('command.start.input_list_long', '--input_list', 'en')
i18n.add_translation('command.start.input_list_short', '-l', 'en')
i18n.add_translation('command.start.definition_help', 'the names of the service used to start processes or YAML files which defines everything', 'en')
i18n.add_translation('command.start.definition_long', 'service_or_yaml', 'en')
i18n.add_translation('command.start.help', 'starts a process', 'en')
i18n.add_translation('command.start.command', 'start', 'en')
i18n.add_translation('command.display.service_or_process_help', 'the names of the service, id, SSD id, process, process id or associated execution id that are to be displayed', 'en')
i18n.add_translation('command.display.service_or_process_long', 'process_or_service', 'en')
i18n.add_translation('command.display.help', 'displays service information or a configured process', 'en')
i18n.add_translation('command.display.command', 'display', 'en')
i18n.add_translation('command.subparser', 'displays a service or process, or starts, defines or downloads a process', 'en')
i18n.add_translation('command.version_content', '%%(prog)s %{version} (%{version_date})', 'en')
i18n.add_translation('command.version_help', 'show the version information and exit', 'en')
i18n.add_translation('command.version_long', '--version', 'en')
i18n.add_translation('command.version_short', '-v', 'en')
i18n.add_translation('command.debug_help', 'show debug output (default \'%%(default)s\')', 'en')
i18n.add_translation('command.debug_long', '--debug', 'en')
i18n.add_translation('command.debug_short', '-b', 'en')
i18n.add_translation('command.organisation_help', 'the organisation to be used', 'en')
i18n.add_translation('command.organisation_long', '--organisation', 'en')
i18n.add_translation('command.organisation_short', '-g', 'en')
i18n.add_translation('command.email_help', 'the email address to be used to login', 'en')
i18n.add_translation('command.email_long', '--email', 'en')
i18n.add_translation('command.email_short', '-e', 'en')
i18n.add_translation('command.deployment_help', 'the deployment used to define the API URL (default \'%%(default)s\')', 'en')
i18n.add_translation('command.deployment_long', '--deployment', 'en')
i18n.add_translation('command.deployment_short', '-y', 'en')
i18n.add_translation('command.epilog', '''
For more detailed options, use:

  fusion_platform display --help
  fusion_platform start --help
  fusion_platform define --help
  fusion_platform download --help

''', 'en')
i18n.add_translation('command.description', '''
Use this command to display service information and processes, and to start, download or define processes. Processes can be selected via command line options or
defined by a YAML file.

Usage:
  The following will display information about one or more services or processes from the given \'service_or_process_name\'.

    fusion_platform display <service_or_process_name> ...

  For a service, this will display the full service documentation, including its expected inputs and options. For a process, it will show the current process
  configuration.

  The following will attempt to create one or more processes from the given \'service_name\' to use the inputs (in order) and options and execute them. All
  processes will use the same inputs and options:

    fusion_platform start <service_name> ... -l <input_file|input_name> ... -p <option=value> ...

  The following will also attempt to create one or more processes and execute them, but this time with the parameters specified in the YAML files:

    fusion_platform start <yaml_file> ...

  The YAML file has the following structure:

  service_name: <service_name>
  process_name: <process_name>
  inputs:
    - <input_file|input_name>
    - name: <input_name>
      file: <input_file>
    ...
  storage:
    - <storage_id>: <storage_file>
    ...
  options:
    <option>: <value>
    ...
  dispatchers:
    - name: <dispatcher_name>
      options:
        <option>: <value>
        ...
    ...

  Note that additional values can be set in the YAML file which cannot be set via the command line, such as \'process_name\', \'storage\' and \'dispatchers\'.

  String values can include the following keywords, which will be replaced by corresponding values:

  {service_name}:           Is replaced with the service name.
  {now}:                    Is replaced with the current date and time (UTC).
  {today@hour:minute}:      Is replaced with today\'s date with the optional hour and minute (UTC). If \'@hour:minute\' is not provided, \'@00:00\' is assumed.
  {tomorrow@hour:minute}:   Is replaced with tomorrow\'s date with the optional hour and minute (UTC). If \'@hour:minute\' is not provided, \'@00:00\' is assumed.
  {<day_name>@hour:minute}: Is replaced with the next occurrence of the specified day, including today. If \'@hour:minute\' is not provided, \'@00:00\' is assumed.

  The following will create a YAML file from one or more existing processes. The YAML file will be named as a sanitised version of the process name with any
  existing file overwritten:

    fusion_platform define <process_name> ...

  The following will optionally download all the outputs for the executions of a process. Only the last execution is downloaded, unless it is part of a group,
  in which case all the executions in the group are downloaded. The files are downloaded to a sanitised version of the process name with any existing directory
  replaced:

    fusion_platform download <process_name> -o

  where
    service_name: Is the name of the service used to create the process.
    process_name: Is the name of the process, or for define or download a process id or an execution id.
    input_file:   Is the path to an input file. The file\'s extension will be used to work out what type of file it is.
    input_name:   Is the name of an existing input within the Fusion Platform(r) which will be used.
    storage_id:   Is the UUID of the storage data item which should be uploaded.
    storage_file: Is the path to a storage file.
    option:       The precise (lower case) name of the option. For example, \'minimum_coverage\' or \'repeat_count\'.
    value:        The value of the option. For date times, use ISO formatting, such as \'2024-02-21T13:40:06.732527+00:00\'
    yaml_file:    Is the path to the YAML file.

''', 'en')
i18n.add_translation('command.program', 'fusion_platform', 'en')
i18n.add_translation('session.request_failed', 'API request failed: %{message}', 'en')
i18n.add_translation('session.login_failed', 'Login failed', 'en')
i18n.add_translation('session.missing_password', 'Password must be specified', 'en')
i18n.add_translation('session.missing_email_user_id', 'Either an email address or a user id must be specified', 'en')
i18n.add_translation('fusion_platform.url', 'https://www.d-cat.co.uk', 'en')
i18n.add_translation('fusion_platform.support', 'Support: support@d-cat.co.uk', 'en')
i18n.add_translation('fusion_platform.version_date', 'Date: %{version_date}', 'en')
i18n.add_translation('fusion_platform.version', 'Version: %{version}', 'en')
i18n.add_translation('fusion_platform.sdk', 'Fusion Platform(r) SDK', 'en')
i18n.add_translation('fusion_platform.organisation', 'Digital Content Analysis Technology Ltd', 'en')
i18n.add_translation('models.data_file.failed_download_url', 'Failed to get URL from download file response', 'en')
i18n.add_translation('models.data_file.no_download', 'No download is in progress', 'en')
i18n.add_translation('models.data_file.download_already_in_progress', 'Cannot download file as the download is already in progress', 'en')
i18n.add_translation('models.data_file.organisation_id.description', 'The owning organisation.', 'en')
i18n.add_translation('models.data_file.organisation_id.title', 'Organisation', 'en')
i18n.add_translation('models.data.no_upload', 'No upload is in progress', 'en')
i18n.add_translation('models.data.no_create', 'No create is in progress', 'en')
i18n.add_translation('models.data.failed_add_missing_file', 'Failed to add file as the file does not exist: %{file}', 'en')
i18n.add_translation('models.data.failed_add_file_not_unique', 'Failed to add file as the id is not unique', 'en')
i18n.add_translation('models.data.failed_add_file_url', 'Failed to get URL from add file response', 'en')
i18n.add_translation('models.data.failed_add_file_id', 'Failed to get id from add file response', 'en')
i18n.add_translation('models.data.failed_copy_id', 'Failed to get data id from copy response', 'en')
i18n.add_translation('models.process_execution.execution_warning', 'Execution has completed successfully but with a warning: %{abort_reason}', 'en')
i18n.add_translation('models.process_execution.execution_failed', 'Execution has failed: %{abort_reason}', 'en')
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
i18n.add_translation('models.model.failed_model_send_and_load', 'Failed to request and load model', 'en')
i18n.add_translation('models.model.no_such_keys', 'No such keys %{keys}', 'en')
i18n.add_translation('models.model.readonly_property', 'Property %{property} is read-only and cannot be set', 'en')
i18n.add_translation('models.model.not_persisted', 'Model is not persisted in the Fusion Platform(r)', 'en')
i18n.add_translation('models.model.already_persisted', 'Model is already persisted in the Fusion Platform(r)', 'en')
i18n.add_translation('models.model.representation', '%{name}%{attributes}', 'en')
i18n.add_translation('models.process.failed_copy', 'Failed to get process from copy response', 'en')
i18n.add_translation('models.process.execution_should_have_started', 'Process execution should have started by now', 'en')
i18n.add_translation('models.process.execution_stopped', 'Process execution has been stopped', 'en')
i18n.add_translation('models.process.wrong_file_type', 'File type of supplied data object (%{actual}) does not match the file type for the input (%{expected})', 'en')
i18n.add_translation('models.process.data_not_ready', 'Data object is not ready to be used in a process', 'en')
i18n.add_translation('models.process.option_wrong_type', 'Option value should be of type %{type}', 'en')
i18n.add_translation('models.process.cannot_find_option', 'No such option', 'en')
i18n.add_translation('models.process.cannot_find_input', 'No such input', 'en')
i18n.add_translation('models.process.cannot_find_dispatcher', 'No such dispatcher', 'en')
i18n.add_translation('models.process.option_not_specified', 'Option name or object must be provided to set option', 'en')
i18n.add_translation('models.process.data_not_specified', 'Data object must be provided to set input', 'en')
i18n.add_translation('models.process.input_not_specified', 'Input number or object must be provided to set input', 'en')
i18n.add_translation('models.process.dispatcher_not_specified', 'Dispatcher number or name must be provided to add a dispatcher', 'en')
i18n.add_translation('models.process.no_change_executing', 'Process cannot be modified as it is currently executing', 'en')
i18n.add_translation('models.process.option.constrained_values.description', 'The constrained values for the option.', 'en')
i18n.add_translation('models.process.option.constrained_values.title', 'Constrained Values', 'en')
i18n.add_translation('models.process.option.constrained_names.description', 'The constrained value names for the option.', 'en')
i18n.add_translation('models.process.option.constrained_names.title', 'Constrained Names', 'en')
i18n.add_translation('models.process.option.representation_required', ', required', 'en')
i18n.add_translation('models.process.option.representation_constrained_values', ' %{constrained_values}', 'en')
i18n.add_translation('models.process.option.representation', '%{title} (\'%{name}\', %{data_type}%{constrained_values}%{required}) = %{value}: %{description}', 'en')
i18n.add_translation('models.process.input.representation_id', ' (%{id})', 'en')
i18n.add_translation('models.process.input.representation_name', ' %{name}', 'en')
i18n.add_translation('models.process.input.representation', '%{title} (%{file_type}) =%{name}%{id}: %{description}', 'en')
i18n.add_translation('models.process.dispatcher.representation', '%{name} (%{ssd_id}, intermediate %{dispatch_intermediate}): %{documentation_summary}', 'en')
# @formatter:on
