# QGIS HDF5 Importer Plugin 

This plugin imports satellite observations in HDF5 file as vector points or raster image.
It allows users to select an HDF5 file, view its metadata, choose latitude and longitude variables, and load the data as a point vector or a raster image layer in QGIS.

## Requirements for installing this plugin

- **QGIS 3.4+** : A valid QGIS installation with version number 3.4 and above,
- **Python libraries**:
    - `h5py`: for reading HDF5 dataset.
    - `gdal`: for converting to raster images.

## Usage

1. Install the plugin via zip. [Load plugins from zip - QGIS Documentation](https://docs.qgis.org/3.40/en/docs/user_manual/plugins/plugins.html#the-install-from-zip-tab)
2. You can find the plugin either from
    - `Plugins` - `HDF5 importer` - `Import HDF5 file`, or
    - An icon ![HDF5 importer icon](icon.svg) in QGIS Toolbar.
3. Open the plugin window, select the HDF5 file you want to load via file selection window.
4. Choose the correct display mode: vector or raster^[1].
5. After loading the HDF5 file, you will see the metadata associated to each varaiable, choose the correct lat/lon variable name for the dataset you want to import.
6. Click import, and you will see the data is now imported to the QGIS layer.

^[1]: Note: import as raster may take some time depending on your dataset size, spatial extent and the resolution, etc.

## Options

- 