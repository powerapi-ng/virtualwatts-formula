# Copyright (C) 2021  INRIA
# Copyright (C) 2021  University of Lille
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import re
from enum import Enum


class VirtualwattsFormulaScope(Enum):
    """
    Enum used to set the scope of the SmartWatts formula.
    """
    CPU = "cpu"
    DRAM = "dram"


class VirtualwattsFormulaConfig:
    """
    Global config of the Procfs formula.
    """

    def __init__(self, reports_frequency, delay_threshold):
        """
        Initialize a new formula config object.
        :param reports_frequency: Frequency at which the reports (in milliseconds)
        :param delay_threshold: Delay threshold to pair two report (in milliseconds)
        """
        self.reports_frequency = reports_frequency
        self.delay_threshold = delay_threshold