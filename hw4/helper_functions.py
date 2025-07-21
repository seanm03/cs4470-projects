#!/usr/bin/env python
""" Helper routine for loading/creating config for kivy apps and optionally simulate different output devices.

Call config_kivy() to load a proper config, optionally setting/overriding the window dimensions. The window
dimensions are returned, which is useful if you need to pass those dims to your layout code.

And the current device density is returned as well. The full return is a tuple of: win_x_size, win_y_size, density

Also, there is an optional feature that allows simulation of other devices display capabilities when running
windowed Kivy apps (discussed below).

A successful call to config_kivy() will result in the default config being loaded.
If window_width and/or window_height are provided, those values will replace the config settings under [graphics] width
and height.

NOTE: config_kivy() should _usually_ be called from the top of your main Kivy app file. The first lines of executable
code should appear similar to the following:

    from kivy_config_helper import config_kivy
    config_kivy(....)

There may occasionally be exceptions. The main thing is that the import statement and call to config_kivy() should
happen before ALL other Kivy modules are imported. If you don't, Kivy may initialize before the adjustments get applied.

Function Description

    def config_kivy(
                    window_width=None, # width of app window. will be the value set in config file (perhaps overriding
                                        existing file, if already present).
                    window_height=None, # height of app window. will be the value set in config file (perhaps overriding
                                        existing file, if already present).
                    simulate_device=False, # set to True if you wish to simulate another device
                    simulate_dpi=None, # (int) Set if you wish to simulate another device
                    simulate_density=None # (float) Set if you wish to simulate another device
                    ):

Returns a tuple of (window_width, window_height, density). This is either the window_width and window_height you passed,
or it is the [graphics] width and height from the existing config file.

The density is a bit peculiar because if simulation mode is enabled then the device density cannot be queried
accurately. Therefore, it relies on storing the correct density to the config during a previous run. Because of
this, the script may occasionally exit and ask you to run again if a change in density was detected, or if the
density has not yet been stored. There is an edge case were if you stay in simulation mode but change attached
displays then the density could be incorrect. To fix, simply run without simulation mode on, then toggle it back.

Example calls

    # Create/Load config and use 800x600 resolution.
    config_kivy(window_width=800, window_height=600)

    # Create/Load config and use whatever resolution is present in config (possibly Kivy default). Also, use
    # returned app window resolution and density
    app_window_width, app_window_height, device_density = config_kivy()

Simulation

The simulation feature allows you to simulate another device with different display characteristics. This is helpful
to ensure that your Kivy layout is device independent. Note that this only works for windowed mode apps. This code
would need to be modified slightly for full screen apps, and your GUI layout would need to be flexible to handle
different aspect ratios.

The simulation feature creates/revises configuration state such that the resolution best matches what is needed.
This config is exactly the same config as the normal config, but possibly with changes to the [graphics] width
and height.

To simulate another device, set simulate_device=True and also provide simulate_dpi (int)
and simulate_density (float). All four parameters must be set. See below for details.

Next, decide what the characteristics are of the device you wish to simulate. Here are some examples:

    # Generic
    # kivy_simulate_dpi = 100
    # kivy_simulate_density = 1.0

    # Macbook Pro 2023 14"
    # kivy_simulate_dpi = 192
    # kivy_simulate_density = 2.0

    # Fancy Device
    # kivy_simulate_dpi = 250
    # kivy_simulate_density = 2.5

    # Not Fancy Device
    # kivy_simulate_dpi = 50
    # kivy_simulate_density = 0.5

Example call:

    # If you have a Mac Retina Display, and want to simulate a basic display, your command might look like this
    # The window will look smaller than normal, but ideally your GUI layout should maintain proportions.

    config_kivy(simulate_device=True, simulate_dpi=100, simulate_density=1.0)

Additional Info:

    There is a complementary mixin, kivy_sim_app_mixin.SimulationMixin. This can interface with the returned
    values of config_kivy(), as well as responding correctly to simulation mode being enabled to allow for
    accurate window resize behavior, including when dragging the window between displays of different density.

"""

__author__ = "Jeff Wilson, PhD"
__contact__ = "jeff@ipat.gatech.edu"
__copyright__ = "Copyright 2024, Georgia Institute of Technology"
__date__ = "2024/10"
__deprecated__ = False
__email__ = "jeff.wilson@gatech.edu"
__status__ = "Production"
__version__ = "0.0.3"

import os
import sys


def is_kivy_loaded():
    # Check if any modules that start with 'kivy' are in sys.modules
    for module_name, module in sys.modules.items():
        if module_name.startswith("kivy") and module is not None and module_name != "kivy_config_helper":
            print(f"Loaded kivy module found!!!: {module_name}")
            return True
    return False


if is_kivy_loaded():
    print("ERROR: It looks like kivy has already been loaded before kivy_config_helper's config_kivy() was called!")
    print("Please move import of kivy_config_helper and config_kivy() call to the top of your file and try again!")
    exit(0)


from kivy.config import Config


def write_density():
    # critical that metrics is not loaded until other configuration is set to what we want (esp. window resolution)
    from kivy.metrics import Metrics
    if not Config.has_section('simulation'):
        Config.add_section('simulation')
    Config.set('simulation', 'density', str(Metrics.dp))
    Config.write()
    return Metrics.dp


def config_kivy(window_width=None, window_height=None,
                simulate_device=False,
                simulate_dpi=None, simulate_density=None):

    target_window_width = int(window_width)
    target_window_height = int(window_height)

    config_window_width = Config.getint('graphics', 'width')
    config_window_height = Config.getint('graphics', 'height')

    if Config.has_section('simulation') and Config.has_option('simulation', 'density'):
        curr_device_density = Config.getfloat('simulation', 'density')
    else:
        curr_device_density = write_density()
        print(f"The current device density ({curr_device_density}) has been stored in the configuration")
        print(f"Now exiting, please run again to use the stored configuration.")
        exit(0)

    if simulate_device:
        # Note the following simulation strategy assumes you want to simulate the same resolution
        # window (e.g. Kivy app in windowed mode) on various devices. If you want to simulate different
        # full screen apps, then some changes are necessary.

        # For some reason, you can only override Kivy's initial DPI and Density
        # via environment variables.

        if not simulate_dpi or not simulate_density:
            raise ValueError("if simulate_device is set to True, then "
                             "simulate_dpi and simulate_density must be set!")

        print(f"Simulating device with density {simulate_density} and dpi {simulate_dpi}")

        os.environ['KIVY_DPI'] = str(simulate_dpi)
        os.environ['KIVY_METRICS_DENSITY'] = str(simulate_density)

        # This scales window size appropriately for simulation
        target_window_width = int(window_width / curr_device_density * simulate_density)
        target_window_height = int(window_height / curr_device_density * simulate_density)
    else:
        # if these are set externally, we'll ignore and use default dpi and density of device
        os.environ.pop('KIVY_DPI', None)
        os.environ.pop('KIVY_METRICS_DENSITY', None)

    if target_window_width != config_window_width or target_window_height != config_window_height:
        print(f"target_window_width: {target_window_width}, target_window_height: {target_window_height}")
        print(f"config_window_width: {config_window_width}, config_window_height: {config_window_height}")

        Config.set('graphics', 'width', str(target_window_width))
        Config.set('graphics', 'height', str(target_window_height))

    if simulate_device:
        target_window_width = window_width
        target_window_height = window_height
        print(f"Simulated resolution: {target_window_width}x{target_window_height}")
    else:
        # we can only get a reliable density if we aren't simulating (due to impact of KIVY_METRICS_DENSITY env var)
        check_density = write_density()

        if curr_device_density != check_density:
            print(f"The current device density ({check_density}) doesn't match the stored "
                  f"configuration ({curr_device_density}).")
            print(f"Therefore, updating the config to use the correct density.")
            print(f"Now exiting, please run again to use the stored configuration.")
            exit(0)

    return target_window_width, target_window_height
