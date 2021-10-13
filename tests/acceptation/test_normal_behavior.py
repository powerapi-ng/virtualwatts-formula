# MIT License

# Copyright (c) 2021 PowerAPI

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
import datetime
import sys
from virtualwatts.__main__ import run_virtualwatts, VirtualWattsConfigValidator
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
                                              'filename': 'SW_output'},
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
                  'delay-threshold': 500,
                  'sensor-reports-sampling-interval': datetime.timedelta(500)}
        # Next command is reached
        if not VirtualWattsConfigValidator.validate(config):
            sys.exit(-1)
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
    file_sensor = FileThread(virtualwatts_power_timeline, 'SW_output')

    vw_pro = MainProcess(unused_tcp_port)
    vw_pro.start()

    file_sensor.start()
    tcp_sensor.start()

    tcp_sensor.join()
    file_sensor.join()

    time.sleep(5)

    os.system('kill ' + str(vw_pro.pid))

    check_db(virtualwatts_procfs_timeline,virtualwatts_power_timeline)
