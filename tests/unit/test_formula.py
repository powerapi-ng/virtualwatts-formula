#!/usr/bin/env python3

# Copyright (c) 2021, INRIA
# Copyright (c) 2021, University of Lille
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.

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

    def test_starting_virtualwatts_formula_without_VirtualWattsFormulaStartMessage_answer_ErrorMessage(self, system, actor):
        answer = system.ask(actor, StartMessage('system', 'test'))
        assert isinstance(answer, ErrorMessage)
        assert answer.error_message == 'use FormulaStartMessage instead of StartMessage'


    def test_send_power_report_virtualwatts_report_to_virtualwatts_formula_return_correct_result(self, system,started_actor, dummy_pipe_out):
        report1 = PowerReport(datetime.datetime(1970,1,1), "toto","t1",42,{})
        usage_dic = {"t1":0.5}
        report2 = ProcfsReport(datetime.datetime(1970,1,1), "totoproc", "t1",usage_dic,0.5)

        system.tell(started_actor,report2)
        system.tell(started_actor,report1)


        _,msg = recv_from_pipe(dummy_pipe_out,1)
        assert isinstance(msg,PowerReport)
        assert msg.power == 42




    def test_send_track_two_process_with_virtualwatts_formula_return_correct_result(self, system,started_actor, dummy_pipe_out):
        report1 = PowerReport(datetime.datetime(1970,1,1), "toto","t1",100,{})
        usage_dic = {"t1":0.7, "t2":0.3}
        report2 = ProcfsReport(datetime.datetime(1970,1,1), "totoproc", "t1",usage_dic,1)


        system.tell(started_actor,report2)
        system.tell(started_actor,report1)


        _,msg = recv_from_pipe(dummy_pipe_out,1)
        assert isinstance(msg,PowerReport)
        if msg.target == "t1":
            assert msg.power == 70
        if msg.target == "t2":
            assert msg.power == 30



    def test_send_track_two_process_with_virtualwatts_formula_return_correct_result(self, system,started_actor, dummy_pipe_out):
        report1 = PowerReport(datetime.datetime(1970,1,1), "toto","t1",100,{})
        usage_dic = {"t1":0.7, "t2":0.3}
        report2 = ProcfsReport(datetime.datetime(1970,1,1), "totoproc", "t1",usage_dic,2)


        system.tell(started_actor,report2)
        system.tell(started_actor,report1)


        _,msg = recv_from_pipe(dummy_pipe_out,1)
        assert isinstance(msg,PowerReport)
        if msg.target == "t1":
            assert msg.power == 35
        if msg.target == "t2":
            assert msg.power == 15
