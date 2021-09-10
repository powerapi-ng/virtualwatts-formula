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
from typing import Dict
from collections import OrderedDict, defaultdict
from math import ldexp, fabs

from thespian.actors import ActorAddress
from sklearn.exceptions import NotFittedError

from powerapi.formula import AbstractCpuDramFormula, FormulaValues
from powerapi.message import FormulaStartMessage
from powerapi.report import PowerReport
from powerapi.utils.sync import Sync

from .report import ProcfsReport
from .context import VirtualwattsFormulaConfig




class VirtualwattsFormulaValues(FormulaValues):
    def __init__(self, power_pushers: Dict[str, ActorAddress],config : VirtualwattsFormulaConfig):
        """
        :param config: Configuration of the formula
        """
        FormulaValues.__init__(self, power_pushers)
        self.config = config

class VirtualwattsFormulaActor(AbstractCpuDramFormula):
    """
    This actor handle the reports for the VirutalWatts formula.
    """

    def __init__(self):
        AbstractCpuDramFormula.__init__(self, FormulaStartMessage)

        self.config = None
        self.sync = None


    def _initialization(self, message: FormulaStartMessage):
        AbstractCpuDramFormula._initialization(self, message)
        self.config = message.values.config

        self.sync = Sync(lambda x : isinstance(x,PowerReport),lambda x : isinstance(x,ProcfsReport),self.config.delay_threshold)


    def process_synced_pair(self,pair):
        pw_report = pair[0]
        use_report = pair[1]

        sum_usage = 0
        for k in use_report.usage.keys() :
            sum_usage += use_report.usage[k]

        for k in  use_report.usage.keys() :
            report = PowerReport(pw_report.timestamp, "virtualwatts", use_report.target,pw_report.power* use_report.usage[k] / sum_usage , {})
            for name , pusher in self.pushers.items():
                self.log_debug('send ' + str(report) + ' to ' + name)
                self.send(pusher, report)




    def receiveMsg_ProcfsReport(self,message:ProcfsReport, sender: ActorAddress):
        self.log_debug('receive Procfs Report :' + str(message))
        self.sync.add_report(message)
        pair = self.sync.request()

        if pair is not None :
            self.process_synced_pair(pair)


    def receiveMsg_PowerReport(self,message:PowerReport, sender: ActorAddress):
        self.log_debug('receive Power Report :' + str(message))
        self.sync.add_report(message)
        pair = self.sync.request()

        if pair is not None :
            self.process_synced_pair(pair)
