"""
Detailed example file.

author: Matthew Casey

&copy; [Digital Content Analysis Technology Ltd](https://www.d-cat.co.uk)
"""

from datetime import datetime, timezone
import rasterio
from rasterio.merge import merge
import matplotlib.pyplot as pyplot
import pandas

import fusion_platform

# Login with email address and password.
user = fusion_platform.login(email='me@org.com', password='MyPassword123!')

# Select the organisation which will own the file. This is
# the first organisation the user belongs to in this example,
# and which is therefore assumed to have sufficient credits.
organisation = next(user.organisations)

# Create a data item for the Lake District region of interest:
lake_district = organisation.create_data(
    name='Lake District National Park', file_type=fusion_platform.FILE_TYPE_GEOJSON, files=[fusion_platform.EXAMPLE_LAKE_DISTRICT_FILE], wait=True)

# Find the cloud classification service using its name.
service, _ = organisation.find_services(
    name='Demo: Sentinel-2 Cloud Classification')

# Create a template process from the service.
process = organisation.new_process(name='Example', service=service)

# Configure the process to use Lake District National Park
# as the region of interest.
process.update(input_number=1, data=lake_district)

# Configure the service to work on historic data.
process.update(option_name='latest_date', value=False)
process.update(option_name='start_date',
               value=datetime(2021, 3, 27, tzinfo=timezone.utc))
process.update(option_name='end_date', value=None)

# Create the process, review its price, then execute it.
process.create()
print(f"Price: {process.price}")
process.execute(wait=True)

# Because the Lake District region of interest is relatively
# large, the process will be executed in a group, so find all of
# the executions in the group. These are assumed to be the most
# recently started group obtained from the last execution.
execution = next(process.executions)
_, executions = process.find_executions(
    group_id=execution.group_id)

# Download the cloud classification output for each execution
# together with the aggregated statistics. We also keep the
# metadata for each raster file.
files = []
selectors = []
statistics_path = None
raster_paths = []

for i, execution in enumerate(executions):
    for component in execution.components:
        # Download the aggregated statistics and classification.
        if component.name == 'Statistics Aggregator':
            print(f"Downloading statistics from {component.id}")
            output = next(component.outputs)
            file = next(output.files)  # First file only.
            files.append(file)
            statistics_path = file.file_name
            file.download(path=statistics_path)

        elif component.name == 'Sentinel-2 Cloud Classification':
            print(f"Downloading output from {component.id}")
            output = next(component.outputs)
            file = next(output.files)  # First file only.
            files.append(file)
            raster_paths.append(f"{i}_{file.file_name}")
            file.download(path=raster_paths[-1])

            # The file has a single band for the classification.
            selectors.append(file.selectors[0])

# Wait for all downloads to complete.
for file in files:
    file.download_complete(wait=True)

# Load the statistics into a Pandas data frame.
statistics = pandas.read_csv(statistics_path)
print(statistics)

# Create a single cloud classification image as a mosaic.
rasters = []

for raster_path in raster_paths:
    rasters.append(rasterio.open(raster_path))

mosaic, transform = merge(rasters)
mosaic_meta = rasters[0].meta.copy()
mosaic_meta.update({'height': mosaic.shape[1],
                    'width': mosaic.shape[2],
                    'transform': transform})

with rasterio.open('mosaic.tif', 'w', **mosaic_meta) as merged:
    merged.write(mosaic)

# Display the mosaic image.
with rasterio.open('mosaic.tif', 'r') as source:
    pyplot.imshow(source.read(1, masked=True), cmap='coolwarm')
    pyplot.show()

# Display the histogram.
histogram = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

for metadata in selectors:
    histogram = [first + second for first, second in zip(histogram, metadata['histogram'])]

# There are only 4 classes, while the histogram has 10 bins.
x = ['Ground', 'Shadow', 'Thick Cloud', 'Thin Cloud']
y = [histogram[0], histogram[3], histogram[6], histogram[9]]

pyplot.bar(x, y)
pyplot.show()

# Tidy everything up by deleting the process and the input file.
process.delete()
lake_district.delete()
