* **id**: The unique identifier for the record.
* **created_at**: When was the record created?
* **updated_at**: When was the record last updated?
* **organisation_id**: The owning organisation.
* **ssd_id**: The SSD for which this process.
* **service_id**: The specific version of the SSD linked to this process.
* **name**: The name of the process.
* **chains**: The processing chain of SSDs which will be executed for this process.
    * **ssd_id**: The SSD for this part of the chain.
    * **service_id**: The corresponding specific version of the SSD.
    * **inputs**: The inputs to the service.
    * **outputs**: The outputs from the service.
    * **options**: The options from the service.
        * **name**: The name of the option.
        * **value**: The value for the option.
        * **data_type**: The data type associated with the option.
        * **validation**: The optional validation for the option. This must be supplied for date/time and constrained values.
    * **intermediate**: Is this an intermediate service within the chain?
* **run_type**: How will the process be executed?
* **repeat_count**: How many more repetitions of the process will there be?
* **repeat_start**: When will the process repetitions next occur?
* **repeat_end**: When will the process repetitions stop?
* **repeat_gap**: How much time is there between repeated processes?
* **repeat_offset**: At what offset from the repeat start will the process run?
* **process_status**: The process status.
* **process_status_at**: When was the process status changed?
* **process_status_changed_by**: Who changed the process status?
* **output_storage_period**: The number of days that outputs should be stored after execution before they are automatically deleted.
* **test_run**: Is this a test run of a service?
* **price**: The price in FPUs to execute this process given its inputs and options.
* **deletable**: Is this process scheduled for deletion?
* **non_aggregator_count**: The count of non-aggregator executions within the current or last execution.
* **aggregator_count**: The count of aggregator executions within the current or last execution.
