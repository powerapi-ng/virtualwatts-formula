# Copyright (C) 2018  INRIA
# Copyright (C) 2018  University of Lille
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
Main module of VirtualWatts
 Initialize the system from the configuration and initiate the run
"""


import logging
import signal
import sys
import json
from typing import Dict
import datetime

from powerapi import __version__ as powerapi_version
from powerapi.dispatcher import DispatcherActor, RouteTable
from powerapi.cli import ConfigValidator
from powerapi.cli.tools import (
    ComponentSubParser,
    ReportModifierGenerator,
    PullerGenerator,
    PusherGenerator,
    CommonCLIParser,
)
from powerapi.message import DispatcherStartMessage
from powerapi.report import PowerReport, ProcfsReport
from powerapi.dispatch_rule import (
    PowerDispatchRule,
    PowerDepthLevel,
    ProcfsDispatchRule,
    ProcfsDepthLevel,
)
from powerapi.filter import Filter
from powerapi.actor import InitializationException
from powerapi.supervisor import Supervisor


from virtualwatts import __version__ as virtualwatts_version
from virtualwatts.actor import (VirtualWattsFormulaActor,
                                VirtualWattsFormulaValues)
from virtualwatts.context import VirtualWattsFormulaConfig


def generate_virtualwatts_parser() -> ComponentSubParser:
    """
    Construct and returns the VirtuamWatts cli parameters parser.
    :return: VirtualWatts cli parameters parser
    """
    parser = ComponentSubParser("virtualwatts")

    # Sync Delay threshold
    parser.add_argument(
        "delay-threshold",
        help="Delay threshold for the sync of reports (in miliseconds)",
        type=float,
        default=250.0,
    )

    # Sensor information
    parser.add_argument(
        "sensor-reports-sampling-interval",
        help="The time interval between two measurements \
        are made (in milliseconds)",
        type=int,
        default=1000,
    )

    return parser


def filter_rule(_):
    """
    No rule is needed
    """
    return True


def run_virtualwatts(args) -> None:
    """
    Run PowerAPI with the VirtualWatts formula.
    :param args: CLI arguments namespace
    :param logger: Logger to use for the actors
    """
    fconf = args

    logging.info(
        "VirtualWatts version %s using PowerAPI version %s",
        virtualwatts_version,
        powerapi_version,
    )

    route_table = RouteTable()
    route_table.dispatch_rule(
        PowerReport, PowerDispatchRule(PowerDepthLevel.SENSOR, primary=True)
    )
    route_table.dispatch_rule(
        ProcfsReport, ProcfsDispatchRule(ProcfsDepthLevel.SENSOR,
                                         primary=False)
    )

    report_filter = Filter()

    report_modifier_list = ReportModifierGenerator().generate(fconf)

    supervisor = Supervisor(args["verbose"])

    def term_handler(_, __):
        supervisor.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGTERM, term_handler)
    signal.signal(signal.SIGINT, term_handler)
    try:
        logging.info("Starting VirtualWatts actors...")

        power_pushers = {}
        pushers_info = PusherGenerator().generate(args)
        for pusher_name in pushers_info:
            pusher_cls, pusher_start_message = pushers_info[pusher_name]
            power_pushers[pusher_name] = supervisor.launch(
                pusher_cls, pusher_start_message
            )

        formula_config = VirtualWattsFormulaConfig(
            fconf["sensor-reports-sampling-interval"], fconf["delay-threshold"]
        )
        dispatcher_start_message = DispatcherStartMessage(
            "system",
            "cpu_dispatcher",
            VirtualWattsFormulaActor,
            VirtualWattsFormulaValues(power_pushers, formula_config),
            route_table,
            "cpu",
        )
        cpu_dispatcher = supervisor.launch(DispatcherActor,
                                           dispatcher_start_message)
        report_filter.filter(filter_rule, cpu_dispatcher)

        pullers_info = PullerGenerator(report_filter,
                                       report_modifier_list).generate(
                                           args
                                       )
        for puller_name in pullers_info:
            puller_cls, puller_start_message = pullers_info[puller_name]
            supervisor.launch(puller_cls, puller_start_message)

    except InitializationException as exn:
        logging.error("Actor initialization error: " + exn.msg)
        supervisor.shutdown()
        sys.exit(-1)

    logging.info("VirtualWatts is now running...")
    supervisor.monitor()
    logging.info("VirtualWatts is shutting down...")


def get_config_file(argv):
    """ Retrieve the config file using the cli args"""
    i = 0
    for s in argv:
        if s == "--config-file":
            if i + 1 == len(argv):
                logging.error("config file path needed with argument\
                --config-file")
                sys.exit(-1)
            return argv[i + 1]
        i += 1
    return None


def get_config_from_file(file_path):
    """ Retrieve the config from the config file"""
    config_file = open(file_path, "r")
    return json.load(config_file)


class VirtualWattsConfigValidator(ConfigValidator):
    """ Class to validate the config format """
    @staticmethod
    def validate(conf: Dict):
        if not ConfigValidator.validate(conf):
            return False

        if "sensor-reports-sampling-interval" not in conf:
            conf["sensor-reports-sampling-interval"] = 500
        if "delay-threshold" not in conf:
            conf["delay-threshold"] = 250.0

        conf["delay-threshold"] = datetime.timedelta(
            milliseconds=conf["delay-threshold"])
        return True


def get_config_from_cli():
    """ Get the config from the cli"""
    parser = CommonCLIParser()
    parser.add_component_subparser(
        "formula", generate_virtualwatts_parser(), "specify the formula to use"
    )
    return parser.parse_argv()


if __name__ == "__main__":
    logging.debug("Loading VirtualWatts' config")
    config_file_path = get_config_file(sys.argv)
    config = (
        get_config_from_file(config_file_path)
        if config_file_path is not None
        else get_config_from_cli()
    )
    logging.debug("Validate config")
    if not VirtualWattsConfigValidator.validate(config):
        sys.exit(-1)
    logging.basicConfig(level=logging.WARNING
                        if config["verbose"] else logging.INFO)
    logging.captureWarnings(True)

    logging.debug(str(config))
    logging.debug("Starting VirtualWatts")
    run_virtualwatts(config)
    sys.exit(0)
