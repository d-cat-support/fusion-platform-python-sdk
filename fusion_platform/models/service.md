* **id**: The unique identifier for the record.
* **created_at**: When was the record created?
* **updated_at**: When was the record last updated?
* **organisation_id**: The owning organisation.
* **ssd_id**: The SSD for which this service is a version.
* **version**: The version number for the SSD that this service represents.
* **approval_status**: The approval status for this service.
* **featured**: Is this a featured service?
* **show_in_latest**: Should this service be listed in the list of latest versions of services?
* **name**: The name of the service.
* **categories**: The list of categories linked to this service.
* **keywords**: The list of keywords linked to this service.
* **image_id**: The image which forms the core of the service.
* **definition**: The service definition which links together this SSD with any other constituent SSD.
    * **ssd_id**: The SSD which is being linked into this service.
    * **output**: The output from the SSD being linked.
    * **linkages**: The list of linkages which consume the output.
        * **ssd_id**: The SSD which is being linked into this service.
        * **input**: The input to the SSD being linked.
* **group_aggregators**: The list of aggregators which are run when all executions in a group have completed.
    * **aggregator_ssd_id**: The SSD executed to aggregate the outputs from a group.
    * **output_ssd_id**: The SSD whose outputs are used by the aggregator.
    * **outputs**: The list of outputs from the output SSD used by the aggregator.
    * **options**: The options for this aggregator.
        * **ssd_id**: The SSD for this option.
        * **name**: The name of the option.
        * **value**: The value for the option.
* **actions**: The custom actions associated with the service.
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
        * **expression**: The expression used to calculate the value.
        * **value**: The actual value.
        * **url**: The URL which can be used to obtain the value.
        * **advanced**: Is this value for advanced usage?
        * **title**: The title for the value.
        * **description**: The description of the value.
    * **url**: The URL which can be executed to receive the value of the action.
    * **title**: The title for the action.
    * **description**: The description of the action.
* **urls**: The list of allowed external URLs the service can access.
* **cidrs**: The list of allowed external IP addresses as CIDRs the service can access.
* **input_expressions**: The list of expressions which are applied to the inputs of the service.
    * **lhs_ssd_id**: The SSD associated with the left-hand side of the input expression.
    * **lhs_input**: The input associated with the left-hand side of the input expression.
    * **expression**: The expression linking the left- and right-hand sides of the input expression.
    * **rhs_ssd_id**: The SSD associated with the right-hand side of the input expression.
    * **rhs_input**: The input associated with the right-hand side of the input expression.
* **input_validations**: The list of validation expressions which are applied to the inputs of the service.
    * **expression**: The expression used for validation.
    * **message**: The message associated with the validation which is used when the validation fails.
* **option_expressions**: The list of expressions which are applied to the options of the service.
    * **lhs_ssd_id**: The SSD associated with the left-hand side of the option expression.
    * **lhs_name**: The option name associated with the left-hand side of the option expression.
    * **expression**: The expression used to calculate the option value.
* **option_validations**: The list of validation expressions which are applied to the options of the service.
    * **expression**: The expression used for validation.
    * **message**: The message associated with the validation which is used when the validation fails.
* **license_id**: The license which must be agreed with in order to execute the service.
* **charge_expression_platform**: The expression used to calculate the charge in FPUs levied for the platform.
* **charge_expression_owner**: The expression used to calculate the charge in FPUs levied for the owner of the service.
* **organisations**: The optional whitelist of organisations who can use this service.
* **organisation_charge_expressions**: For the whitelisted organisations, these provide the optional charge expressions to be applied.
    * **id**: The owning organisation.
    * **platform**: The expression used to calculate the charge in FPUs levied for the platform.
    * **owner**: The expression used to calculate the charge in FPUs levied for the owner of the service.
* **geographic_regions**: The optional list of geographic regions from which this service can be used.
* **documentation_summary**: The documentation summary of the service.
* **documentation_description**: The documentation description of the service.
* **documentation_assumptions**: Any documented assumptions that underlie the service.
* **documentation_performance**: Notes on service performance.
* **documentation_actions**: The documentation for the custom actions for the service.
* **documentation_inputs**: The inputs to the service.
* **documentation_outputs**: The outputs from the service.
* **documentation_options**: The service options.
