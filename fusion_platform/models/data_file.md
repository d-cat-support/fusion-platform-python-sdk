* **id**: The unique identifier for the record.
* **created_at**: When was the record created?
* **updated_at**: When was the record last updated?
* **organisation_id**: The owning organisation.
* **data_id**: The data item linked to this file record.
* **file_id**: The file associated with this data item.
* **preview_file_id**: The preview file associated with this data item.
* **file_type**: The type of file.
* **file_name**: The name of the file.
* **resolution**: For raster files, the resolution in metres.
* **crs**: The optional coordinate reference system for the file.
* **bounds**: The longitude and latitude bounds for the file (west, south, east, north).
* **area**: The optional total area covered by the file content in metres squared.
* **length**: The optional total length covered by the file content in metres.
* **points**: The optional total number of points in the file.
* **size**: The size of the file in bytes.
* **error**: Was there an error encountered during analysis of the file?
* **publishable**: Is the file suitable for publishing as it is without optimisation?
* **alternative**: The alternative file to use if this file is not publishable.
* **source**: If this file is an alternative created from a non-publishable file, then this specifies the source file.
* **selectors**: The selectors for the file.
    * **selector**: The selector to be applied to the file, such as the required raster band or data field.
    * **category**: The category associated with the selector.
    * **data_type**: The data type associated with the selector.
    * **unit**: The optional unit associated with the selector.
    * **validation**: The optional validation for the selector. This must be supplied for date/time and constrained values.
    * **area**: The optional area for the selector in metres squared.
    * **length**: The optional length for the selector in metres.
    * **points**: The optional total number of points in the selector.
    * **initial_values**: The first initial values associated with the selector.
    * **minimum**: The minimum value associated with the selector values.
    * **maximum**: The maximum value associated with the selector values.
    * **mean**: The mean value associated with the selector values.
    * **sd**: The standard deviation associated with the selector values.
    * **histogram_minimum**: The histogram maximum value associated with the selector values.
    * **histogram_maximum**: The histogram maximum value associated with the selector values.
    * **histogram**: The histogram associated with the selector values.
* **downloads**: How many times has the file been downloaded?
* **geojson**: The content of the associated file if it is a GeoJSON file (of limited size).
* **title**: The title for the selector.
* **description**: The description of the selector.
* **stac_item**: The STAC item associated with this file.
* **stac_item_file**: The name of the STAC item file.
