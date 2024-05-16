import logging
import os
import tempfile
import time
from datetime import datetime as dt
from datetime import timedelta as td

import libnfs
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.transforms as mtransforms
import pandas as pd
from gtimes.timefunc import datepathlist
from matplotlib.ticker import AutoMinorLocator


# from rtk_gps.rtk_gps import open_datafile, inpLogo
def inpLogo(fig, Logo=None):
    """ """

    import matplotlib.image as image
    import matplotlib.pyplot as plt
    import numpy as np

    # asp = 0.6948051948051948
    # asp = 0.93 # Image aspect ratio
    asp = 0.1  # Image aspect ratio
    xlen = 0.3
    ylen = xlen * asp

    xpos = fig.axes[0].get_position().xmin - 0.052
    ypos = (fig.axes[0].get_position().ymax) - 0.033

    im = plt.imread(Logo)
    # im[np.all(im[:,:,:3] == [0, 0, 0], axis=-1)] = [255, 255 ,255, 255]
    aximage = fig.add_axes(
        [xpos, ypos, xlen, ylen], frameon=False, xticks=[], yticks=[]
    )
    aximage.imshow(im, alpha=0.7, interpolation="none")


def open_datafile(filelist, nfs, file_type="rtk_coordinate", filt=[5]):
    """
    open rtk baseiline plots
    """
    if file_type == "rtk_coordinate":
        col_names = [
            "date",
            "time",
            "latitude",
            "longitude",
            "height",
            "Q",
            "ns",
            "sdn",
            "sde",
            "sdu",
            "sdne",
            "sdeu",
            "sdun",
            "age",
            "ratio",
        ]
        date_format = "%Y/%m/%d%H:%M:%S.%f"
    else:
        #  UTC, e-baseline(m), n-baseline(m)i,u-baseline(m), Q, ns, sde(m), sdn(m), sdu(m), sden(m), sdnu(m), (m), age(s)  ratio
        col_names = [
            "date",
            "time",
            "e-baseline",
            "n-baseline",
            "u-baseline",
            "Q",
            "ns",
            "sdn",
            "sde",
            "sdu",
            "sdne",
            "sdeu",
            "sdun",
            "age",
            "ratio",
        ]
        date_format = "%Y/%m/%d%H:%M:%S.%f"

    filelist.sort()
    df = pd.DataFrame(columns=col_names[2:])
    r_start = time.perf_counter()
    for filename in filelist:
        try:
            if nfs is None:
                if os.path.exists(filename) and os.stat(filename).st_size != 0:
                    tmp_df = pd.read_csv(
                        filename,
                        header=None,
                        sep=r"\s+",
                        comment="%",
                        names=col_names,
                    )
                else:
                    tmp_df = pd.DataFrame(columns=col_names[2:])

            elif type(nfs) is libnfs.NFS:
                logging.info("Opening %s via NFS...", filename)
                if nfs.stat(filename)["size"] > 0:
                    content = nfs.open(filename, mode="r").read()
                    with tempfile.NamedTemporaryFile(mode="r+") as tf:
                        logging.info("Writing %s to a temp file...", filename)
                        tf.write(content)
                        tf.seek(0, os.SEEK_SET)
                        logging.info("Reading temp file into data frame...")
                        tmp_df = pd.read_csv(
                            tf,
                            header=None,
                            sep="\s+",
                            comment="%",
                            names=col_names,
                        )
                else:
                    tmp_df = pd.DataFrame(columns=col_names[2:])

            if not tmp_df.empty:
                tmp_df["date_time"] = pd.to_datetime(
                    tmp_df["date"] + tmp_df["time"], format=date_format
                )
                tmp_df.drop(columns=["date", "time"], inplace=True)
                tmp_df.set_index("date_time", inplace=True)

        except IOError as e:
            tmp_df = pd.DataFrame(columns=col_names[2:])

        if df.empty:
            df = tmp_df
        elif tmp_df.empty:
            pass
        else:
            df = pd.concat([df, tmp_df])

    r_end = time.perf_counter()
    logging.warning(
        "Run time: %f s for reading in data in %s", r_end - r_start, filelist
    )

    df.index = pd.to_datetime(df.index)  # - timedelta(seconds=18)
    df = df.dropna()

    for i in filt:
        df = df[df.Q != i]

    return df


def plot_rtk_neu(
    nfs,
    baseline_list,
    start=None,
    end=None,
    resample="60s",
    special="twodays",
    figurepath=None,
    figtype="png",
):
    """
    Plot north, east, up component of a few rtk GPS baselines
    with common base station
    """

    figend = ""
    if end is None:
        figend = "now"
        end = dt.now()

    if start is None:
        if special == "twodays":
            start = end - td(days=2)
        elif special == "day":
            start = end - td(days=1)
        elif special == "12h":
            start = end - td(hours=12)
        elif special == "6h":
            start = end - td(hours=6)
        else:
            start = end - td(days=2)
    else:
        special = None

    dstr = "%Y%m%d-%H:%M"
    date_list = list(set(datepathlist("%Y%m%d", "2h", start, end, closed="both")))
    now_string = end.strftime("%Y-%m-%d %H:%M:%S")

    components = ["n-baseline", "e-baseline", "u-baseline"]
    ylabels = ["Norður", "Austur", "Upp"]
    base_stat = baseline_list[0][5:9]

    if figtype == "pdf":
        matplotlib.use("pdf")
    else:
        matplotlib.use("agg")

    fig, axs = plt.subplots(nrows=3, ncols=1, figsize=(13, 20))
    ymin = [None, None, None]
    for baseline in baseline_list:
        stat = baseline[0:4]
        filelist = [
            os.path.join(baseline, "{}{}0000b.pos".format(baseline, date))
            for date in date_list
        ]

        stat_df = open_datafile(filelist, nfs, file_type="")
        # stat_df = open_datafile(datafiles, file_type="")
        stat_df = stat_df.resample(resample).median()
        stat_df = stat_df.dropna()
        stat_df_subset = stat_df.loc[start:end]

        for i, component, ylabel in zip(range(0, 3), components, ylabels):
            stat_df_subset.loc[:, component] = (
                stat_df_subset.loc[:, component]
                - stat_df_subset.loc[:, component].iloc[0:80].mean()
            ) * 100  # change to cm
            axs[i].plot(stat_df_subset.index, stat_df_subset[component], label=stat)

            if ymin[i] is None:
                ymin[i] = axs[i].get_ylim()[0]
            else:
                if axs[i].get_ylim()[0] < ymin[i]:
                    ymin[i] = axs[i].get_ylim()[0]

    # plt.yticks(fontsize=14)
    for i, ylabel in zip(range(0, 3), ylabels):
        trans_offset = mtransforms.offset_copy(
            axs[i].transData, fig=fig, x=0.15, y=2.252756, units="inches"
        )
        axs[i].grid(which="major", color="#DDDDDD", linewidth=2.0)
        axs[i].grid(which="minor", color="#EEEEEE", linestyle=":", linewidth=1.5)
        axs[i].xaxis.set_minor_locator(AutoMinorLocator())
        axs[i].yaxis.set_minor_locator(AutoMinorLocator())

        axs[i].set_ylabel("{} [cm]".format(ylabel), fontsize=16)
        # axs[i].xaxis.set_major_locator(mticker.MaxNLocator())
        # ticks_loc = axs[i].get_xticks().tolist()
        # axs[i].xaxis.set_major_locator(mticker.FixedLocator(ticks_loc))
        axs[i].tick_params(axis="both", labelsize=14)
        axs[i].axvline(x=end, color="green", zorder=2, linewidth=2)
        axs[i].text(
            end,
            ymin[i],
            now_string,
            transform=trans_offset,
            rotation="vertical",
            verticalalignment="center",
            color="green",
            fontsize=18,
        )

    # inpLogo(fig, Logo="VI_Two_Line_Blue.png")

    if special:
        if figend == "now":
            fig_name = f"{figurepath}/rtk_{baseline_list[0]}_{special}.{figtype}"
            title = f"{baseline_list[0]} {special}"
        else:
            end = end.strftime(dstr)
            fig_name = f"{figurepath}/rtk_{baseline_list[0]}_{special}-{end}.{figtype}"
            title = f"{baseline_list[0]} {special}-{end}"

    else:
        start = start.strftime(dstr)
        fig_name = f"{figurepath}/rtk_{baseline_list[0]}_{start}-{end}.{figtype}"
        title = f"{baseline_list[0]} {start}-{end}"

    axs[0].set_title(title, fontdict={"fontsize": 30, "verticalalignment": "bottom"})
    axs[0].legend(loc="lower left", fontsize=16)
    fig.savefig(fig_name)
    plt.close(fig=fig)
    logging.info(f"{fig_name} created")


def test_plot():
    """
    Test plot_rtk_neu
    """
    nfs = libnfs.NFS("nfs://rtk.vedur.is/home/gpsops/rtklib-run/data")
    # tmp = nfs.listdir("./")
    # print(tmp)

    start = None
    end = None
    resample_str = "60s"
    figtype = "pdf"
    special = "twoday"
    figure_path = os.environ.get("OUTPUT_DIR", "fig_output")

    if os.path.exists(figure_path) is False:
        os.mkdir(figure_path)

    # baseline_list = ["GRIC-ELDC", "THOB-ELDC", "SKSH-ELDC", "SENG-ELDC"]
    baseline_list = [
        "SENG-SUDV",
    ]
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


def main():
    """
    main for tests
    """

    test_plot()

    # nfs = libnfs.NFS("nfs://rtk.vedur.is/home/gpsops/rtklib-run/data")
    # filename = "SENG-ELDC/SENG-ELDC202402210000b.pos"


if __name__ == "__main__":
    main()
