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


from enum import Enum


class VirtualWattsFormulaScope(Enum):
    """
    Enum used to set the scope of the VirtualWatts formula.
    """

    CPU = "cpu"
    DRAM = "dram"


class VirtualWattsFormulaConfig:
    """
    Global config of the VirtualWatts formula.
    """

    def __init__(self, reports_sampling_interval, delay_threshold):
        """
        Initialize a new formula config object.
        :param reports_sampling_interval: The time interval
        between two reports (in milliseconds)
        :param delay_threshold: Delay threshold to pair
                                two report (in milliseconds)
        """
        self.reports_sampling_interval = reports_sampling_interval
        self.delay_threshold = delay_threshold
