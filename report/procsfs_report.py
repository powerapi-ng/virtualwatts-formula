# Copyright (c) 2021, INRIA
# Copyright (c) 2021, University of Lille
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Tuple

from powerapi.report.report import Report, BadInputData, CSV_HEADER_COMMON


CSV_HEADER_PROCFS = CSV_HEADER_COMMON + ['socket', 'cpu']


class PROCFSReport(Report):
    """
    PROCFSReport class
    JSON PROCFS format
    {
    timestamp: int
    sensor: str,
    target: str,
    usage: [ {cgroup_name: str, usage: float} ]
    }


    """

    def __init__(self, timestamp: datetime, sensor: str, target: str, usage: Dict):
        """
        Initialize an PROCFS report using the given parameters.
        :param datetime timestamp: Timestamp of the report
        :param str sensor: Sensor name
        :param str target: Target name
        :param int usage : CGroup name and cpu_usage
        """
        Report.__init__(self, timestamp, sensor, target)

        #: (dict): Events groups
        self.usage = usage

    def __repr__(self) -> str:
        return 'PROCFSReport(%s, %s, %s, %s)' % (self.timestamp, self.sensor, self.target, sorted(self.usage.keys()))



    @staticmethod
    def from_json(data: Dict) -> PROCFSReport:
        """
        Generate a report using the given data.
        :param data: Dictionary containing the report attributes
        :return: The PROCFS report initialized with the given data
        """
        try:
            ts = Report._extract_timestamp(data['timestamp'])
            return PROCFSReport(ts, data['sensor'], data['target'], data['usage'])
        except KeyError as exn:
            raise BadInputData('no field ' + str(exn.args[0]) + ' in json document')

    @staticmethod
    def to_json(report: PROCFSReport) -> Dict:
        return report.__dict__

    @staticmethod
    def from_mongodb(data: Dict) -> PROCFSReport:
        return PROCFSReport.from_json(data)

    @staticmethod
    def to_mongodb(report: PROCFSReport) -> Dict:
        return PROCFSReport.to_json(report)

    @staticmethod
    def from_csv_lines(lines: List[Tuple[str, Dict]]) -> PROCFSReport:
        sensor_name = None
        target = None
        timestamp = None
        usage = {}

        for file_name, row in lines:
            cgroup_name = file_name[:-4] if file_name[len(file_name)-4:] == '.csv' else file_name
            try:
                if sensor_name is None:
                    sensor_name = row['sensor']
                else:
                    if sensor_name != row['sensor']:
                        raise BadInputData('csv line with different sensor name are mixed into one report')
                if target is None:
                    target = row['target']
                else:
                    if target != row['target']:
                        raise BadInputData('csv line with different target are mixed into one report')
                if timestamp is None:
                    timestamp = PROCFSReport._extract_timestamp(row['timestamp'])
                else:
                    if timestamp != PROCFSReport._extract_timestamp(row['timestamp']):
                        raise BadInputData('csv line with different timestamp are mixed into one report')

                if cgroup_name not in usage:
                    usage[cgroup_name] = {}

                for key, value in row.items():
                    if key not in CSV_HEADER_PROCFS:
                        usage[cgroup_name][key] = int(value)

            except KeyError as exn:
                raise BadInputData('missing field ' + str(exn.args[0]) + ' in csv file ' + file_name)

        return PROCFSReport(timestamp, sensor_name, target, usage)

#############################
# REPORT CREATION FUNCTIONS #
#############################


# def create_core_report(core_id, event_id, event_value, events=None):
#     id_str = str(core_id)
#     data = {id_str: {}}
#     if events is not None:
#         data[id_str] = events
#         return data
#     data[id_str] = {event_id: event_value}
#     return data


# def create_socket_report(socket_id, core_list):
#     id_str = str(socket_id)
#     data = {id_str: {}}
#     for core in core_list:
#         data[id_str].update(core)
#     return data


# def create_group_report(group_id, socket_list):
#     group = {}
#     for socket in socket_list:
#         group.update(socket)
#     return (group_id, group)


def create_report_root(cgroup_list, timestamp=datetime.fromtimestamp(0), sensor='toto', target='all'):
    sensor = PROCFSReport(timestamp=timestamp, sensor=sensor, target=target, usage={})
    for (cgroup_id, cpu_usage) in cgroup_list:
        sensor.usage[cgroup_id] = cpu_usage
    return sensor
