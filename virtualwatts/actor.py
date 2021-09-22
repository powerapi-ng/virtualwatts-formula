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

"""
Module that define the virtuallWatts actor
"""

from typing import Dict
from thespian.actors import ActorAddress

from powerapi.formula import AbstractCpuDramFormula, FormulaValues
from powerapi.message import FormulaStartMessage
from powerapi.report import PowerReport
from powerapi.utils.sync import Sync

from powerapi.report import ProcfsReport
from .context import VirtualWattsFormulaConfig


class VirtualWattsFormulaValues(FormulaValues):
    """
    Special parameters needed for the formula
    """
    def __init__(self, power_pushers: Dict[str, ActorAddress],
                 config: VirtualWattsFormulaConfig):
        """
        :param config: Configuration of the formula
        """
        FormulaValues.__init__(self, power_pushers)
        self.config = config


class VirtualWattsFormulaActor(AbstractCpuDramFormula):
    """
    This actor handle the reports for the VirutalWatts formula.
    """

    def __init__(self):
        AbstractCpuDramFormula.__init__(self, FormulaStartMessage)

        self.config = None
        self.sync = None

    def _initialization(self, start_message: FormulaStartMessage):

        AbstractCpuDramFormula._initialization(self, start_message)
        self.config = start_message.values.config

        self.sync = Sync(lambda x: isinstance(x, PowerReport),
                         lambda x: isinstance(x, ProcfsReport),
                         self.config.delay_threshold)

    def process_synced_pair(self):
        """
        :param pair: A power report and a procfs report sync in time

        :return the power consumption of each process
        """

        pair = self.sync.request()
        if pair is not None:
            self.log_debug('Have synced pair :' + str(pair))
            pw_report = pair[0]
            use_report = pair[1]

            for k in use_report.usage.keys():
                used_power = pw_report.power * use_report.usage[k]
                used_power = used_power / use_report.global_cpu_usage

                report = PowerReport(pw_report.timestamp, "virtualwatts",
                                     k, used_power, {})
                for name, pusher in self.pushers.items():
                    self.log_debug('send ' + str(report) + ' to ' + name)
                    self.send(pusher, report)

        self.log_debug('No synced pair yet')

    def receiveMsg_ProcfsReport(self, message: ProcfsReport, _):
        """
        :param message: A procfs Report received from sender

        Provide the report to the sync and call the compute if a pair is formed
        """
        self.log_debug('receive Procfs Report :' + str(message))
        self.sync.add_report(message)
        self.process_synced_pair()

    def receiveMsg_PowerReport(self, message: PowerReport, _):
        """
        :param message: A procfs Report received from sender

        Provide the report to the sync and call the compute if a pair is formed
        """
        self.log_debug('receive Power Report :' + str(message))
        self.sync.add_report(message)
        self.process_synced_pair()
