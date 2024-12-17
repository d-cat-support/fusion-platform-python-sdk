* **id**: The unique identifier for the record.
* **created_at**: When was the record created?
* **updated_at**: When was the record last updated?
* **organisation_id**: The owning organisation.
* **process_id**: The process executed.
* **group_id**: The optional group that this execution belongs to.
* **group_index**: The optional unique index for the execution within a group.
* **group_count**: The optional number of executions within a group.
* **options**: The options defined for this process execution.
    * **ssd_id**: The SSD for this option.
    * **name**: The name of the option.
    * **value**: The value for the option.
    * **required**: Is a value for the option required?
    * **data_type**: The data type associated with the selector.
    * **validation**: The optional validation for the option. This must be supplied for date/time and constrained values.
    * **mutually_exclusive**: The optional expression used by clients to determine whether this value is displayed compared with other option values.
    * **advanced**: Is this an option for advanced usage?
    * **title**: The title for the option.
    * **description**: The description of the option.
* **chains**: The processing chain of SSDs which will be executed for this process execution.
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
* **started_at**: When did the execution start?
* **ended_at**: When did the execution end?
* **stopped**: Has the execution been stopped by a user?
* **abort**: Has the execution been aborted?
* **abort_reason**: The reason for any abort of the execution.
* **exit_type**: The type of exit experienced by the execution.
* **success**: Has the execution completed successfully?
* **progress**: Percentage progress of the execution.
* **delete_expiry**: When will the execution expire and therefore be deleted?
* **delete_warning_status**: What is the notification status for the delete warning?
* **deletable**: Is this execution scheduled for deletion?
* **delete_protection**: Is this execution prevented from being deleted irrespective of its delete expiry?
