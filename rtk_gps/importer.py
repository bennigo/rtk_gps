import sys
import re
import os
import io
import logging
import libnfs
from rtk_gps import open_datafile
import pandas as pd
import sqlalchemy as sa

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logging.info("Establishing SQL connection...")
psql_engine = sa.create_engine(
    "postgresql://{user}:{password}@{host}:{port}/{database}".format(
        user=os.environ.get("RTK_PSQL_USER"),
        password=os.environ.get("RTK_PSQL_PASS"),
        host=os.environ.get("RTK_PSQL_HOST"),
        port=os.environ.get("RTK_PSQL_PORT"),
        database="gps_metrics"
    ),
    echo=False,
    future=True
)

rtk_table = sa.Table("rtk_one_min", sa.MetaData(), autoload_with=psql_engine)

text_file_columns = [
    "date",
    "time",
    "e-baseline",
    "n-baseline",
    "u-baseline",
    "q",
    "ns",
    "sdn",
    "sde",
    "sdu",
    "sden",
    "sdnu",
    "sdue",
    "age",
    "ratio",
]

#TODO: concat-a frame per dag við ein tóman því það gætu verið duplicate
final_columns = [
    "time",
    "e",
    "n",
    "u",
    "q",
    "sdn",
    "sde",
    "sdu",
    "sden",
    "sdnu",
    "sdue",
]

date_format = "%Y/%m/%d%H:%M:%S.%f"

logging.info("Mounting NFS...")
nfs = libnfs.NFS("nfs://rtk.vedur.is/home/gpsops/rtklib-run/data")

baseline_regex = re.compile(r"((?:[A-Z]|[0-9]){4})-((?:[A-Z]|[0-9]){4})")
for baseline in sorted(nfs.listdir(".")):
    match = baseline_regex.search(baseline)
    if match:
        final_frame = pd.DataFrame(columns=col_names[2:])
        base = match.group(2)
        rover = match.group(1)
        filelist = []
        for fn in sorted(nfs.listdir(baseline)):
            if fn.find(baseline) == 0:
                filelist.append(fn)

        if len(filelist) > 0:
            for i in range(min(len(filelist), 4)):
                newest_fn = os.path.join(baseline, filelist[-(i+1)])
                if nfs.stat(newest_fn)["size"] > 0:
                    logging.info(f"Reading {newest_fn}...")
                    content = io.StringIO(nfs.open(newest_fn, mode="r").read())
                    df = pd.read_csv(
                        content,
                        header=None,
                        sep="\s+",
                        comment="%",
                        names=text_file_columns
                    )

                    if not df.empty:
                        df["date_time"] = pd.to_datetime(df["date"] + df["time"], format=date_format)
                        df.drop(columns=["date", "time", "age", "ratio", "ns"], inplace=True)
                        df.rename(columns={
                            "date_time": "time",
                            "e-baseline": "e",
                            "n-baseline": "n", 
                            "u-baseline": "u"
                        }, inplace=True)
                        df.set_index("time", inplace=True)

                        df = df[df.q != 5]
                        df = df.resample("60s").median()
                        df["base"] = base
                        df["rover"] = rover


        with psql_engine.begin() as conn:
            logging.info(f"Inserting {newest_fn}...")
            df.to_sql(rtk_table.name, conn, if_exists="append")


#['time', 'base', 'rover', 'n', 'e', 'u', 'q', 'sdn', 'sde', 'sdu', 'sden', 'sdnu', 'sdue']
