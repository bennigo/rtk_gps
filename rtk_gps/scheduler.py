import logging
import os
import sys
import time

import libnfs
from rtk_gps.rtk_gps import plot_rtk_neu
import schedule


def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
    logging.critical(
        "Uncaught exception: {exc_value}. Traceback:",
        exc_info=(exc_type, exc_value, exc_traceback),
    )


def plot_schedule(nfs):
    """
    plots for the monitoring room
    """
    logging.info("Running plot schedule...")
    # tmp = nfs.listdir("./")
    # print(tmp)

    start = None
    end = None
    resample_str = "60s"
    figtype = "png"
    figure_path = os.environ.get("OUTPUT_DIR", "fig_output")

    if os.path.exists(figure_path) == False:
        os.mkdir(figure_path)

    # baseline_list = ["GRIC-ELDC", "THOB-ELDC", "SKSH-ELDC", "SENG-ELDC"]
    baseline_list = [
        "SENG-ELDC",
        "THOB-ELDC",
        "SKSH-ELDC",
        "HS02-ELDC",
        "ASVE-ELDC",
        "GEVK-ELDC",
        "AUSV-ELDC",
    ]
    logging.info(f"Plotting {baseline_list}...")
    plot_rtk_neu(
        nfs,
        baseline_list,
        start=start,
        end=end,
        resample=resample_str,
        special="twodays",
        figurepath=figure_path,
        figtype=figtype,
    )
    plot_rtk_neu(
        nfs,
        baseline_list,
        start=start,
        end=end,
        resample=resample_str,
        special="12h",
        figurepath=figure_path,
        figtype=figtype,
    )

    baseline_list = [
        "SENG-SUDV",
        "HS02-SUDV",
        "THOB-SUDV",
        "ASVE-SUDV",
        "VMOS-SUDV",
        "GRVV-SUDV",
        "GEVK-SUDV",
    ]
    logging.info(f"Plotting {baseline_list}...")
    plot_rtk_neu(
        nfs,
        baseline_list,
        start=start,
        end=end,
        resample=resample_str,
        special="twodays",
        figurepath=figure_path,
        figtype=figtype,
    )
    plot_rtk_neu(
        nfs,
        baseline_list,
        start=start,
        end=end,
        resample=resample_str,
        special="12h",
        figurepath=figure_path,
        figtype=figtype,
    )
    
def main():
    sys.excepthook = handle_uncaught_exception
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logging.info("Mounting NFS...")
    nfs = libnfs.NFS("nfs://rtk.vedur.is/home/gpsops/rtklib-run/data")
    logging.info("Mounting finished.")

    # main()
    plot_schedule(nfs)#one run before we start the schedule
    scheduler = schedule.Scheduler()
    scheduler.every(5).minutes.at(":10").do(plot_schedule, nfs)

    while True:
        scheduler.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
