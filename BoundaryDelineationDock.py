# -*- coding: utf-8 -*-
"""
/***************************************************************************
 BoundaryDelineationDock
                                 A QGIS plugin
 BoundaryDelineation
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2018-05-23
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Sophie Crommelink
        email                : s.crommelinck@utwente.nl
        development          : Reiner Borchert, Hansa Luftbild AG Münster
        email                : borchert@hansaluftbild.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, QSettings, QTranslator, qVersion, Qt
from PyQt5.QtGui import QIcon, QColor, QPixmap
from PyQt5.QtWidgets import QDockWidget, QAction, QFileDialog, QToolBar

from qgis.core import QgsMapLayerProxyModel, QgsFieldProxyModel

from .utils import SelectionModes

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'BoundaryDelineationDock.ui'))

class BoundaryDelineationDock(QDockWidget, FORM_CLASS):
    closingPlugin = pyqtSignal()

    def __init__(self, plugin, parent=None):
        """Constructor."""
        super(BoundaryDelineationDock, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        self.plugin = plugin
        self.isAlreadyProcessed = False

        self.tabs.setTabEnabled(1, False)
        self.step1ProgressBar.setValue(0)

        self.baseRasterLayerComboBox.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.baseRasterLayerComboBox.setFilters(QgsMapLayerProxyModel.LineLayer)

        self.baseRasterLayerButton.clicked.connect(self.onBaseRasterInputButtonClicked)
        self.baseRasterLayerComboBox.layerChanged.connect(self.onBaseRasterLayerComboBoxChanged)
        self.segmentsLayerButton.clicked.connect(self.onSegmentsLayerButtonClicked)
        self.segmentsLayerComboBox.currentIndexChanged.connect(self.onSegmentsLayerComboBoxChanged)

        self.modeEnclosingRadio.toggled.connect(self.onModeEnclosingRadioToggled)
        self.modeNodesRadio.toggled.connect(self.onModeNodesRadioToggled)
        self.modeManualRadio.toggled.connect(self.onModeManualRadioToggled)
        self.addLengthAttributeCheckBox.toggled.connect(self.onAddLengthAttributeCheckBoxToggled)
        self.processButton.clicked.connect(self.onProcessButtonClicked)

        self.weightComboBox.fieldChanged.connect(self.onWeightComboBoxChanged)

        self.acceptButton.clicked.connect(self.onAcceptButtonClicked)
        self.rejectButton.clicked.connect(self.onRejectButtonClicked)
        self.editButton.toggled.connect(self.onEditButtonToggled)

        self.weightComboBox.setFilters(QgsFieldProxyModel.Numeric)

        self.__setImage(self.its4landLabel, 'its4landLogo.png')
        self.__setIcon(self.acceptButton, 'accept.png')
        self.__setIcon(self.editButton, 'edit.png')
        self.__setIcon(self.rejectButton, 'reject.png')
        self.__setIcon(self.finishButton, 'finishFlag.png')

        # as there is no option to select None, make sure the correct layer is selected in the first place
        self.segmentsLayerComboBox.currentIndexChanged.emit(self.segmentsLayerComboBox.currentIndex())

    def onBaseRasterInputButtonClicked(self):
        result = QFileDialog.getOpenFileName(self, 'Open Base Raster Layer File', '', 'Raster Image (*.tif *.tiff *.geotiff *.ascii *.map)')

        if result and result[0]:
            self.baseRasterLayerComboBox.setAdditionalItems([result[0]])
            self.baseRasterLayerComboBox.setCurrentIndex(self.baseRasterLayerComboBox.count() - 1)

    def onSegmentsLayerButtonClicked(self):
        result = QFileDialog.getOpenFileName(self, 'Open Segments Layer File', '', 'ESRI Shapefile (*.shp)')

        if result and result[0]:
            self.segmentsLayerComboBox.setAdditionalItems([result[0]])
            self.segmentsLayerComboBox.setCurrentIndex(self.segmentsLayerComboBox.count() - 1)

    def onBaseRasterLayerComboBoxChanged(self, layer):
        if layer:
            self.plugin.setBaseRasterLayer(layer)

    def onSegmentsLayerComboBoxChanged(self, layerIdx):
        if layerIdx is None:
            return

        layer = self.segmentsLayerComboBox.layer(layerIdx)
        layer = self.segmentsLayerComboBox.currentText() if not layer else layer

        if not layer:
            return

        # normalize layer if it's filepath instead of layer instance
        layer = self.plugin.setSegmentsLayer(layer)

        self.weightComboBox.setLayer(layer)
        self.processButton.setEnabled(True)

    def onModeNodesRadioToggled(self, checked):
        self.weightComboBox.setEnabled(checked)

        if checked:
            self.plugin.setSelectionMode(SelectionModes.NODES)

    def onModeEnclosingRadioToggled(self, checked):
        if checked:
            self.plugin.setSelectionMode(SelectionModes.ENCLOSING)

    def onModeManualRadioToggled(self, checked):
        if checked:
            self.plugin.setSelectionMode(SelectionModes.MANUAL)

    def onAddLengthAttributeCheckBoxToggled(self, checked):
        self.plugin.shouldAddLengthAttribute = checked

    def onAcceptButtonClicked(self) -> None:
        self.plugin.acceptCandidates()
        # TODO see the self.onRejectButtonClicked
        self.plugin.refreshSelectionModeBehavior()

    def onRejectButtonClicked(self) -> None:
        self.plugin.rejectCandidates()
        # TODO for some reason this refresh is needed in case we are in manual mode.
        # If we are in manual mode and then rejected, it swtitches to manual too and
        # the selection mode is undefined...
        self.plugin.refreshSelectionModeBehavior()

    def onEditButtonToggled(self) -> None:
        self.plugin.toggleEditCandidates()
        # putting here self.plugin.refreshSelectionModeBehavior() causes infinite loop.

    def onProcessButtonClicked(self) -> None:
        if self.isAlreadyProcessed:
            # TODO confirm you want reprocess and lose all changes
            pass

        self.step1ProgressBar.setValue(0)
        self.plugin.processFirstStep()
        self.step1ProgressBar.setValue(100)

        self.tabs.setCurrentWidget(self.stepTwoTab)
        self.tabs.setTabEnabled(1, True)

        self.updateSelectionModeButtons()

        self.isAlreadyProcessed = True

    def onWeightComboBoxChanged(self, name: str) -> None:
        self.plugin.edgesWeight = name

    def updateSelectionModeButtons(self):
        if self.plugin.isMapSelectionToolEnabled and self.plugin.selectionMode == SelectionModes.ENCLOSING:
            self.modeEnclosingRadio.setChecked(True)
            return

        if self.plugin.isMapSelectionToolEnabled and self.plugin.selectionMode == SelectionModes.NODES:
            self.modeNodesRadio.setChecked(True)
            return

        self.modeManualRadio.setChecked(True)


    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def updateCandidatesButtons(self) -> None:
        enableButtons = self.plugin.candidatesLayer.featureCount() > 0

        self.acceptButton.setEnabled(enableButtons)
        self.rejectButton.setEnabled(enableButtons)
        self.editButton.setEnabled(enableButtons)

    def __setImage(self, label, icon: str) -> None:
        label.setPixmap(QPixmap(os.path.join(self.plugin.pluginDir, 'icons', icon)))


    def __setIcon(self, button, icon: str) -> None:
        button.setIcon(QIcon(os.path.join(self.plugin.pluginDir, 'icons', icon)))

