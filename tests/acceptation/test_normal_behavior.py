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
Run virtualwatts on a socket and a file_read

We test if smartwatts return coherent Power report
"""
from datetime import datetime
import pytest
from threading import Thread
from socket import socket
import pymongo
import time
from multiprocessing import Process
import os
import json
import socket



from virtualwatts.__main__ import run_virtualwatts
from virtualwatts.test_utils.reports import virtualwatts_procfs_timeline, virtualwatts_power_timeline

from powerapi.test_utils.actor import shutdown_system
from powerapi.test_utils.db.mongo import mongo_database
from powerapi.test_utils.db.mongo import MONGO_URI, MONGO_INPUT_COLLECTION_NAME, MONGO_OUTPUT_COLLECTION_NAME, MONGO_DATABASE_NAME


@pytest.fixture
def mongodb_content():
    return []


class TCPThread(Thread):
    """
    Thread that open a connection to a socket and send it a list of reports
    """

    def __init__(self, msg_list, port):

        Thread.__init__(self)
        self.msg_list = msg_list
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.port = port

    def run(self):
        time.sleep(1)
        # Sleep to let the time to the puller to start the server
        self.sock.connect(('127.0.0.1', self.port))

        for msg in self.msg_list:
            self.sock.sendall(bytes(json.dumps(msg), 'utf-8'))
            time.sleep(0.5)
        self.sock.close()


class FileThread(Thread):
    """
    Thread that open a virtual file and write a list of reports
    """

    def __init__(self, msg_list, filename):
        Thread.__init__(self)

        self.msg_list = msg_list
        self.filename = filename

    def run(self):
        time.sleep(0.5)
        for msg in self.msg_list:
            file_obj = open(self.filename, 'w')
            file_obj.write(json.dumps(msg))
            file_obj.close()
            time.sleep(0.5)


class MainProcess(Process):
    """
    Process to host VirtualWatts
    """
    def __init__(self,port):
        Process.__init__(self)
        self.port = port

    def run(self):
        config = {'verbose': True,
                  "stream":True,
                  'input': {'puller_filedb': {'type': 'filedb',
                                              'model': 'PowerReport',
                                              'filename': '/tmp/SW_output'},
                            'puller_tcpdb': {'type' : 'socket',
                                             'model': 'ProcfsReport',
                                             'uri': '127.0.0.1',
                                             'port': self.port}
                            },
                  'output': {'power_pusher': {'type': 'mongodb',
                                              'model': 'PowerReport',
                                              'uri': MONGO_URI,
                                              'db': MONGO_DATABASE_NAME,
                                              'collection': MONGO_OUTPUT_COLLECTION_NAME}},
                  'formula': { 'delay-threshold': 500,
                               'sensor-reports-frequency': 500}}
        # Next command is reached
        run_virtualwatts(config)

def check_db(virtualwatts_procfs_timeline,virtualwatts_power_timeline):   # TODO
    procfs_report =  virtualwatts_procfs_timeline
    power_report = virtualwatts_power_timeline
    mongo = pymongo.MongoClient(MONGO_URI)
    c_output = mongo[MONGO_DATABASE_NAME][MONGO_OUTPUT_COLLECTION_NAME]

    amount = 0
    r = procfs_report[0]
    amount = len(r['usage']) * len(power_report)

    assert c_output.count_documents({}) == amount

    for report in c_output.find({'target': 'all'}):
        ts = report['timestamp']
        sum = 0
        for r in c_output.find({'timestamp': ts}):
            sum += int(r['power'])
            assert sum == 42


def test_normal_behaviour(mongo_database, unused_tcp_port, shutdown_system, virtualwatts_procfs_timeline, virtualwatts_power_timeline ):
    tcp_sensor = TCPThread(virtualwatts_procfs_timeline, unused_tcp_port)
    file_sensor = FileThread(virtualwatts_power_timeline, '/tmp/SW_output')

    vw_pro = MainProcess(unused_tcp_port)
    vw_pro.start()

    file_sensor.start()
    tcp_sensor.start()

    tcp_sensor.join()
    file_sensor.join()

    time.sleep(5)

    os.system('kill ' + str(vw_pro.pid))

    check_db(virtualwatts_procfs_timeline,virtualwatts_power_timeline)
