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

import pytest

from thespian.actors import ActorExitRequest

from virtualwatts.actor import VirtualWattsFormulaActor
from powerapi.formula import CpuDramDomainValues
from powerapi.message import StartMessage, FormulaStartMessage, ErrorMessage, EndMessage, OKMessage
from powerapi.report import Report, PowerReport, ProcfsReport
from powerapi.test_utils.abstract_test import AbstractTestActor, recv_from_pipe
from powerapi.test_utils.actor import system
from powerapi.test_utils.dummy_actor import logger
import datetime
from virtualwatts.actor import VirtualWattsFormulaValues
from virtualwatts.context import VirtualWattsFormulaConfig


class TestVirtualWattsFormula(AbstractTestActor):
    @pytest.fixture
    def actor(self, system):
        actor = system.createActor(VirtualWattsFormulaActor)
        yield actor
        system.tell(actor, ActorExitRequest())

    @pytest.fixture
    def actor_start_message(self, logger):
        config = VirtualWattsFormulaConfig(1000, datetime.timedelta(500))
        values = VirtualWattsFormulaValues({'logger': logger},config)
        return FormulaStartMessage('system', 'test_virtualwatts_formula', values, CpuDramDomainValues('test_device', ('test_sensor', 0, 0)))

    # def test_starting_virtualwatts_formula_without_VirtualWattsFormulaStartMessage_answer_ErrorMessage(self, system, actor):
    #     answer = system.ask(actor, StartMessage('system', 'test'))
    #     assert isinstance(answer, ErrorMessage)
    #     assert answer.error_message == 'use FormulaStartMessage instead of StartMessage'


    def test_send_power_report_virtualwatts_report_to_virtualwatts_formula_return_correct_result(self, system,started_actor, dummy_pipe_out):
        report1 = PowerReport(datetime.datetime(1970,1,1), "toto","t1",42,{})
        usage_dic = {"t1": 0.5}
        report2 = ProcfsReport(datetime.datetime(1970, 1, 1), "totoproc", "t1", usage_dic, 0.5)

        system.tell(started_actor,report2)
        system.tell(started_actor,report1)


        _,msg = recv_from_pipe(dummy_pipe_out,1)
        assert isinstance(msg,PowerReport)
        assert msg.power == 42




    def test_send_track_two_process_with_virtualwatts_formula_return_correct_result(self, system, started_actor, dummy_pipe_out):
        report1 = PowerReport(datetime.datetime(1970, 1, 1), "toto", "t1", 100, {})
        usage_dic = {"t1": 0.7, "t2": 0.3}
        report2 = ProcfsReport(datetime.datetime(1970,1,1), "totoproc", "t1",usage_dic,1)


        system.tell(started_actor,report2)
        system.tell(started_actor,report1)


        _,msg = recv_from_pipe(dummy_pipe_out,1)
        assert isinstance(msg,PowerReport)
        if msg.target == "t1":
            assert msg.power == 70
        if msg.target == "t2":
            assert msg.power == 30



    def test_send_track_two_process_with_virtualwatts_formula_return_correct_result(self, system, started_actor, dummy_pipe_out):
        report1 = PowerReport(datetime.datetime(1970, 1, 1), "toto", "t1",
                              100, {})
        usage_dic = {"t1": 0.7, "t2": 0.3}
        report2 = ProcfsReport(datetime.datetime(1970, 1, 1), "totoproc", "t1",
                               usage_dic, 2)

        system.tell(started_actor, report2)
        system.tell(started_actor, report1)


        _,msg = recv_from_pipe(dummy_pipe_out, 1)
        assert isinstance(msg, PowerReport)
        if msg.target == "t1":
            assert msg.power == 35
        if msg.target == "t2":
            assert msg.power == 15
