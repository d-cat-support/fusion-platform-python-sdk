* **id**: The unique identifier for the record.
* **created_at**: When was the record created?
* **updated_at**: When was the record last updated?
* **organisation_id**: The owning organisation.
* **name**: The name of the data item.
* **unlinked**: Is the data item unlinked from any other model and therefore not in use?
* **unfulfilled**: Indicates that the data item will never be used.
* **ingester_availability**: The optionally list of ingesters which can use this data item, and the associated dates for which data is available.
    * **ingester_id**: The ingester which can provide input for this data item.
    * **dates**: The list of dates for which data is available from this ingester.
* **bounds**: The longitude and latitude bounds for the file (west, south, east, north).
* **file_with_preview**: Identifies a file owned by this data item which as a preview.
* **uploaded_organisation_id**: Was the data item uploaded?
* **deletable**: Is this data model scheduled for deletion?
