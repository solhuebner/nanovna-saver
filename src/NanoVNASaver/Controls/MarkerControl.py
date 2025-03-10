#  NanoVNASaver
#
#  A python program to view and export Touchstone data from a NanoVNA
#  Copyright (C) 2019, 2020  Rune B. Broberg
#  Copyright (C) 2020,2021 NanoVNA-Saver Authors
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
import logging
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtWidgets
from PySide6.QtWidgets import QCheckBox, QSizePolicy

from ..Defaults import get_app_config
from ..Marker.Widget import Marker
from .Control import Control

if TYPE_CHECKING:
    from ..NanoVNASaver.NanoVNASaver import NanoVNASaver as vna_app

logger = logging.getLogger(__name__)


class ShowButton(QtWidgets.QPushButton):
    def setText(self, text: str = ""):
        app_config = get_app_config()
        if not text:
            text = "Show data" if app_config.gui.markers_hidden else "Hide data"
        super().setText(text)
        self.setToolTip("Toggle visibility of marker readings area")


class MarkerControl(Control):
    def __init__(self, app: "vna_app"):
        super().__init__(app, "Markers")

        app_config = get_app_config()
        for i in range(app_config.chart.marker_count):
            marker = Marker("", self.app.settings)
            # marker.setFixedHeight(20)
            marker.updated.connect(self.app.markerUpdated)
            label, layout = marker.getRow()
            self.layout.addRow(label, layout)
            self.app.markers.append(marker)
            if i == 0:
                marker.isMouseControlledRadioButton.setChecked(True)

        self.check_delta = QCheckBox("Enable Delta Marker")
        self.check_delta.toggled.connect(self.toggle_delta)

        self.check_delta_reference = QCheckBox("Reference")
        self.check_delta_reference.toggled.connect(self.toggle_delta_reference)

        layout2 = QtWidgets.QHBoxLayout()
        layout2.addWidget(self.check_delta)
        layout2.addWidget(self.check_delta_reference)

        self.layout.addRow(layout2)

        self.showMarkerButton = ShowButton()
        self.showMarkerButton.setFixedHeight(20)
        self.showMarkerButton.setText()
        self.showMarkerButton.clicked.connect(self.toggle_frame)

        lock_radiobutton = QtWidgets.QRadioButton("Locked")
        lock_radiobutton.setLayoutDirection(
            QtCore.Qt.LayoutDirection.RightToLeft
        )
        lock_radiobutton.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred
        )

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.showMarkerButton)
        hbox.addWidget(lock_radiobutton)
        self.layout.addRow(hbox)

    def toggle_frame(self):
        def settings(hidden: bool):
            app_config = get_app_config()
            app_config.gui.markers_hidden = not hidden
            self.app.marker_frame.setHidden(app_config.gui.markers_hidden)
            self.showMarkerButton.setText()
            self.showMarkerButton.repaint()

        settings(self.app.marker_frame.isHidden())

    def toggle_delta(self):
        self.app.delta_marker_layout.setVisible(self.check_delta.isChecked())

    def toggle_delta_reference(self):
        self.app.marker_ref = bool(self.check_delta_reference.isChecked())

        if self.app.marker_ref:
            new_name = "Delta Reference - Marker 1"

        else:
            new_name = "Delta Marker 2 - Marker 1"
            # FIXME: reset
        self.app.delta_marker.group_box.setTitle(new_name)
        self.app.delta_marker.resetLabels()
