import configparser
import logging
import os
import re
import time
from datetime import datetime as dt
from datetime import timedelta as td
from os.path import getsize, isdir, isfile

import libnfs
import pandas as pd
from gtimes.timefunc import datepathlist

from rtk_gps import open_datafile

# from pathlib import Path


def rtk_write_median(baseline, nfs, date_list, resample, use_columns, filepath):
    """
    read in raw rtk baseline data and writing median to a file
    """

    if type(nfs) is libnfs.NFS:
        filelist = [
            os.path.join(baseline, f"{baseline}{date}0000b.pos") for date in date_list
        ]
    else:
        filelist = [
            os.path.join(nfs, baseline, f"{baseline}{date}0000b.pos")
            for date in date_list
        ]
        nfs = None

    logging.info("filelist: %s", filelist)
    stat_df = open_datafile(filelist, nfs=nfs, file_type="", filt=[5])
    if not len(stat_df.index) > 0:
        logging.info("No data in files: %s", filelist)
        return 1

    stat_df = stat_df.resample(resample).median()
    stat_df = stat_df.dropna()
    stat_df = stat_df[use_columns]

    file = f"{filepath}/{baseline}-distance.neu"
    if len(stat_df.index) > 0:
        stat_df.to_csv(
            file,
            sep="\t",
            float_format="%.3f",
            header=use_columns,
            index_label="#  date_time",
        )
    else:
        print("Dataframe is empty")

    return


def rtk_write_archive(
    baseline, resample, date_list, frequency_list, use_columns, nfs, filepath
):
    """
    read in raw rtk baseline data and writing median to a file
    """

    if type(nfs) is libnfs.NFS:
        filelist = [
            os.path.join(baseline, f"{baseline}{date}0000b.pos") for date in date_list
        ]
    else:
        filelist = [
            os.path.join(nfs, baseline, f"{baseline}{date}0000b.pos")
            for date in date_list
        ]
        nfs = None
    # filelist = [
    #     os.path.join(baseline, f"{baseline}{date}0000b.pos") for date in date_list
    # ]
    
    # stat_df = open_datafile(nfs, filelist, file_type="", filt=[5])
    stat_df = open_datafile(filelist, nfs=nfs, file_type="", filt=[5])
    if not len(stat_df.index) > 0:
        return 1

    stat_df = stat_df.resample(resample).median()
    stat_df = stat_df.dropna()
    stat_df = stat_df[use_columns]

    for period in frequency_list:
        file = f"{filepath}/{baseline}-distance-{period}.neu"
        if not isfile(file):
            # print(stat_df.index.inferred_type == "datetime64")
            try:
                stat_df.loc[period].to_csv(
                    file,
                    sep="\t",
                    float_format="%.3f",
                    header=use_columns,
                    index_label="#  date_time",
                )
                logging.info("File %s has size %sb", file, getsize(file))

            except KeyError:
                logging.info("No data, %s not created", file)

        elif getsize(file) < 826:
            print(f"File {file} has size {getsize(file)}")
            # print(f"adding new data to: {file}")
            file_df = pd.read_csv(
                file,
                index_col=0,
                sep="\t",
                comment="#",
                names=["date_time"] + use_columns,
            )

            join_df = pd.concat([file_df, stat_df.loc[period]])
            join_df.index = pd.to_datetime(join_df.index)
            join_df = join_df[~join_df.index.duplicated(keep="first")]
            join_df.to_csv(
                file,
                sep="\t",
                float_format="%.3f",
                header=use_columns,
                index_label="#  date_time",
            )

    return None


def main():
    """
    Save resample and save rtk files
    """

    projectdir = os.path.split(os.path.dirname(__file__))[0]
    filepath = os.path.join(projectdir, "data")

    python_nfs = False

    if python_nfs:
        nfs = libnfs.NFS("nfs://rtk.vedur.is/home/gpsops/rtklib-run/data")
        baselines = nfs.listdir("./")
    else:
        config = configparser.ConfigParser()
        configpath = os.path.join(os.path.join(projectdir, "config"), "config.ini")
        config.read(configpath)
        nfs = config["paths"]["filepath"]
        baselines = os.listdir(nfs)

    strf = "%Y%m%d"
    # end = dt.now()
    end = dt(year=2024, month=3, day=18)
    start = end - td(days=5)
    # start = dt(year=2024, month=1, day=1)
    resample = "1min"
    file_frequency = "1d"

    r = re.compile(r"\S+-\S+")
    baseline_list = list(filter(r.match, baselines))  # Read Note below
    # baseline_list = ["THOB-ELDC", "SENG-ELDC", "SKSH-ELDC", "ORFC-ELDC"]
    # baseline_list = ["THOB-ELDC"]
    logging.debug("%s", baseline_list)

    if not isdir(filepath):
        logging.info("Directory does not %s exist ... creating it", filepath)
        os.mkdir(filepath)

    use_columns = ["n-baseline", "sdn", "e-baseline", "sde", "u-baseline", "sdu"]
    date_list = list(set(datepathlist("%Y%m%d", "6h", start, end, closed="both")))
    frequency_list = datepathlist(
        strf,
        file_frequency,
        starttime=start,
        endtime=end,
        closed="right",
    )

    start_time = time.perf_counter()
    for baseline in baseline_list:
        print(baseline)
        # rtk_write_median(baseline, nfs, date_list, resample, use_columns, filepath)
        rtk_write_archive(
        baseline, resample, date_list, frequency_list, use_columns, nfs, filepath
        )
    end_time = time.perf_counter()
    logging.warning("Total Run time: %f min", (end_time - start_time)/60.0)


if __name__ == "__main__":
    main()
