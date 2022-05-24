* **id**: The unique identifier for the record.
* **created_at**: When was the record created?
* **updated_at**: When was the record last updated?
* **name**: The unique name of the organisation
* **address_line_1**: The first line of the address.
* **address_line_2**: The second line of the address.
* **address_town_city**: The town or city.
* **address_post_zip_code**: The postal or zip code.
* **address_country**: The country.
* **payment_customer**: The payment customer reference from the payment service.
* **payment_valid**: Are the payment service details valid?
* **income_customer**: The income customer reference from the income service.
* **income_valid**: Are the income service details valid?
* **income_tax_rate**: The percentage tax to be applied to income.
* **income_tax_reference**: The income tax reference.
* **currency**: The currency to be used for payment and income.
* **users**: The list of users linked to this organisation.
    * **id**: The user identifier.
    * **email**: The user's email address.
    * **roles**: Assigned organisational roles.
* **agreed_licenses**: The list of licences agreed on behalf of the organisation.
* **offers**: The list of offers linked to this organisation.
* **maximum_output_storage_period**: The maximum period in days for this organisation for which an output can be stored before it is deleted.
* **maximum_file_downloads**: The maximum number of time any file can be downloaded for this organisation.
