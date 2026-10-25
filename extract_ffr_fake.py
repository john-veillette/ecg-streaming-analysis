from bids import BIDSLayout
import os
import argparse
from time import time

from extract_ffr import main

BIDS_ROOT = 'bids_dataset'

if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--sub', type = str, help = 'participant ID')
    parser.add_argument('-n', '--num', type = int, help = 'participant index')
    args = parser.parse_args()
    # index BIDS directory
    layout = BIDSLayout(BIDS_ROOT)
    subs = layout.get_subjects()
    # get subject ID to process, or 'all' for all subjects
    if (not args.sub is None) and (args.num is None):
        sub = args.sub
    elif (not args.num is None) and (args.sub is None):
        sub = subs[args.num]
    else:
        raise Exception('Specify a subject with --sub or --num but not both!')
    # now run the main code
    t0 = time()
    if sub == 'all':
        print('Processing all subjects...')
        for s in subs:
            main(layout, s, fake = True)
    else:
        print('Processing sub-%s...'%sub)
        main(layout, sub, fake = True)
    t1 = time()
    print('Done in %.02f minutes.'%((t1 - t0)/60))
