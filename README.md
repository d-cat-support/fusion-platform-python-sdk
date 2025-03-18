# Fusion Platform<sup>&reg;</sup> Python SDK

This package contains the Python SDK used to interact with the Fusion Platform<sup>&reg;</sup>. The Fusion Platform<sup>&reg;</sup> provides enhanced remote
monitoring services. By ingesting remotely sensed Earth Observation (EO) data, and data from other sources, the platform uses and fuses this data to execute
algorithms which provide actionable knowledge to customers.

The Python SDK is designed to enable interaction with the Fusion Platform<sup>&reg;</sup> via its API. As such, the SDK therefore allows software to login, upload
files, create and execute processes, monitor their execution and then download the corresponding results. Additional functionality is available directly via the
API, and this is defined within the corresponding OpenAPI 3.0 specification, which can be obtained via a support request.

[&copy; Digital Content Analysis Technology Ltd](https://www.d-cat.co.uk)

## Installation

The SDK has been built for Python 3, and is tested against Python 3.9, 3.10, 3.11, 3.12 and 3.13. To install the SDK into a suitable Python environment containing
`pip`, execute the following:

```shell
pip install fusion-platform-python-sdk
```

This will install the SDK and all its dependencies.

To update an existing installation to the latest version, execute the following:

```shell
pip install fusion-platform-python-sdk --upgrade
```

## Example

The following shows a simple example of how to use the SDK to create a process, execute it and download the resulting data. This example assumes that a suitable
user account has been created with an organisation which has sufficient credits to run the process, and that the SDK has been installed as above. To use a different
user account, replace the email address `me@org.com` and password `MyPassword123!`.

The example uses a pre-defined region of interest for Glasgow, and then obtains spectral indices for the region. A range of spectral indices are built using ESA's
Sentinel-2 multi-spectral data from the most recent date available for Glasgow.

```python
import os
import fusion_platform

# Login with email address and password.
user = fusion_platform.login(email='me@org.com', password='MyPassword123!')

# Select the organisation which will own the file. This is
# the first organisation the user belongs to in this example,
# and which is therefore assumed to have sufficient credits.
organisation = next(user.organisations)

# Create a data item for the Glasgow region of interest:
glasgow = organisation.create_data(name='Glasgow', file_type=fusion_platform.FILE_TYPE_GEOJSON, files=[fusion_platform.EXAMPLE_GLASGOW_FILE], wait=True)

# Find the elevation service.
service, _ = organisation.find_services(keyword='Elevation')

# Create a template process from the service.
process = organisation.new_process(name='Example', service=service)

# Configure the process to use Glasgow as the region.
process.update(input_number=1, data=glasgow)

# Create the process, which will validate its options and inputs.
process.create()

# Before execution, review the price in credits.
print(f"Price: {process.price}")

# Now execute the process and wait for it to complete.
process.execute(wait=True)

# Get the corresponding execution of the process. This is assumed
# to be the most recently started execution.
execution = next(process.executions)

# Now download all the outputs.
for i, component in enumerate(execution.components):
    print(f"Downloading {component.name}")
    component_dir = f"component_{str(i)}"

    for j, output in enumerate(component.outputs):
        dir = os.path.join(component_dir, str(j))
        for file in output.files:
            file.download(path=os.path.join(dir, file.file_name))

# Now tidy everything up by deleting the process and the region.
process.delete()
glasgow.delete()
```

## Documentation

Details of the methods and attributes available from objects used within the SDK can be
found [https://www.d-cat.co.uk/public/fusion_platform_python_sdk/](https://www.d-cat.co.uk/public/fusion_platform_python_sdk/).

Full documentation can be found
in [fusion_platform_sdk.pdf](https://github.com/d-cat-support/fusion-platform-python-sdk/blob/master/fusion_platform/fusion_platform_sdk.pdf).

## Support

Support for the SDK can be obtained by contacting Digital Content Analysis Technology Ltd via [support@d-cat.co.uk](mailto:support@d-cat.co.uk).

## License

See [LICENSE.txt](LICENSE.txt).