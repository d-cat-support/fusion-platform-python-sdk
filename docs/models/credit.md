* **id**: The unique identifier for the record.
* **created_at**: When was the record created?
* **updated_at**: When was the record last updated?
* **organisation_id**: The owning organisation.
* **any_credits**: How many credits does the organisation have which can be used for anything?
* **cloud_storage_credits**: How many credits does the organisation have which can be used just for cloud storage?
* **registry_storage_credits**: How many credits does the organisation have which can be used just for registry storage?
* **runtime_any_credits**: How many credits does the organisation have which can be used just for runtime, but for any SSD?
* **runtime_ssds**: Specifies the credits available for specific SSDs.
    * **ssds**: The list of SSDs for which the corresponding credits apply.
    * **credits**: How many credits does the organisation have which can be used just for the corresponding list of credits?
