# rtk_gps

RTK GPS is a collection of scripts that produce plots of realtime GPS baselines that have been downsampled over 10 minutes.
The project can be installed by using `poetry` or `pip install .`
Poetry installs plotrtk, rtk_scheduler and save_rtk_data. plotrtk is a command line program to generate the plots while
rtk_scheduler is a program that generates new images every 5 minutes and copies them to cdn.vedur.is.
save_rtk_data generates 1 minute median resamples of the data as text files.
The raw files themselves are transferred from nfs://rtk.vedur.is using libnfs.
