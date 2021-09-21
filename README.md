VirtualWatts is a software-defined power meter based on the PowerAPI toolkit.
VirtualWatts a configurable software that can estimate the power consumption of
process inside a VM in real-time.
VirtuallWatts is supposed to be used inside a VM. It need to receive two metrics :

- The energy consumption of the VM, usually made with
  [SmartWatts](https://github.com/powerapi-ng/smartwatts-formula)
- The cpu usage of the tracked processes and the global cpu usage, as provided
  by [procfs-sensor](https://github.com/powerapi-ng/procfs-sensor).

# About

VirtualWatts is an open-source project developed by the [Spirals research
group](https://team.inria.fr/spirals) (University of Lille 1 and Inria).

The documentation is not available yet.

## Contributing

If you would like to contribute code you can do so through GitHub by forking the
repository and sending a pull request.
You should start by reading the [contribution guide](https://github.com/powerapi-ng/virtualwatts/blob/main/contributing.md)

When submitting code, please check that it is conform by using `pylint` and
`flake8` with the configurations files at the root of the project.

## Acknowledgments

VirtualWatts is written in [Python](https://www.python.org/) (under [PSF
license](https://docs.python.org/3/license.html)) and built on top of
[PowerAPI](https://github.com/powerapi-ng/powerapi)
