* **id**: The unique identifier for the record.
* **created_at**: When was the record created?
* **updated_at**: When was the record last updated?
* **organisation_id**: The owning organisation.
* **process_execution_id**: The specific execution of the process.
* **process_id**: The process executed.
* **service_id**: The explicit service version of the SSD which has been executed.
* **image_id**: The image which was executed.
* **chain_index**: The index in the processing chain for this executed service in the process.
* **name**: The name of the service which has been executed.
* **started_at**: When did the execution start?
* **ended_at**: When did the execution end?
* **runtime**: The execution runtime in seconds.
* **cpu**: The number of CPUs used to run the image.
* **memory**: The memory in megabytes used to run the image.
* **actions**: The custom actions associated with this execution.
    * **name**: The name of the value.
    * **values**: The values required for the action.
        * **name**: The name of the value.
        * **required**: Is the value required for the action?
        * **data_type**: The data type associated with the value.
        * **default**: The optional default value.
        * **validation**: The optional validation. This must be supplied for date/time and constrained values.
        * **constant**: Is this value constant and therefore cannot be changed?
        * **ssd_id**: The SSD from which this value is taken.
        * **output**: The output from the SSD being used for the value.
        * **selector**: The selector from the SSD output being used for the value.
        * **data_id**: The data item which has been output by the SSD to extract the value from.
        * **expression**: The expression used to calculate the value.
        * **value**: The actual value.
        * **url**: The URL which can be used to obtain the value.
        * **advanced**: Is this value for advanced usage?
        * **title**: The title for the value.
        * **description**: The description of the value.
    * **url**: The URL which can be executed to receive the value of the action.
    * **title**: The title for the action.
    * **description**: The description of the action.
* **options**: The options used by this execution.
    * **name**: The name of the option.
    * **value**: The value for the option.
    * **data_type**: The data type associated with the option.
    * **validation**: The optional validation for the option. This must be supplied for date/time and constrained values.
* **intermediate**: Is this an intermediate service?
* **success**: Has the execution completed successfully?
* **metrics**: Metrics recorded during the execution.
    * **date**: When was the metric recorded?
    * **memory_total_bytes**: The total memory in bytes.
    * **memory_free_bytes**: The free memory in bytes.
    * **swap_total_bytes**: The total swap space in bytes.
    * **swap_free_bytes**: The free swap space in bytes.
    * **tmp_total_bytes**: The total temporary disk space in bytes.
    * **tmp_free_bytes**: The free temporary disk space in bytes.
    * **s3_transfer_bytes**: The number of bytes transferred in from S3.
    * **gcs_transfer_bytes**: The number of bytes transferred in from Google Cloud Storage.
    * **external_transfer_bytes**: The number of bytes transferred in externally.
    * **internal_transfer_bytes**: The number of bytes transferred in internally.
    * **comment**: Any comment recorded with the metric.
