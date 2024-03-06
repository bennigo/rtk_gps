# -*- coding: utf-8 -*-
"""
#/usr/bin/python
"""

import argparse
import configparser
import os
from datetime import datetime as dt
from pathlib import Path

import libnfs
import matplotlib.pyplot as plt
from numpy import who

from rtk_gps.rtk_gps import plot_rtk_neu

# from rtk_gps import plot_rtk_neu


def main():
    """
    cli program to plot real time GPS time series
    """

    nfs = libnfs.NFS("nfs://rtk.vedur.is/home/gpsops/rtklib-run/data")

    projectdir = os.path.split(os.path.dirname(__file__))[0]
    configpath = os.path.join(os.path.join(projectdir, "config"), "config.ini")

    config = configparser.ConfigParser()
    config.read(configpath)

    file_path = Path(config["Paths"]["filepath"])
    figure_path = Path(os.path.join(projectdir, config["Paths"]["figurepath"]))
    if os.path.exists(figure_path) == False:
        os.mkdir(figure_path)

    start = end = None

    resample_str = "1min"
    # baseline_list = ["ORFC-ELDC", "THOB-ELDC", "SKSH-ELDC", "SENG-ELDC"]
    dstr = "%Y%m%d-%H:%M:%S"  # Default input string

    # initialising  few variables
    start = end = None
    save_allow = ["png", "pdf"]
    special_allow = ["6h", "12h", "day", "twodays", "threedays", "week"]

    parser = argparse.ArgumentParser(
        description="Plot tool for realtime time series.",
        epilog="For any issues regarding this program or the GPS system contact,email: bgo@vedur.is",
    )

    parser.add_argument("Stations", nargs="+", help="List of stations")
    parser.add_argument("-s", "--start", type=str, default=None, help="Start of plot")
    parser.add_argument("-e", "--end", type=str, default=None, help="End of plot")
    parser.add_argument(
        "--save",
        type=str,
        nargs="?",
        default="png",
        const="png",
        choices=save_allow,
        help="save figure to a file defaults to postscript (eps)",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="plot strictly the period specified, regardless of the data",
    )
    parser.add_argument(
        "--ylim",
        type=int,
        default=[],
        nargs="+",
        help="set limit for y-axis: list of one or two numbers in mm. "
        + "One number x will expand the y axis by x mm in each direciton. "
        + "Two numbers will give absolute lower and upper boundary of the y-axis",
    )
    parser.add_argument(
        "--special",
        type=str,
        default="twodays",
        choices=special_allow,
        help="For routine plots: one day, two days, three days and a week",
    )
    parser.add_argument(
        "-d",
        "--figDir",
        type=str,
        nargs="?",
        default="",
        const=figure_path,
        help="Figure save directory",
    )
    parser.add_argument(
        "-i",
        "--Dir",
        type=str,
        nargs="?",
        default="",
        const=file_path,
        help="Time series input directory",
    )

    args = parser.parse_args()

    baseline_list = args.Stations
    special = args.special
    figtype = args.save

    if args.start:  # start the plot at
        start = dt.strptime(args.start, dstr)
    if args.end:  # end the plot at
        end = dt.strptime(args.end, dstr)
    if args.figDir:
        figure_path = args.figDir

    plot_rtk_neu(
        nfs,
        baseline_list,
        start=start,
        end=end,
        resample=resample_str,
        special=special,
        figurepath=figure_path,
        figtype=figtype,
    )


if __name__ == "__main__":
    main()
