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
import math
from dataclasses import dataclass

from PySide6 import QtGui

from ..RFTools import Datapoint
from ..SITools import log_floor_125
from .Chart import Chart
from .Frequency import FrequencyChart

logger = logging.getLogger(__name__)


@dataclass
class TickVal:
    count: int = 0
    first: float = 0.0
    step: float = 0.0


def span2ticks(span: float, min_val: float) -> TickVal:
    span = abs(span)
    step = log_floor_125(span / 5)
    count = math.floor(span / step)
    first = math.ceil(min_val / step) * step
    if first == min_val:
        first += step
    return TickVal(count, first, step)


class LogMagChart(FrequencyChart):
    def __init__(self, name="") -> None:
        super().__init__(name)

        self.name_unit: str = "dB"

        self.minDisplayValue: int = -80
        self.maxDisplayValue: int = 10

        self.minValue: float = 0.0
        self.maxValue: float = 1.0
        self.span: float = 1.0

        self.isInverted: bool = False

    def drawValues(self, qp: QtGui.QPainter) -> None:
        if len(self.data) == 0 and len(self.reference) == 0:
            return
        self._set_start_stop()

        # Draw bands if required
        if self.bands.enabled:
            self.drawBands(qp, self.fstart, self.fstop)

        self.calc_scaling()
        self.draw_grid(qp)

        self.drawData(qp, self.data, Chart.color.sweep)
        self.drawData(qp, self.reference, Chart.color.reference)
        self.drawMarkers(qp)

    def calc_scaling(self) -> None:
        if self.fixedValues:
            maxValue = self.maxDisplayValue
            minValue = self.minDisplayValue
        else:
            # Find scaling
            min_val = 100.0
            max_val = -100.0
            for d in self.data:
                logmag = self.logMag(d)
                if math.isinf(logmag):
                    continue
                max_val = max(max_val, logmag)
                min_val = min(min_val, logmag)

            # Also check min/max for the reference sweep
            for d in self.reference:
                if d.freq < self.fstart or d.freq > self.fstop:
                    continue
                logmag = self.logMag(d)
                if math.isinf(logmag):
                    continue
                max_val = max(max_val, logmag)
                min_val = min(min_val, logmag)
            minValue = 10 * math.floor(min_val / 10)
            maxValue = 10 * math.ceil(max_val / 10)

        self.minValue = minValue
        self.maxValue = maxValue

    def draw_grid(self, qp):
        self.span = (self.maxValue - self.minValue) or 0.01
        ticks = span2ticks(self.span, self.minValue)
        self.draw_db_lines(qp, self.maxValue, self.minValue, ticks)

        qp.setPen(QtGui.QPen(Chart.color.foreground))
        qp.drawLine(
            self.leftMargin - 5,
            self.topMargin,
            self.leftMargin + self.dim.width,
            self.topMargin,
        )
        qp.setPen(Chart.color.text)
        qp.drawText(3, self.topMargin + 4, f"{self.maxValue}")
        qp.drawText(3, self.dim.height + self.topMargin, f"{self.minValue}")
        self.drawFrequencyTicks(qp)
        self.draw_swr_markers(qp)

    def draw_db_lines(self, qp, max_value: int, min_value: int, ticks) -> None:
        for i in range(ticks.count):
            db = ticks.first + i * ticks.step
            y = self.topMargin + round(
                (max_value - db) / self.span * self.dim.height
            )
            qp.setPen(QtGui.QPen(Chart.color.foreground))
            qp.drawLine(
                self.leftMargin - 5, y, self.leftMargin + self.dim.width, y
            )
            if db > min_value and db != max_value:
                qp.setPen(QtGui.QPen(Chart.color.text))
                qp.drawText(
                    3, y + 4, f"{round(db, 1)}" if ticks.step < 1 else f"{db}"
                )

    def draw_swr_markers(self, qp) -> None:
        qp.setPen(Chart.color.swr)
        for vswr in self.swrMarkers:
            if vswr <= 1:
                continue
            logMag = 20 * math.log10((vswr - 1) / (vswr + 1))
            if self.isInverted:
                logMag = logMag * -1
            y = self.topMargin + round(
                (self.maxValue - logMag) / self.span * self.dim.height
            )
            qp.drawLine(self.leftMargin, y, self.leftMargin + self.dim.width, y)
            qp.drawText(self.leftMargin + 3, y - 1, f"VSWR: {vswr}")

    def getYPosition(self, d: Datapoint) -> int:
        logMag = self.logMag(d)
        if math.isinf(logMag):
            return self.topMargin
        return self.topMargin + int(
            (self.maxValue - logMag) / self.span * self.dim.height
        )

    def valueAtPosition(self, y) -> list[float]:
        absy = y - self.topMargin
        val = -1 * ((absy / self.dim.height * self.span) - self.maxValue)
        return [val]

    def logMag(self, p: Datapoint) -> float:
        return -p.gain if self.isInverted else p.gain

    def copy(self) -> "LogMagChart":
        new_chart: LogMagChart = super().copy()
        new_chart.isInverted = self.isInverted
        new_chart.span = self.span
        return new_chart
