# -*- coding: utf-8 -*-

def classFactory(iface):
    """Load HDF5Importer class from file hdf5_importer_main."""
    from .hdf5_importer_main import HDF5Importer
    return HDF5Importer(iface)