* **id**: The unique identifier for the record.
* **created_at**: When was the record created?
* **updated_at**: When was the record last updated?
* **organisation_id**: The owning organisation.
* **name**: The name of the data item.
* **unlinked**: Is the file unlinked from any other model and therefore not in use?
* **ingester_availability**: The optionally list of ingesters which can use this data item, and the associated dates for which data is available.
    * **ingester_id**: The ingester which can provide input for this data item.
    * **dates**: The list of dates for which data is available from this ingester.
* **uploaded**: Was the data item uploaded?
* **deletable**: Is this data model scheduled for deletion?
