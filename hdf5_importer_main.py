import os
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.PyQt.QtGui import QIcon
from .hdf5_importer_dialog import HDF5ImporterDialog

class HDF5Importer:
    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = u'&HDF5 Importer'
        self.toolbar = self.iface.addToolBar(u'HDF5Importer')
        self.toolbar.setObjectName(u'HDF5Importer')

    def initGui(self):
        """Create the menu entries and toolbar icons for the plugin."""
        icon_path = os.path.join(self.plugin_dir, 'assets', 'icon.svg')
        if not os.path.exists(icon_path):
            icon_path = os.path.join(self.plugin_dir,'assets','icon.png') 

        icon = QIcon(icon_path)
        self.action = QAction(icon, u'Import HDF5 File', self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(self.menu, self.action)
        self.actions.append(self.action)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(u'&HDF5 Importer', action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar

    def run(self):
        """Run method that performs all the real work."""
        try:
            self.dlg = HDF5ImporterDialog()
            self.dlg.show()
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Could not load the dialog. Make sure h5py and numpy are installed.\nError: {str(e)}")
