import os
import h5py
from qgis.PyQt.QtWidgets import QDialog, QFileDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QComboBox, QTreeWidget, QTreeWidgetItem, QHeaderView, QLabel, QGroupBox, QRadioButton, QMessageBox, QApplication
from qgis.core import QgsVectorLayer, QgsProject, QgsField, QgsFeature, QgsGeometry, QgsPointXY, QgsRasterLayer, QgsVectorFileWriter, QgsCoordinateReferenceSystem
from qgis.PyQt.QtCore import QVariant, Qt
import numpy as np
import tempfile
import math

class HDF5ImporterDialog(QDialog):
    def __init__(self, parent=None):
        """Constructor."""
        super(HDF5ImporterDialog, self).__init__(parent)
        self.setWindowTitle("HDF5 Importer")
        self.h5_file = None
        self.datasets = []

        # --- UI Layout ---
        self.layout = QVBoxLayout(self)

        # File selection
        file_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Select HDF5 file...")
        self.browse_button = QPushButton("Browse")
        file_layout.addWidget(self.file_path_edit)
        file_layout.addWidget(self.browse_button)
        self.layout.addLayout(file_layout)

        # Metadata viewer
        metadata_group = QGroupBox("HDF5 Metadata")
        metadata_layout = QVBoxLayout()
        self.metadata_tree = QTreeWidget()
        self.metadata_tree.setHeaderLabels(["Name", "Type/Shape", "Attributes"])
        self.metadata_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        metadata_layout.addWidget(self.metadata_tree)
        metadata_group.setLayout(metadata_layout)
        self.layout.addWidget(metadata_group)

        # Display mode
        display_group = QGroupBox("Display Mode")
        display_layout = QHBoxLayout()
        self.vector_radio = QRadioButton("Vector (Points)")
        self.raster_radio = QRadioButton("Raster (Image)")
        self.vector_radio.setChecked(True)
        display_layout.addWidget(self.vector_radio)
        display_layout.addWidget(self.raster_radio)
        display_group.setLayout(display_layout)
        self.layout.addWidget(display_group)

        # --- Main Options Group ---
        options_group = QGroupBox("Import Options")
        self.options_layout = QVBoxLayout()
        
        # Variable selection
        lat_layout = QHBoxLayout()
        lat_layout.addWidget(QLabel("Latitude Variable:"))
        self.lat_combo = QComboBox()
        lat_layout.addWidget(self.lat_combo)
        self.options_layout.addLayout(lat_layout)

        lon_layout = QHBoxLayout()
        lon_layout.addWidget(QLabel("Longitude Variable:"))
        self.lon_combo = QComboBox()
        lon_layout.addWidget(self.lon_combo)
        self.options_layout.addLayout(lon_layout)
        
        data_layout = QHBoxLayout()
        data_layout.addWidget(QLabel("Data Variable:"))
        self.data_combo = QComboBox()
        data_layout.addWidget(self.data_combo)
        self.options_layout.addLayout(data_layout)

        options_group.setLayout(self.options_layout)
        self.layout.addWidget(options_group)

        # --- Raster-specific options ---
        self.raster_options_group = QGroupBox("Raster Generation Options")
        raster_layout = QVBoxLayout()
        
        px_size_x_layout = QHBoxLayout()
        px_size_x_layout.addWidget(QLabel("X Pixel Size (degrees):"))
        self.px_size_x_edit = QLineEdit("0.025")
        px_size_x_layout.addWidget(self.px_size_x_edit)
        raster_layout.addLayout(px_size_x_layout)

        px_size_y_layout = QHBoxLayout()
        px_size_y_layout.addWidget(QLabel("Y Pixel Size (degrees):"))
        self.px_size_y_edit = QLineEdit("0.025")
        px_size_y_layout.addWidget(self.px_size_y_edit)
        raster_layout.addLayout(px_size_y_layout)

        nodata_layout = QHBoxLayout()
        nodata_layout.addWidget(QLabel("NoData Value:"))
        self.nodata_edit = QLineEdit("-9999.0")
        nodata_layout.addWidget(self.nodata_edit)
        raster_layout.addLayout(nodata_layout)
        
        # --- REMOVED: Interpolation options removed ---
        
        self.raster_options_group.setLayout(raster_layout)
        self.options_layout.addWidget(self.raster_options_group)

        # Import button
        self.import_button = QPushButton("Import")
        self.layout.addWidget(self.import_button)

        # --- Connections ---
        self.browse_button.clicked.connect(self.browse_file)
        self.import_button.clicked.connect(self.import_data)
        self.vector_radio.toggled.connect(self.update_ui_for_mode)
        
        # Initial state
        self.update_ui_for_mode()

    def update_ui_for_mode(self):
        """Show/hide UI elements based on the selected display mode."""
        self.raster_options_group.setVisible(self.raster_radio.isChecked())

    def browse_file(self):
        file_filter = "HDF Files (*.h5 *.hdf5 *.hdf *.HDF);;All files (*)"
        file_path, _ = QFileDialog.getOpenFileName(self, "Select HDF File", "", file_filter)
        if file_path:
            self.file_path_edit.setText(file_path)
            self.load_hdf5_metadata()

    def load_hdf5_metadata(self):
        file_path = self.file_path_edit.text()
        self.metadata_tree.clear()
        self.lat_combo.clear()
        self.lon_combo.clear()
        self.data_combo.clear()
        self.datasets = []

        if not os.path.exists(file_path): return
        try:
            if self.h5_file: self.h5_file.close()
            self.h5_file = h5py.File(file_path, 'r')
            self.h5_file.visititems(self.populate_metadata_tree)
            self.datasets = sorted(self.datasets)
            self.lat_combo.addItems(self.datasets)
            self.lon_combo.addItems(self.datasets)
            self.data_combo.addItems(self.datasets)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not read HDF5 file: {e}")
            self.h5_file = None

    def populate_metadata_tree(self, name, obj):
        if isinstance(obj, h5py.Dataset): self.datasets.append(name)
        path_parts = name.split('/')
        parent_item = self.metadata_tree.invisibleRootItem()
        for part in path_parts:
            child_item = next((parent_item.child(i) for i in range(parent_item.childCount()) if parent_item.child(i).text(0) == part), None)
            if child_item is None: child_item = QTreeWidgetItem(parent_item, [part])
            parent_item = child_item
        if isinstance(obj, h5py.Dataset):
            parent_item.setText(1, f"Dataset ({obj.dtype}) - {obj.shape}")
            parent_item.setText(2, "; ".join([f"{k}='{v}'" for k, v in obj.attrs.items()]))

    def import_data(self):
        if not self.h5_file:
            QMessageBox.warning(self, "Warning", "Please select a valid HDF5 file.")
            return

        lat_var = self.lat_combo.currentText()
        lon_var = self.lon_combo.currentText()
        data_var = self.data_combo.currentText()

        if not lat_var or not lon_var or not data_var:
            QMessageBox.warning(self, "Warning", "Please select Latitude, Longitude, and Data variables.")
            return

        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            lat_data = self.h5_file[lat_var][:]
            lon_data = self.h5_file[lon_var][:]
            main_data = self.h5_file[data_var][:]

            if self.vector_radio.isChecked():
                self.import_as_vector(lat_data, lon_data, main_data, data_var)
            else:
                self.import_as_raster(lat_data, lon_data, main_data, data_var)
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"An error occurred during import: {e}")
        finally:
            QApplication.restoreOverrideCursor()
            self.close()

    def import_as_vector(self, lat_data, lon_data, value_data, value_name):
        """Creates a new vector point layer from lat/lon data and a value dataset."""
        if not (lat_data.shape == lon_data.shape == value_data.shape):
             QMessageBox.critical(self, "Error", "Latitude, Longitude, and Data arrays must have the same shape.")
             return None
        
        layer = self._create_temp_vector_layer(lat_data, lon_data, value_data, value_name)
        if layer:
            QgsProject.instance().addMapLayer(layer)
            QMessageBox.information(self, "Success", f"Successfully created vector layer '{layer.name()}'.")
        return layer

    def _create_temp_vector_layer(self, lat_data, lon_data, value_data, value_name):
        """Helper function to create a vector layer, excluding NoData values."""
        layer = QgsVectorLayer("Point?crs=epsg:4326", "temp_points", "memory")
        provider = layer.dataProvider()
        provider.addAttributes([QgsField("value", QVariant.Double)])
        layer.updateFields()

        lat_flat = lat_data.flatten()
        lon_flat = lon_data.flatten()
        val_flat = value_data.flatten()

        features = []
        data_fill_value = self.h5_file[self.data_combo.currentText()].attrs.get('_FillValue')
        for i in range(len(lat_flat)):
            lat, lon, val = lat_flat[i], lon_flat[i], val_flat[i]
            if np.isfinite(lon) and np.isfinite(lat) and np.isfinite(val) and (data_fill_value is None or val != data_fill_value):
                feat = QgsFeature()
                feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(float(lon), float(lat))))
                feat.setAttributes([float(val)])
                features.append(feat)
        
        provider.addFeatures(features)
        return layer

    def import_as_raster(self, lat_data, lon_data, main_data, data_var_name):
        """Creates a raster by direct rasterization of points."""
        try:
            from osgeo import gdal
            gdal.UseExceptions()
        except (ImportError, ModuleNotFoundError):
            QMessageBox.critical(self, "Error", "GDAL Python bindings are required for this feature.")
            return

        vector_layer = self._create_temp_vector_layer(lat_data, lon_data, main_data, data_var_name)
        if not vector_layer or vector_layer.featureCount() == 0:
            QMessageBox.warning(self, "Warning", "No valid data points found to create a raster.")
            return
            
        try:
            px_size_x = abs(float(self.px_size_x_edit.text()))
            px_size_y = abs(float(self.px_size_y_edit.text()))
            nodata_val = float(self.nodata_edit.text())
        except ValueError:
            QMessageBox.critical(self, "Input Error", "Pixel sizes and NoData value must be valid numbers.")
            return

        with tempfile.NamedTemporaryFile(suffix=".gpkg", delete=False) as temp_gpkg:
            temp_gpkg_path = temp_gpkg.name
        
        writer = QgsVectorFileWriter.writeAsVectorFormat(vector_layer, temp_gpkg_path, "UTF-8", vector_layer.crs(), "GPKG")
        if writer[0] != QgsVectorFileWriter.NoError:
            QMessageBox.critical(self, "Error", f"Failed to write temporary vector file: {writer[1]}")
            return
            
        clean_name = data_var_name.replace('/', '_').replace('-', '_')
        base_layer_name = os.path.basename(self.file_path_edit.text()).split('.')[0] + f"_{clean_name}"
        output_dir = os.path.dirname(self.file_path_edit.text())
        temp_tiff_path = os.path.join(output_dir, f"{base_layer_name}_raster.tif")
        
        extent = vector_layer.extent()
        width = math.ceil(extent.width() / px_size_x)
        height = math.ceil(extent.height() / px_size_y)

        try:
            # --- SIMPLIFIED: Only use gdal.Rasterize ---
            gdal.Rasterize(temp_tiff_path, temp_gpkg_path,
                outputBounds=[extent.xMinimum(), extent.yMinimum(), extent.xMaximum(), extent.yMaximum()],
                width=width, height=height, attribute="value", noData=nodata_val,
                outputType=gdal.GDT_Float32, allTouched=True)
        except Exception as e:
            os.remove(temp_gpkg_path)
            QMessageBox.critical(self, "Raster Creation Error", f"GDAL operation failed: {e}")
            return
        
        os.remove(temp_gpkg_path)

        rlayer = QgsRasterLayer(temp_tiff_path, base_layer_name)
        if not rlayer.isValid():
            QMessageBox.critical(self, "Error", f"Failed to load the rasterized layer from {temp_tiff_path}")
        else:
            QgsProject.instance().addMapLayer(rlayer)
            QMessageBox.information(self, "Success", f"Successfully created raster '{base_layer_name}'.")

    def closeEvent(self, event):
        if self.h5_file:
            self.h5_file.close()
            self.h5_file = None
        super(HDF5ImporterDialog, self).closeEvent(event)