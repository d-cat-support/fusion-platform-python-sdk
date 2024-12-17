"""
Main entry point for the command line.

author: Matthew Casey

&copy; [Digital Content Analysis Technology Ltd](https://www.d-cat.co.uk)
"""

import argparse
from argparse import RawTextHelpFormatter
from copy import deepcopy
import csv
from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from functools import partial
import i18n
import json
import logging
from marshmallow.utils import _Missing
import os
from pathos.multiprocessing import ProcessPool as Pool
from prompt_toolkit import prompt
from prompt_toolkit import print_formatted_text as print
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.validation import Validator
import re
import shutil
import tempfile
from time import sleep
from tqdm import tqdm
import uuid
import yaml

# Make sure localisation is set up before any SDK-specific imports.
from fusion_platform.localise import Localise

Localise.setup()

import fusion_platform
from fusion_platform.base import Base
from fusion_platform.common.utilities import json_default
from fusion_platform.models.data import Data
from fusion_platform.models.model import Model
from fusion_platform.session import RequestError


class CommandError(Exception):
    """
    Exception raised on command errors.
    """
    pass


class Command(Base):
    """
    Command class providing a CLI.
    """

    # Deployment constants.
    _DEPLOYMENT_KEY_URL = 'url'
    _DEPLOYMENT_KEY_STAGE = 'stage'
    _DEPLOYMENT_KEY_REGION = 'region'

    _DEPLOYMENT_PRODUCTION_IRL = 'production-irl'
    _DEPLOYMENT_PRODUCTION_AUS = 'production-aus'
    _DEPLOYMENT_STAGE = 'stage'

    DEPLOYMENTS = {
        _DEPLOYMENT_PRODUCTION_IRL: {
            _DEPLOYMENT_KEY_URL: 'https://api.thefusionplatform.com',
            _DEPLOYMENT_KEY_STAGE: 'production',
            _DEPLOYMENT_KEY_REGION: 'eu-west-1'
        },
        _DEPLOYMENT_PRODUCTION_AUS: {
            _DEPLOYMENT_KEY_URL: 'https://api.thefusionplatform.com.au',
            _DEPLOYMENT_KEY_STAGE: 'production-aus',
            _DEPLOYMENT_KEY_REGION: 'ap-southeast-2'
        },
        _DEPLOYMENT_STAGE: {
            _DEPLOYMENT_KEY_URL: 'https://api.stage.thefusionplatform.com',
            _DEPLOYMENT_KEY_STAGE: 'stage',
            _DEPLOYMENT_KEY_REGION: 'eu-west-1'
        }
    }

    # Useful download constants.
    _DOWNLOAD_INPUT = 'input'
    _DOWNLOAD_OUTPUT = 'output'
    _DOWNLOAD_STORAGE = 'storage'

    # Metrics used during download.
    _METRICS_FILE = 'metrics.csv'
    _METRICS_METRICS = 'metrics'
    _METRICS_EXECUTION = 'execution'
    _METRICS_PROCESS = 'process'
    _METRICS_DURATION = 'duration'
    _METRICS_COMPONENT = 'component'
    _METRICS_SUCCESS = 'success'
    _METRICS_CPU = 'cpu'
    _METRICS_MEMORY = 'memory'
    _METRICS_RUNTIME = 'runtime'
    _METRIC_S3_INPUT_SIZE = 'input_size'
    _METRIC_S3_OUTPUT_SIZE = 'output_size'
    _METRIC_S3_TRANSFER_BYTES = 's3_transfer_bytes'
    _METRIC_EXTERNAL_TRANSFER_BYTES = 'external_transfer_bytes'

    # Process other field constants.
    _MODEL_FIELDS = ['output_storage_period', 'run_type', 'repeat_count', 'repeat_start', 'repeat_end', 'repeat_gap', 'repeat_offset']

    # Storage constants.
    _STORAGE_NAME = 'storage.tar.gz'  # Must match the engine TaskManager#STORAGE_NAME.

    # For keyword replacement.
    _KEYWORD_SERVICE_NAME = 'service_name'
    _KEYWORD_NOW = 'now'
    _KEYWORD_TODAY = 'today'
    _KEYWORD_TOMORROW = 'tomorrow'

    # YAML file constants.
    _YAML_EXTENSION = '.yml'
    _YAML_SERVICE_NAME = _KEYWORD_SERVICE_NAME
    _YAML_PROCESS_NAME = 'process_name'
    _YAML_INPUTS = 'inputs'
    _YAML_STORAGE = 'storage'
    _YAML_OPTIONS = 'options'
    _YAML_DISPATCHERS = 'dispatchers'

    def __init__(self):
        """
        Initialises the object.
        """
        super().__init__()

        # For keyword replacement, build a dictionary of day names mapped to the corresponding date from now.
        now = datetime.now(timezone.utc)
        days = [
            datetime(now.year, now.month, now.day, tzinfo=timezone.utc) + timedelta(days=day) for day in range(0, 7)
        ]

        self.__keyword_day_names = {day.strftime('%A').lower(): day for day in days}
        self.__keyword_day_names[Command._KEYWORD_TODAY] = now
        self.__keyword_day_names[Command._KEYWORD_TOMORROW] = now + timedelta(days=1)

        # Set the default print level.
        self.__print_level = logging.INFO

    def __create_process(self, organisation, process_name, options, dispatchers, service, data_items):
        """
        Creates a new process based upon the service, options, dispatchers and input data items.

        Args:
            organisation: The logged in organisation.
            process_name: The name of the process.
            options: The list of options.
            dispatchers: The list of dispatchers.
            service: The base service to create the process from.
            data_items: The list of data items to be used as inputs.

        Returns:
            The process model.
        """

        # Create a template process from the service.
        process = organisation.new_process(name=process_name, service=service)

        # Configure the process to use the inputs and set its options. Note that we filter out model level fields and set those as keyword arguments.
        for i, data_item in enumerate(data_items):
            process.update(input_number=i + 1, data=data_item)

        kwargs = {}

        for key, value in options.items():
            if key in Command._MODEL_FIELDS:
                kwargs[key] = value
            else:
                process.update(option_name=key, value=value, coerce_value=True)

        if len(kwargs) > 0:
            process.update(**kwargs)

        # Add in optional dispatchers.
        dispatchers_added = 0

        for i, dispatcher in enumerate(process.available_dispatchers):
            finished = False

            while not finished:
                # Either find the dispatchers from what has been loaded from the YAML file or prompt the user.
                add = False
                dispatcher_options = {}

                if dispatchers is not None:
                    # See if any of the remaining dispatchers match this one. Once used, the corresponding dispatcher is marked as used.
                    filtered_dispatchers = [item for item in dispatchers if
                                            (item.get(Model._FIELD_NAME) == dispatcher.name) and (not item.get(Model._FIELD_USED, False))]

                    if len(filtered_dispatchers) > 0:
                        selected_dispatcher = filtered_dispatchers[0]
                        selected_dispatcher[Model._FIELD_USED] = True
                        add = True
                        dispatcher_options = selected_dispatcher.get(Model._FIELD_OPTIONS) if selected_dispatcher.get(Model._FIELD_OPTIONS) is not None else {}

                else:
                    response = self.__get_input(i18n.t('command.add_dispatcher', dispatcher=dispatcher.name),
                                                constrained_values=[i18n.t('command.prompt_no'), i18n.t('command.prompt_yes')])

                    if (response is not None) and response.lower().startswith(i18n.t('command.prompt_yes').lower()[0]):
                        add = True

                        for option in dispatcher.options:
                            option_value = self.__get_input(option.name)

                            if option_value is not None:
                                dispatcher_options[option.name] = option_value

                if add:
                    process.add_dispatcher(number=(i + 1))
                    dispatchers_added += 1

                    for option_name, option_value in dispatcher_options.items():
                        process.update(dispatcher_number=dispatchers_added, option_name=option_name, value=option_value)
                else:
                    finished = True

        # Create the process, which will validate its options and inputs.
        process.create()

        return process

    def define_process(self, organisation, process_name, download_inputs=False, download_storage=False):
        """
        Obtains the process definition for a process.

        Args:
            organisation: The logged in organisation.
            process_name: The name of the process to be defined. This can also be the id of a process.
            download_inputs: Download the input files as well? Default False.
            download_storage: Download the storage files as well? Default False.

        Returns:
            The process definition.
        """
        self.__print(logging.INFO, i18n.t('command.define_process', process=process_name, inputs=download_inputs, storage=download_storage))

        # We are defining an existing process.
        process, _ = self.get_process_or_execution(organisation, process_name)

        # Get the underlying service name.
        service, _ = organisation.find_services(ssd_id=process.ssd_id)

        # Get the options and dispatchers.
        options = {option.name: self.__format_value(option.value, data_type=option.data_type) for option in process.options}
        dispatchers = [
            {Model._FIELD_NAME: dispatcher.name,
             Model._FIELD_OPTIONS: {option.name: self.__format_value(option.value, data_type=option.data_type) for option in dispatcher.options}} for dispatcher in
            process.dispatchers]

        # Add in the standard options.
        for field in Command._MODEL_FIELDS:
            if hasattr(process, field):
                options[field] = self.__format_value(getattr(process, field))

        # We may want to download inputs and storage.
        downloads = []

        # Get the inputs, optionally adding in the files, downloading them as well.
        if download_inputs:
            # Get all the input files.
            inputs = []
            extracted_inputs = [(k + 1, input) for k, input in enumerate(process.inputs)]

            self.__print(logging.INFO, i18n.t('command.define_inputs', files=len(extracted_inputs)))
            progress_bar = tqdm(total=len(extracted_inputs), ncols=100)

            for k, input in extracted_inputs:
                # Get the data item for this input.
                data, _ = organisation.find_data(id=input.id)
                data.check_analysis_complete(wait=True)

                # Get the list of files which we filter to only use those files that are not sources. This will include any files which do not have an alternative.
                data_files = [data_file for data_file in data.files if data_file.file_type.lower().strip() == input.file_type.lower().strip()]
                file_ids_to_ignore = [str(data_file.source) for data_file in data_files if hasattr(data_file, 'source') and (data_file.source is not None)]
                data_files = [data_file for data_file in data_files if str(data_file.file_id) not in file_ids_to_ignore]

                # Build the list of downloads. Here we take just the first file found on the assumption that there should be only one.
                if len(data_files) > 0:
                    downloads.append((data_files[0], data_files[0].file_name))
                    inputs.append({Model._FIELD_NAME: data.name, Model._FIELD_FILE: data_files[0].file_name})

                progress_bar.update(1)

            progress_bar.close()

        else:
            # Just get the names of the inputs.
            inputs = [input.name for input in process.inputs]

        # Get the storage ready for download, if needed. Optional storage is used by each slice and each component within the chain. We ignore aggregators.
        storage = {}

        if download_storage:
            # Loop through all aggregators and non-aggregators.
            non_aggregator_count = process.non_aggregator_count if hasattr(process, Model._FIELD_NON_AGGREGATOR_COUNT) else 0
            non_aggregator_digits = len(str(non_aggregator_count))
            non_aggregator_chains = process.chains if hasattr(process, Model._FIELD_CHAINS) else []

            self.__print(logging.INFO, i18n.t('command.define_storage', slices=non_aggregator_count))
            progress_bar = tqdm(total=non_aggregator_count, ncols=100)

            for group_index in range(1, non_aggregator_count + 1):
                ssd_ids = [(i, non_aggregator_chains[i].get(Model._FIELD_SSD_ID)) for i in range(len(non_aggregator_chains))]
                chain_digits = len(str(len(ssd_ids)))

                for chain_index, ssd_id in ssd_ids:
                    storage_data_item = self.__get_storage_data_item(process, group_index, non_aggregator_count, ssd_id, chain_index)

                    if storage_data_item is not None:
                        # Add the storage file to the downloads. We assume there are zero or one file for the storage data item.
                        storage_data_item.check_analysis_complete(wait=True)
                        storage_data_file = next(storage_data_item.files, None)

                        if storage_data_file is not None:
                            path = f"{str(group_index).zfill(non_aggregator_digits)}_{str(chain_index).zfill(chain_digits)}_{storage_data_file.file_name.split('_')[-1]}"
                            key = f"{group_index}_{non_aggregator_count}_{ssd_id}_{chain_index}"
                            downloads.append((storage_data_file, path))
                            storage[key] = path

                progress_bar.update(1)

            progress_bar.close()

        # Download the files.
        self.__download_files(downloads)

        # Build the definition.
        process_definition = {
            Command._YAML_SERVICE_NAME: service.name if service is not None else '',
            Command._YAML_PROCESS_NAME: process_name,
            Command._YAML_INPUTS: inputs,
            Command._YAML_STORAGE: storage,
            Command._YAML_OPTIONS: options,
            Command._YAML_DISPATCHERS: dispatchers
        }

        return process_definition

    def __download_execution(self, process, download_inputs, download_outputs, download_storage, download_intermediate, download_components, output_dir, execution):
        """
        Downloads an execution.

        Args:
            process: The process containing the execution to be downloaded.
            download_inputs: Should inputs be downloaded?
            download_outputs: Should outputs be downloaded?
            download_storage: Should storage be downloaded?
            download_intermediate: Should intermediate components be downloaded?
            download_components: The names of the components that should be downloaded? If None or [], then all components are downloaded.
            output_dir: The output directory.
            execution: The execution to be downloaded.

        Returns:
            The list of file tuples to be downloaded (file model, download path), and the metrics.
        """
        download_components = [] if download_components is None else download_components
        started_at = process.created_at
        ended_at = None
        metrics = []
        downloads = []

        # Wait for the execution to complete. We explicitly wait in this method to keep the SDK free.
        complete = False

        while not complete:
            try:
                complete = execution.check_complete()
            except:
                # Execution must have failed. We want to carry on anyway.
                complete = True

            if not complete:
                sleep(Model._API_UPDATE_WAIT_PERIOD)

        # Now download the inputs and/or outputs.
        execution_dir = output_dir
        group_count = None
        group_index = None

        if hasattr(execution, Model._FIELD_GROUP_INDEX) and (execution.group_index is not None) and (not isinstance(execution.group_index, _Missing)) and hasattr(
                execution, Model._FIELD_GROUP_COUNT) and (execution.group_count is not None) and (not isinstance(execution.group_count, _Missing)):
            group_count = execution.group_count
            group_index = execution.group_index
            number_of_group_digits = len(str(group_count))
            execution_dir = os.path.join(output_dir, str(group_index).zfill(number_of_group_digits))
            os.makedirs(execution_dir)

        # Get the list of components and optionally include all those which are intermediate or in the component list.
        components = [
            component
            for component in execution.components
            if ((not component.intermediate) or (component.intermediate and download_intermediate)) and (
                    (len(download_components) <= 0) or
                    ((len(download_components) >= 1) and (component.name in download_components))
            )
        ]

        if (started_at is None) or (execution.started_at < started_at):
            started_at = execution.started_at

        if (ended_at is None) or (execution.ended_at > ended_at):
            ended_at = execution.ended_at

        for j, component in enumerate(components):
            # Download the component.
            component_name = '_'.join([item for item in re.sub(r'[\W]', '_', component.name).split('_') if len(item) > 0])
            component_dir = f"{str(j + 1)}_{component_name[:25]}"
            component_options = {item.get(Model._FIELD_NAME): item.get(Model._FIELD_VALUE) for item in component.options} if hasattr(component,
                                                                                                                                     Model._FIELD_OPTIONS) else {}

            # Save the metrics for each component in the execution.
            # @formatter:off
            metric = {
                Command._METRICS_EXECUTION: group_index if group_index is not None else 1,
                Command._METRICS_PROCESS: process.name,
                Command._METRICS_DURATION: ended_at - started_at if (started_at is not None) and (ended_at is not None) else 0,
                Command._METRICS_COMPONENT: component.name,
                Command._METRICS_SUCCESS: component.success,
                Command._METRICS_CPU: component.cpu,
                Command._METRICS_MEMORY: component.memory,
                Command._METRICS_RUNTIME: component.runtime
            }
            # @formatter:on

            # Only D-CAT services have metrics.
            s3_transfer_bytes = 0
            external_transfer_bytes = 0

            if hasattr(component, Command._METRICS_METRICS) and (component.metrics is not None):
                s3_transfer_bytes = sum(
                    [metric[Command._METRIC_S3_TRANSFER_BYTES] for metric in component.metrics if metric[Command._METRIC_S3_TRANSFER_BYTES] is not None])
                external_transfer_bytes = sum([metric[Command._METRIC_EXTERNAL_TRANSFER_BYTES] for metric in component.metrics if
                                               metric[Command._METRIC_EXTERNAL_TRANSFER_BYTES] is not None])

            metric[Command._METRIC_S3_TRANSFER_BYTES] = s3_transfer_bytes
            metric[Command._METRIC_EXTERNAL_TRANSFER_BYTES] = external_transfer_bytes

            # Find each input, output and storage to download. While traversing each, save the input and output size. The size might not be immediately available
            # for every file, so wait for all items to be analysed.
            data_items = []

            if download_inputs:
                data_items += [(k + 1, Command._DOWNLOAD_INPUT, data_item) for k, data_item in enumerate(component.inputs)]

            if download_outputs:
                data_items += [(k + 1, Command._DOWNLOAD_OUTPUT, data_item) for k, data_item in enumerate(component.outputs)]

            if download_storage:
                chain_index = component.chain_index if hasattr(component, Model._FIELD_CHAIN_INDEX) else None
                ssd_id = process.chains[chain_index].get(Model._FIELD_SSD_ID) if (chain_index is not None) and hasattr(process, Model._FIELD_CHAINS) and (
                        process.chains is not None) and (chain_index < len(process.chains)) else None
                storage_data_item = self.__get_storage_data_item(process, group_index, group_count, ssd_id, chain_index)

                if storage_data_item is not None:
                    data_items += [(1, Command._DOWNLOAD_STORAGE, storage_data_item)]

            input_sizes = []
            output_sizes = []

            for k, data_type, data_item in data_items:
                # Download the data item once it is complete.
                data_item.check_analysis_complete(wait=True)

                download_dir = os.path.join(execution_dir, component_dir, f"{data_type}_{str(k)}")
                os.makedirs(download_dir, exist_ok=True)

                # We also create the corresponding STAC definitions.
                stac_definitions = []

                for file in data_item.files:
                    path = os.path.join(download_dir, file.file_name)

                    # Download each file for the data item. We don't do anything with "storage".
                    if data_type == Command._DOWNLOAD_INPUT:
                        input_sizes.append(file.size)
                    elif data_type == Command._DOWNLOAD_OUTPUT:
                        output_sizes.append(file.size)

                    downloads.append((file, path))
                    stac_definitions.append(file.get_stac_item())

                stac_collection = data_item.get_stac_collection(stac_definitions, owner=component.name, created_at=component.created_at, detail=component_options)
                stac_definitions.append(stac_collection)

                # Write the STAC definitions.
                for stac_definition, stac_file_name in stac_definitions:
                    with open(os.path.join(download_dir, stac_file_name), 'w') as stac_file:
                        stac_file.write(json.dumps(stac_definition, default=json_default))

            metric[Command._METRIC_S3_INPUT_SIZE] = sum(input_sizes)
            metric[Command._METRIC_S3_OUTPUT_SIZE] = sum(output_sizes)
            metrics.append(metric)

        return downloads, metrics

    def __download_files(self, downloads):
        """
        Downloads the files from the downloads list.

        Args:
            downloads: A list of tuples with the file model and the download path.
        """
        downloads = [] if downloads is None else downloads

        if len(downloads) > 0:
            # Report progress.
            self.__print(logging.INFO, i18n.t('command.download_files', files=len(downloads)))
            progress_bar = tqdm(total=len(downloads), ncols=100)

            # Do all the downloads in batches. We use small batches so that we do not swamp memory.
            batch_size = 2 * os.cpu_count()  # Downloads don't swamp CPU.

            for batch in [downloads[i:i + batch_size] for i in range(0, len(downloads), batch_size)]:
                # Start downloading the batch.
                for file, path in batch:
                    file.download(path=path, wait=False)

                # Wait for the download to complete.
                for file, path in batch:
                    progress_bar.update(1)
                    file.download_complete(wait=True)

            progress_bar.close()

    def download_process_execution(self, organisation, process_name, download_inputs, download_outputs, download_storage, download_intermediate,
                                   download_components, save_metrics):
        """
        Downloads the inputs and/or outputs from a process or execution(s).

        Args:
            organisation: The logged in organisation.
            process_name: The name of the process to be downloaded. This can also be the id of a process or an execution.
            download_inputs: Should inputs be downloaded?
            download_outputs: Should outputs be downloaded?
            download_storage: Should storage be downloaded?
            download_intermediate: Should intermediate components be downloaded?
            download_components: The names of the components that should be downloaded? If None or [], then all components are downloaded.
            save_metrics: Save process metrics to file?

        Returns:
            The process model.
        """

        # If we are downloading nothing, at least download the outputs.
        if (not download_inputs) and (not download_outputs) and (not download_storage):
            download_outputs = True

        self.__print(logging.INFO,
                     i18n.t('command.download_process_execution', process=process_name, inputs=download_inputs, outputs=download_outputs, storage=download_storage,
                            intermediate=download_intermediate, metrics=save_metrics, components=download_components))

        # We are downloading from an existing process.
        process, execution = self.get_process_or_execution(organisation, process_name)

        # Get the output directory and remove it if it exists.
        output_dir = self.__process_name_to_file_name(process_name)
        shutil.rmtree(output_dir, ignore_errors=True)

        if execution is None:
            self.__print(logging.DEBUG, i18n.t('command.download_process', process=process.name, output=output_dir))
        else:
            self.__print(logging.DEBUG, i18n.t('command.download_execution', execution=execution.id, output=output_dir))

        # Get the corresponding execution(s) of the process. This is assumed to be the most recently started execution and/or group unless an execution id has been
        # specified.
        executions = None

        if execution is None:
            execution = next(process.executions, None)

            if execution is None:
                self.__print(logging.WARNING, i18n.t('command.no_executions', process=process.name))
                return None

            if hasattr(execution, Model._FIELD_GROUP_ID) and (execution.group_id is not None):
                _, executions = process.find_executions(group_id=execution.group_id)
                executions = [execution for execution in executions]

        if executions is None:
            executions = [execution]

        # Do all the downloads in batches. We use small batches so that we do not swamp memory.
        batch_size = 2 * os.cpu_count()  # Downloads don't swamp CPU.
        self.__print(logging.INFO, i18n.t('command.download_executions', executions=len(executions)))
        progress_bar = tqdm(total=len(executions), ncols=100)

        # Now download each execution in batches.
        partial_download_execution = partial(self.__download_execution, process, download_inputs, download_outputs, download_storage, download_intermediate,
                                             download_components, output_dir)
        results = []

        with Pool(nodes=batch_size) as pool:
            for result in pool.uimap(partial_download_execution, executions):
                progress_bar.update(1)
                results.append(result)

        progress_bar.close()

        # Combine the results.
        downloads = []
        metrics = []

        for execution_downloads, execution_metrics in results:
            downloads.extend(execution_downloads)
            metrics.extend(execution_metrics)

        # Download the files.
        self.__download_files(downloads)

        # Save the metrics to file.
        if save_metrics and (len(metrics) > 0):
            with open(Command._METRICS_FILE, 'w') as csv_file:
                writer = csv.DictWriter(csv_file, metrics[0].keys())
                writer.writeheader()
                writer.writerows(metrics)

        return process

    def extract_start_parameters(self, service_or_yaml, input_list, option_list):
        """
        Extracts the start parameters from either the command line arguments or the supplied YAML file.

        Args:
            service_or_yaml: Either a service name or a YAML file.
            input_list: The list of inputs.
            option_list: The list of options.

        Returns:
            The service name, process name, input files, storage_files, options and dispatchers.
        """

        yaml_file = None
        service_name = None
        process_name = None
        input_files = []
        storage_files = {}
        options = {}
        dispatchers = None

        # See if a YAML file is being used.
        extension = os.path.splitext(service_or_yaml)[1]

        if (len(extension) > 0) and (extension == Command._YAML_EXTENSION):
            # Load the YAML file.
            with open(service_or_yaml, 'r') as stream:
                yaml_file = yaml.safe_load(stream)

        # Extract the service name, input files, storage_files and options.
        if yaml_file is None:
            service_name = service_or_yaml
            input_files = input_list
            option_arguments = option_list if option_list is not None else []

            for option_argument in option_arguments:
                elements = option_argument.split('=')
                options[elements[0]] = elements[1]
        else:
            service_name = yaml_file.get(Command._YAML_SERVICE_NAME)
            process_name = yaml_file.get(Command._YAML_PROCESS_NAME)  # Optional in the YAML file.
            input_files = yaml_file.get(Command._YAML_INPUTS)
            storage_files = yaml_file.get(Command._YAML_STORAGE)  # Optional in the YAML file.
            options = yaml_file.get(Command._YAML_OPTIONS) or {}  # Optional in the YAML file.
            dispatchers = yaml_file.get(Command._YAML_DISPATCHERS) or []  # Optional in the YAML file.

        # Convert any values which use keyword replacement.
        process_name = self.__replace_keywords(service_name, process_name)
        input_files = self.__replace_keywords(service_name, input_files)
        storage_files = self.__replace_keywords(service_name, storage_files)
        options = self.__replace_keywords(service_name, options)
        dispatchers = self.__replace_keywords(service_name, dispatchers)

        return service_name, process_name, input_files, storage_files, options, dispatchers

    def __format_value(self, value, data_type=None):
        """
        Formats the value according to its data type.

        Args:
            value: The value to format.
            data_type: The optional data type. Either one of "boolean", "string", "numeric", "currency", "datetime", "constrained". If None, use the value's class.

        Returns:
            The formatted value.
        """
        if value is None:
            return value

        formatted = value

        # Format the value based upon its stated data type.
        if (data_type == fusion_platform.DATA_TYPE_BOOLEAN) or ((data_type is None) and isinstance(value, bool)):
            formatted = value
        elif (data_type == fusion_platform.DATA_TYPE_STRING) or (data_type == fusion_platform.DATA_TYPE_CONSTRAINED) or (
                (data_type is None) and isinstance(value, str)):
            formatted = value
        elif (data_type == fusion_platform.DATA_TYPE_NUMERIC) or (data_type == fusion_platform.DATA_TYPE_CURRENCY) or (
                (data_type is None) and (isinstance(value, int) or isinstance(value, float) or isinstance(value, Decimal))):
            formatted = value
        elif (data_type == fusion_platform.DATA_TYPE_DATETIME) or ((data_type is None) and isinstance(value, datetime)):
            formatted = value.isoformat()
        elif (data_type is None) and isinstance(value, relativedelta):
            dictionary = {'years': value.years, 'months': value.months, 'days': value.days, 'leapdays': value.leapdays, 'weeks': 0, 'hours': value.hours,
                          'minutes': value.minutes, 'seconds': value.seconds, 'microseconds': value.microseconds, 'year': value.year, 'month': value.month,
                          'day': value.day, 'weekday': value.weekday, 'hour': value.hour, 'minute': value.minute, 'second': value.second,
                          'microsecond': value.microsecond}  # Weeks is a pseudo-field, so we ignore it.

            formatted = json.dumps(dictionary)

        return formatted

    def __get_input(self, input_prompt, is_password=False, default=None, constrained_values=None):
        """
        Gets an input from the user.

        Args:
            input_prompt: The user prompt.
            is_password: Whether this is a password prompt or not.
            default: The optional default value.
            constrained_values: The optional constrained values.

        Returns:
            The user response.
        """
        default = constrained_values[0] if (default is None) and (constrained_values is not None) and (len(constrained_values) > 0) else default
        input_prompt = f"{input_prompt}{' [' + default + ']' if default is not None else ''}: "
        constrained_values = [''] + constrained_values if constrained_values is not None else constrained_values

        # Set up any validation against constrained values.
        partial_validate_constrained = partial(self.__validate_constrained, constrained_values)
        parameters = {'is_password': is_password}

        # See if we have constraints, so that we add in a validator and completer to make life easier.
        if constrained_values is not None:
            validator = Validator.from_callable(partial_validate_constrained,
                                                error_message=i18n.t('command.validate_constrained_error', constrained=constrained_values), move_cursor_to_end=True)
            completer = WordCompleter(constrained_values)
            parameters = {'completer': completer, 'complete_while_typing': True, 'validator': validator, 'validate_while_typing': False}

        # Prompt the user. This will enforce any constrained values.
        response = prompt(input_prompt, **parameters)

        return response or default

    def get_process_or_execution(self, organisation, process_name):
        """
        Attempts to find a process or execution using the given process name, process id or execution id.

        Args:
            organisation: The logged in organisation.
            process_name: The name of the process to be downloaded. This can also be the id of a process or an execution.

        Returns:
            The found process and/or execution.
        """

        # Attempt to find the process.
        process, _ = organisation.find_processes(name=process_name)
        execution = None

        if process is None:
            # Try a process or execution id instead.
            for process_to_check in organisation.processes:
                if str(process_to_check.id) == process_name:
                    process = process_to_check
                else:
                    for execution_to_check in process_to_check.executions:
                        if str(execution_to_check.id) == process_name:
                            process = process_to_check
                            execution = execution_to_check

        if process is None:
            raise CommandError(i18n.t('command.no_such_process', process=process_name))

        return process, execution

    def __get_storage_data_item(self, process, group_index, group_count, ssd_id, chain_index):
        """
        Gets the storage date item for a process' group and chain index.

        Args:
            process: The process for which the storage item is to be obtained.
            group_index: The group index within the sliced executions. When not sliced, this must be None.
            group_count: The count of non-aggregator executions in the group. When not sliced, this must be None.
            ssd_id: The SSD id of the service the storage belongs to.
            chain_index: The sequence of the SSD id within the execution.

        Returns:
            The storage data item if found. Otherwise, None.
        """
        storage_data_item = None

        # Get the storage data identifier for this component within the process. Note that it might not exist.
        storage_id = self.__get_storage_id(
            process.id,
            None if group_count == 1 else group_index,  # If not in a group, then this needs to be None.
            None if group_count == 1 else group_count,  # If not in a group, then this needs to be None.
            ssd_id,
            chain_index
        ) if ssd_id is not None else None

        if storage_id is not None:
            try:
                storage_data_item = Data._model_from_api_id(process._session, organisation_id=process.organisation_id, data_id=storage_id)
            except:
                pass  # There is no storage item.

        return storage_data_item

    def __get_storage_id(self, process_id, group_index, group_count, ssd_id, chain_index):
        """
        Gets the storage id for a process' constituent execution. This must match to the same calculation in the engine ProcessExecutionJob#__allocate_storage.

        Args:
            process_id: The process identifier.
            group_index: The group index within the sliced executions. When not sliced, this must be None.
            group_count: The count of non-aggregator executions in the group. When not sliced, this must be None.
            ssd_id: The SSD id of the service the storage belongs to.
            chain_index: The sequence of the SSD id within the execution.

        Returns:
            The calculated storage id.
        """
        return uuid.uuid5(uuid.NAMESPACE_URL, f"{process_id}_{group_count}_{group_index}_{ssd_id}_{chain_index}")

    def login(self, deployment, email, organisation_name):
        """
        Logs into the desired Fusion Platform(r) deployment and allows the user to select an organisation.

        Args:
            deployment: The deployment to use.
            email: The optional email address used to login. If not provided, the email will be prompted for.
            organisation_name: The optional organisation name. If not provided, the organisation will be prompted for.

        Returns:
            The selected organisation and its corresponding stage name and region.
        """

        # Which API deployment?
        deployment = deployment.lower()
        stage = Command.DEPLOYMENTS[deployment][Command._DEPLOYMENT_KEY_STAGE]
        region = Command.DEPLOYMENTS[deployment][Command._DEPLOYMENT_KEY_REGION]

        # Login with email address and password. We retry the email and password up to three times.
        count = 0

        while True:
            if email is None:
                email = self.__get_input(i18n.t('command.email'), default=email)

            password = self.__get_input(i18n.t('command.password'), is_password=True)

            try:
                user = fusion_platform.login(email=email, password=password, api_url=Command.DEPLOYMENTS[deployment]['url'])
                break
            except RequestError as e:
                count += 1

                # Cope with finger trouble.
                if (i18n.t('command.invalid_login_response') not in str(e)) or (count >= 3):
                    raise

        # Get the list of organisation names the user belongs to if the organisation is not provided.
        if organisation_name is None:
            organisation_names = [(item.name, item.updated_at) for item in user.organisations]
            organisation_names = [item[0] for item in sorted(organisation_names, key=lambda item: item[0])]

            # Select the organisation.
            organisation_name = self.__get_input(i18n.t('command.organisation'), constrained_values=organisation_names)

        organisation, _ = user.find_organisations(name=organisation_name)

        if organisation is None:
            raise CommandError(i18n.t('command.no_such_organisation', organisation=organisation_name))

        self.__print(logging.DEBUG, i18n.t('command.using_organisation', organisation=organisation.name))

        return organisation, stage, region

    def main(self):
        """
        Main entry point for the command line tool. This method overrides the superclass method.
        """

        # Parse the arguments.
        arguments = self.__parse_arguments()

        # Change the print and logging to the desired level.
        self._logger.setLevel(logging.CRITICAL)

        if arguments.debug:
            self.__print_level = logging.DEBUG
        else:
            self.__print_level = logging.INFO

        try:
            # Login to the correct deployment and select the organisation.
            organisation, _, _ = self.login(arguments.deployment, arguments.email, arguments.organisation)

            # Perform the start, define or download.
            if arguments.command == i18n.t('command.start.command'):
                # Start one or more processes.
                for service_or_yaml in arguments.service_or_yaml:
                    # Extract the command line or YAML file arguments.
                    service_name, process_name, input_files, storage_files, options, dispatchers = self.extract_start_parameters(service_or_yaml,
                                                                                                                                 arguments.input_list,
                                                                                                                                 arguments.options)

                    # Start the process.
                    process_name = f"{service_name} {datetime.now(timezone.utc)}" if process_name is None else process_name
                    process = self.start_process(organisation, service_name, process_name, input_files, storage_files, options, dispatchers,
                                                 arguments.download or arguments.wait_for_start)
                    self.__print_process(process)

                    # Also perform the download, if required.
                    if arguments.download:
                        process = self.download_process_execution(organisation, process_name, arguments.inputs, arguments.outputs, arguments.storage,
                                                                  arguments.intermediate, arguments.component, arguments.metrics)

                        # And optionally remove the process and its inputs.
                        if arguments.remove:
                            self.remove_process_and_inputs(organisation, process)

            elif arguments.command == i18n.t('command.define.command'):
                # Define one or more processes as YAML files.
                for process_name in arguments.process:
                    # Get the process definition, optionally downloading the inputs and storage to the current directory as well.
                    process_definition = self.define_process(organisation, process_name, download_inputs=arguments.inputs, download_storage=arguments.storage)

                    # Write the YAML to file. This will overwrite the existing file.
                    file_name = f"{self.__process_name_to_file_name(process_name)}{Command._YAML_EXTENSION}"

                    with open(file_name, 'w') as file:
                        yaml.dump(process_definition, file, sort_keys=False, width=float('inf'))

            elif arguments.command == i18n.t('command.download.command'):
                # Download one or more processes.
                for process_name in arguments.process:
                    # Download the process.
                    process = self.download_process_execution(organisation, process_name, arguments.inputs, arguments.outputs, arguments.storage,
                                                              arguments.intermediate, arguments.component, arguments.metrics)

                    # And optionally remove the process and its inputs.
                    if arguments.remove:
                        self.remove_process_and_inputs(organisation, process)

            else:
                # Unknown command.
                raise CommandError(i18n.t('command.unknown_command', command=arguments.command))

        except KeyboardInterrupt:
            exit(0)  # We just want to exit without any stack trace.

        except CommandError as e:
            self.__print(logging.ERROR, str(e))
            exit(1)  # We want to exit with an error status.

    def __parse_arguments(self):
        """
        Parses the command line arguments.

        :return: The parsed arguments.
        """

        parser = argparse.ArgumentParser(
            formatter_class=RawTextHelpFormatter,
            prog=i18n.t('command.program'),
            description=i18n.t('command.description'),
            epilog=i18n.t('command.epilog')
        )

        # Create the subparsers.
        subparsers = parser.add_subparsers(help=i18n.t('command.subparser'), dest='command')
        parser.add_argument(i18n.t('command.version_short'), i18n.t('command.version_long'), help=i18n.t('command.version_help'), action='version',
                            version=i18n.t('command.version_content', version=fusion_platform.__version__, version_date=fusion_platform.__version_date__))

        subparsers.required = True
        parser_start = subparsers.add_parser(i18n.t('command.start.command'), help=i18n.t('command.start.help'))
        parser_define = subparsers.add_parser(i18n.t('command.define.command'), help=i18n.t('command.define.help'))
        parser_download = subparsers.add_parser(i18n.t('command.download.command'), help=i18n.t('command.download.help'))

        # Add in the common arguments.
        for subparser in [parser_start, parser_define, parser_download]:
            subparser.add_argument(i18n.t('command.deployment_short'), i18n.t('command.deployment_long'), help=i18n.t('command.deployment_help'),
                                   default=Command._DEPLOYMENT_PRODUCTION_IRL)
            subparser.add_argument(i18n.t('command.email_short'), i18n.t('command.email_long'), help=i18n.t('command.email_help'))
            subparser.add_argument(i18n.t('command.organisation_short'), i18n.t('command.organisation_long'), help=i18n.t('command.organisation_help'))
            subparser.add_argument(i18n.t('command.debug_short'), i18n.t('command.debug_long'), help=i18n.t('command.debug_help'), default=False,
                                   action="store_true")

        # Start arguments.
        parser_start.add_argument(i18n.t('command.start.definition_long'), help=i18n.t('command.start.definition_help'), nargs='+')
        parser_start.add_argument(i18n.t('command.start.input_list_short'), i18n.t('command.start.input_list_long'), help=i18n.t('command.start.input_list_help'),
                                  nargs='*')
        parser_start.add_argument(i18n.t('command.start.options_short'), i18n.t('command.start.options_long'), help=i18n.t('command.start.options_help'), nargs='*')
        parser_start.add_argument(i18n.t('command.start.wait_for_start_short'), i18n.t('command.start.wait_for_start_long'),
                                  help=i18n.t('command.start.wait_for_start_help'), default=False, action="store_true")
        parser_start.add_argument(i18n.t('command.start.download_short'), i18n.t('command.start.download_long'), help=i18n.t('command.start.download_help'),
                                  default=False, action="store_true")
        parser_start.add_argument(i18n.t('command.start.remove_short'), i18n.t('command.start.remove_long'), help=i18n.t('command.start.remove_help'),
                                  default=False, action="store_true")
        parser_start.add_argument(i18n.t('command.start.inputs_short'), i18n.t('command.start.inputs_long'), help=i18n.t('command.start.inputs_help'),
                                  default=False, action="store_true")
        parser_start.add_argument(i18n.t('command.start.outputs_short'), i18n.t('command.start.outputs_long'), help=i18n.t('command.start.outputs_help'),
                                  default=False, action="store_true")
        parser_start.add_argument(i18n.t('command.start.storage_short'), i18n.t('command.start.storage_long'), help=i18n.t('command.start.storage_help'),
                                  default=False, action="store_true")
        parser_start.add_argument(i18n.t('command.start.intermediate_short'), i18n.t('command.start.intermediate_long'),
                                  help=i18n.t('command.start.intermediate_help'), default=False, action="store_true")
        parser_start.add_argument(i18n.t('command.start.metrics_short'), i18n.t('command.start.metrics_long'), help=i18n.t('command.start.metrics_help'),
                                  default=False, action="store_true")
        parser_start.add_argument(i18n.t('command.start.component_short'), i18n.t('command.start.component_long'), help=i18n.t('command.start.component_help'),
                                  nargs='*')

        # Define arguments.
        parser_define.add_argument(i18n.t('command.define.process_long'), help=i18n.t('command.define.process_help'), nargs='+')
        parser_define.add_argument(i18n.t('command.start.inputs_short'), i18n.t('command.start.inputs_long'), help=i18n.t('command.start.inputs_help'),
                                   default=False, action="store_true")
        parser_define.add_argument(i18n.t('command.start.storage_short'), i18n.t('command.start.storage_long'), help=i18n.t('command.start.storage_help'),
                                   default=False, action="store_true")

        # Download arguments.
        parser_download.add_argument(i18n.t('command.download.process_long'), help=i18n.t('command.download.process_help'), nargs='+')
        parser_download.add_argument(i18n.t('command.start.inputs_short'), i18n.t('command.start.inputs_long'), help=i18n.t('command.start.inputs_help'),
                                     default=False, action="store_true")
        parser_download.add_argument(i18n.t('command.start.outputs_short'), i18n.t('command.start.outputs_long'), help=i18n.t('command.start.outputs_help'),
                                     default=False, action="store_true")
        parser_download.add_argument(i18n.t('command.start.storage_short'), i18n.t('command.start.storage_long'), help=i18n.t('command.start.storage_help'),
                                     default=False, action="store_true")
        parser_download.add_argument(i18n.t('command.start.remove_short'), i18n.t('command.start.remove_long'), help=i18n.t('command.start.remove_help'),
                                     default=False, action="store_true")
        parser_download.add_argument(i18n.t('command.start.intermediate_short'), i18n.t('command.start.intermediate_long'),
                                     help=i18n.t('command.start.intermediate_help'), default=False, action="store_true")
        parser_download.add_argument(i18n.t('command.start.metrics_short'), i18n.t('command.start.metrics_long'), help=i18n.t('command.start.metrics_help'),
                                     default=False, action="store_true")
        parser_download.add_argument(i18n.t('command.start.component_short'), i18n.t('command.start.component_long'), help=i18n.t('command.start.component_help'),
                                     nargs='*')

        return parser.parse_args()

    def __print(self, level, message, format=True, **kwargs):
        """
        Prints a message to the console. This works much the same was a log message.

        Args:
            level: Same as logging constants.
            message: The message to print, as per a log message.
            format: Format the message to fill in placeholders from the keyword arguments? Default True.
            kwargs: The associated key word arguments.
        """
        if level >= self.__print_level:
            if format:
                print(message.format(**kwargs))
            else:
                print(message)

    def __print_process(self, process):
        """
        Prints a process.

        Args:
            process: The process to be logged.
        """
        self.__print(logging.INFO, i18n.t('command.log_bookend'))
        self.__print(logging.INFO, i18n.t('command.log_process', process=process.name))

        for field in Command._MODEL_FIELDS:
            if hasattr(process, field):
                self.__print(logging.INFO, i18n.t('command.log_field', field=field, value=getattr(process, field)))

        self.__print(logging.INFO, i18n.t('command.log_divider'))
        self.__print(logging.INFO, i18n.t('command.log_inputs'))

        for data_item in process.inputs:
            self.__print(logging.INFO, str(data_item), format=False)

        self.__print(logging.INFO, i18n.t('command.log_divider'))
        self.__print(logging.INFO, i18n.t('command.log_options'))

        for option in process.options:
            self.__print(logging.INFO, str(option), format=False)

        self.__print(logging.INFO, i18n.t('command.log_divider'))
        self.__print(logging.INFO, i18n.t('command.log_dispatchers'))

        for dispatcher in process.dispatchers:
            self.__print(logging.INFO, i18n.t('command.log_subdivider'))
            self.__print(logging.INFO, str(dispatcher), format=False)

            for option in dispatcher.options:
                self.__print(logging.INFO, str(option), format=False)

        self.__print(logging.INFO, i18n.t('command.log_bookend'))

    def __process_name_to_file_name(self, process_name):
        """
        Converts a process name into a same file name (without extension).

        Args:
            process_name: The process name to convert.

        Returns:
            The corresponding file name.
        """
        return re.sub(r"[^A-Za-z0-9._\-]", '_', str(process_name)) if process_name is not None else None

    def remove_process_and_inputs(self, organisation, process):
        """
        Removes the process and its inputs.

        Args:
            organisation: The logged in organisation.
            process: The process to be removed.
        """

        # Find all the processes inputs. We do this before we remove the process.
        inputs = []

        for input in process.inputs:
            # Get the data item for this input.
            data, _ = organisation.find_data(id=input.id)

            if data is not None:
                inputs.append(data)

        # Now remove the process. This will free up the inputs to be removed.
        self.__print(logging.INFO, i18n.t('command.remove_process', process=process.name))
        process.delete()

        # Finally delete the inputs.
        for input in inputs:
            self.__print(logging.INFO, i18n.t('command.remove_input', input=input.name))
            input.delete()

    def __replace_keywords(self, service_name, value):
        """
        Recursively replaces any keywords which are found in the value.

        Args:
            service_name: The name of the service for use in keyword replacement.
            value: The value to be modified.

        Returns:
            The modified value.
        """
        modified = deepcopy(value)

        if isinstance(modified, str):
            partial_replacer = partial(self.__replacer, service_name)
            modified = re.sub(r'\{(.*)\}', partial_replacer, modified, re.DOTALL)

        elif isinstance(modified, list):
            for i, item in enumerate(modified):
                modified[i] = self.__replace_keywords(service_name, item)

        elif isinstance(modified, dict):
            for key, item in modified.items():
                modified[key] = self.__replace_keywords(service_name, item)

        return modified

    def __replacer(self, service_name, match):
        """
        Called when a keyword match has been found to replace the match with the corresponding keyword.

        Args:
            service_name: The service name to use in any service name replacement.
            match: The match found.

        Returns:
            The modified content for the match.
        """
        replacement = None

        # Extract the keyword and optional modifier.
        original_content = match.group()[1:-1]
        content = original_content.split('@')
        keyword = content[0].lower()
        modifier = content[-1] if len(content) > 1 else ''

        if len(keyword) > 0:
            # We have a keyword, so replace it.
            if keyword == Command._KEYWORD_SERVICE_NAME:
                replacement = service_name

            elif keyword == Command._KEYWORD_NOW:
                replacement = datetime.now(timezone.utc).isoformat()

            elif keyword in self.__keyword_day_names:
                hour = 0
                minute = 0

                if len(modifier) > 0:
                    content = modifier.split(':')
                    hour = int(content[0])
                    minute = int(content[-1]) if len(content) > 1 else 0

                replacement = datetime(self.__keyword_day_names[keyword].year, self.__keyword_day_names[keyword].month, self.__keyword_day_names[keyword].day,
                                       hour=hour, minute=minute, tzinfo=timezone.utc).isoformat()

            else:
                # An unknown keyword. Make sure we just put everything back as it was, with the keyword markers.
                replacement = f"{{{original_content}}}"

        return replacement

    def start_process(self, organisation, service_name, process_name, input_files, storage_files, options, dispatchers, wait_for_start):
        """
        Starts a new process based upon the service, inputs, options and dispatchers.

        Args:
            organisation: The logged in organisation.
            service_name: The name of the service from which the process will be created.
            process_name: The name of the process.
            input_files: The list of input files to be uploaded or pre-existing input names.
            storage_files: The list of storage files to be uploaded.
            options: The list of options.
            dispatchers: The list of dispatchers.
            wait_for_start: Wait for the process to start?

        Returns:
            The process model.
        """
        self.__print(logging.INFO, i18n.t('command.start_process', process=process_name, service=service_name))

        # Upload the inputs.
        if (input_files is not None) and (len(input_files) > 0):
            data_items = self.__upload_or_find_inputs(organisation, process_name, input_files)
        else:
            data_items = []

        # Find the service using its case-sensitive name (starts with).
        service, _ = organisation.find_services(name=service_name)

        # If the service cannot be found, then try it as a specific service for the organisation.
        if service is None:
            service = next((item for item in organisation.own_services if item.name == service_name), None)

        if service is None:
            raise CommandError(i18n.t('command.no_such_service', service=service_name))

        self.__print(logging.DEBUG, i18n.t('command.using_service', service=service.name))

        # Create the process with its options and inputs.
        process = self.__create_process(organisation, process_name, options, dispatchers, service, data_items)

        # Upload the optional storage data items now that the process has been created because we need the process id.
        if (storage_files is not None) and (len(storage_files) > 0):
            self.__upload_storage(organisation, storage_files, process)

        # Now execute the process, but do not wait for it to complete.
        self.__print(logging.INFO, i18n.t('command.executing'))
        process.execute(wait=False)

        if wait_for_start:
            # Wait for the next execution to start.
            self.__print(logging.DEBUG, i18n.t('command.wait_for_next'))
            process.wait_for_next_execution()

        return process

    def __upload_or_find_inputs(self, organisation, process_name, input_files):
        """
        Uploads or finds the inputs ready to start a process.

        Args:
            organisation: The logged in organisation.
            process_name: The name of the process.
            input_files: The list of input files to be uploaded or pre-existing input names to be found.

        Returns:
            The found data items in the same order as the input files.
        """
        data_items = []
        created_items = []

        self.__print(logging.INFO, i18n.t('command.upload_inputs', files=len(input_files)))
        progress_bar = tqdm(total=len(input_files), ncols=100)

        try:
            for i, input_file in enumerate(input_files if input_files is not None else []):
                # The input file can either be a string representing a name or a file, or a dictionary with explicit values for both.
                input_name = None
                filename = None
                extension = None

                if isinstance(input_file, dict):
                    input_name = input_file.get(Model._FIELD_NAME)
                    filename = input_file.get(Model._FIELD_FILE)
                    extension = os.path.splitext(filename.lower())[1]
                else:
                    # An input name is not assumed to have an extension.
                    extension = os.path.splitext(input_file.lower())[1]

                    if len(extension) > 0:
                        filename = input_file
                    else:
                        input_name = input_file
                        extension = None

                if extension is not None:
                    # Create a data item for each input.
                    if (extension == '.tif') or (extension == '.tiff'):
                        file_type = fusion_platform.FILE_TYPE_GEOTIFF
                    elif extension == '.jp2':
                        file_type = fusion_platform.FILE_TYPE_JPEG2000
                    elif extension == '.dem':
                        file_type = fusion_platform.FILE_TYPE_DEM
                    elif (extension == '.json') or (extension == '.geojson'):
                        file_type = fusion_platform.FILE_TYPE_GEOJSON
                    elif extension == '.kml':
                        file_type = fusion_platform.FILE_TYPE_KML
                    elif extension == '.kmz':
                        file_type = fusion_platform.FILE_TYPE_KMZ
                    elif extension == '.csv':
                        file_type = fusion_platform.FILE_TYPE_CSV
                    elif extension == '.zip':
                        file_type = fusion_platform.FILE_TYPE_ESRI_SHAPEFILE
                    elif (extension == '.jpeg') or (extension == '.jpg'):
                        file_type = fusion_platform.FILE_TYPE_JPEG
                    elif extension == '.png':
                        file_type = fusion_platform.FILE_TYPE_PNG
                    else:
                        file_type = fusion_platform.FILE_TYPE_OTHER

                    input_name = f"{process_name} {i + 1}" if input_name is None else input_name
                    created = organisation.create_data(name=input_name, file_type=file_type, files=[filename], wait=False)
                    data_items.append(created)
                    created_items.append(created)
                else:
                    data_item, _ = organisation.find_data(name=input_name)

                    if data_item is None:
                        raise CommandError(i18n.t('command.no_such_input', input_name=input_name))

                    data_items.append(data_item)
                    progress_bar.update(1)

            # Wait for the analysis of any created items to complete.
            for created in created_items:
                created.create_complete(wait=True)
                progress_bar.update(1)

        finally:
            progress_bar.close()

        return data_items

    def __upload_storage(self, organisation, storage_files, process):
        """
        Uploads the storage files for a new process.

        Args:
            organisation: The logged in organisation.
            storage_files: The list of storage files to be uploaded.
            process: The newly created process.
        """
        created_items = []

        self.__print(logging.INFO, i18n.t('command.upload_storage', files=len(storage_files)))
        progress_bar = tqdm(total=len(storage_files), ncols=100)

        try:
            for storage_key, storage_file in (storage_files if storage_files is not None else {}).items():
                # The key represents the values used to generate the new storage id, without the process id, which will be different.
                elements = storage_key.split('_')
                group_index = int(elements[0])
                group_count = int(elements[1])
                ssd_id = elements[2]
                chain_index = int(elements[3])
                storage_name = i18n.t('command.storage_name', process=process.name, group_index=group_index, chain_index=chain_index)

                group_index = None if group_count == 1 else group_index  # If not in a group, then this needs to be None.
                group_count = None if group_count == 1 else group_count  # If not in a group, then this needs to be None.
                storage_id = self.__get_storage_id(process.id, group_index, group_count, ssd_id, chain_index)

                # The destination filename must be correct for everything to work, so we must make a copy with the right name.
                with tempfile.TemporaryDirectory() as tmp_dir:
                    upload_file = os.path.join(tmp_dir, Command._STORAGE_NAME)
                    shutil.copy(storage_file, upload_file)

                    created = organisation.create_data(name=storage_name, file_type=fusion_platform.FILE_TYPE_GZIP, files=[upload_file], wait=False, id=storage_id)
                    created_items.append(created)

                    os.remove(upload_file)

            # Wait for the analysis of any created items to complete.
            for created in created_items:
                created.create_complete(wait=True)
                progress_bar.update(1)

        finally:
            progress_bar.close()

    def __validate_constrained(self, values, text):
        """
        Validates a constrained value. All are assumed to be lowercase.

        Args:
            values: The allowed list of constrained values.
            text: The text to validate.

        Returns:
            True if the text is valid.
        """
        return text.lower() in [value.lower() for value in values]


def main():
    """
    Main entry point for command line.
    """
    Command().main()


if __name__ == "__main__":
    main()
