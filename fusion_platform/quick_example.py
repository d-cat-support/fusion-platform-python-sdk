"""
Quick example file.

author: Matthew Casey

&copy; [Digital Content Analysis Technology Ltd](https://www.d-cat.co.uk)
"""

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
