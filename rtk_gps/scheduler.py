import logging
import os
import io
import sys
import time

import libnfs
from rtk_gps.rtk_gps import plot_rtk_neu
import schedule
import paramiko


def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
    logging.critical(
        "Uncaught exception: {exc_value}. Traceback:",
        exc_info=(exc_type, exc_value, exc_traceback),
    )

def plot(nfs: libnfs.NFS, figure_path: str):
    """
    plots for the monitoring room
    """
    logging.info("Running plot schedule...")

    start = None
    end = None
    resample_str = "60s"
    figtype = "png"

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
    plot_rtk_neu(
        nfs,
        baseline_list,
        start=start,
        end=end,
        resample=resample_str,
        special="6h",
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
    plot_rtk_neu(
        nfs,
        baseline_list,
        start=start,
        end=end,
        resample=resample_str,
        special="6h",
        figurepath=figure_path,
        figtype=figtype,
    )

def program_schedule():
    figure_path = "fig_output"

    if os.path.exists(figure_path) == False:
        os.mkdir(figure_path)

    logging.info("Mounting NFS...")
    nfs = libnfs.NFS(os.path.join(os.environ.get("RTK_NFS_HOST"), os.environ.get("RTK_NFS_PATH")))
    plot(nfs, figure_path)

    logging.info("Transfer is set to true.")
    private_key_str = os.environ.get("RTK_SSH_PRIVATE_KEY")
    if not private_key_str:
        raise RuntimeError("Missing SSH private key!")

    private_key = paramiko.RSAKey.from_private_key(io.StringIO(private_key_str))

    logging.info("Establishing SSH connection to CDN...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        os.environ.get("RTK_SFTP_HOST"),
        username=os.environ.get("RTK_SFTP_USER"),
        pkey=private_key
    )

    sftp = client.open_sftp()
    remote_folder_path = os.environ.get("RTK_SFTP_PATH")
    
    for fn in os.listdir(figure_path):
        local_path = os.path.join(figure_path, fn)
        remote_path = os.path.join(remote_folder_path, fn)
        sftp.put(local_path, remote_path)
        logging.info(f"{fn} transferred.")

    client.close()
    
def main():
    sys.excepthook = handle_uncaught_exception
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    program_schedule()#one run before we start the schedule
    scheduler = schedule.Scheduler()
    scheduler.every(5).minutes.at(":10").do(program_schedule)

    while True:
        scheduler.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
