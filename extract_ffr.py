# standard python libraries
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import os
import argparse
from time import time

# some EEG-specific utilities
from mne_bids import BIDSPath, read_raw_bids, print_dir_tree
from bids import BIDSLayout
import mne

from util.bids import DataSink

# the directory where BIDS-formatted data can be found
BIDS_ROOT = 'bids_dataset'
# passband for filter (in Hz),
# make sure it contains frequency of stimulus
PASSBAND = (100., 2000.)
# peak-to-peak rejection threshold
THRES = 35e-6

TASK_TO_USE = 'both'
assert(TASK_TO_USE in ['streaming', 'discrimination', 'both'])

def main(layout, sub, fake = False):

    # figure out where derivative files should be saved
    deriv_root = os.path.join(layout.root, 'derivatives')
    name_of_current_file = os.path.basename(__file__)[:-3]
    if fake:
        name_of_current_file += '_fake'

    ## only proceed if participant has not already been preprocessed
    deriv_dir = os.path.join(deriv_root, name_of_current_file, 'sub-%s'%sub)
    if os.path.isdir(deriv_dir):
        return

    # create datasink helper to save derivative files
    sink = DataSink(deriv_root, name_of_current_file)

    # load all events from both tasks to get minimum tone duration
    event_fs = layout.get(subject = sub, suffix = 'events', extension = 'tsv')
    event_df = pd.concat([f.get_df() for f in event_fs])
    max_tone_dur = np.max(event_df.duration)

    # create list to collect epochs from both tasks
    epochs = []

    tasks = ['streaming', 'discrimination']
    for task in tasks:

        bids_path = BIDSPath(
            root = layout.root,
            subject = sub,
            task = task,
            datatype = 'eeg'
        )
        raw = read_raw_bids(bids_path, verbose = False).load_data()
        events, event_ids = mne.events_from_annotations(raw)
        metadata = layout.get(
            subject = sub,
            task = task,
            suffix = 'events',
            extension = 'tsv'
        )[0].get_df()
        if fake:
            # shift event times by 1/2 the cardiac cycle
            # so we can make an "FFR" where there is no tone
            # to check for cardiac artifacts
            ibi = metadata.duration * 8 # tones are ~1/8 of IBI
            events[:,0] += np.round(ibi * raw.info['sfreq'] / 2).astype(int)

        # filter out electrical noise and harmonics
        lf = raw.info['line_freq'] # this came from BIDS sidecar!
        line_freqs = np.arange(lf, PASSBAND[1], lf)
        # but keep harmonics of frequency of interest
        tone_freq = metadata[metadata.tone_type == 'B'].frequency.iloc[0]
        line_freqs = line_freqs[line_freqs % tone_freq != 0]
        raw = raw.notch_filter(line_freqs, picks = ['eeg'])
        # then filter to frequency band that should contain FFR
        raw = raw.filter(l_freq = PASSBAND[0], h_freq = PASSBAND[1])

        # now split into epochs
        epo = mne.Epochs(
            raw,
            events, event_id = event_ids,
            metadata = metadata, # remember to hang onto metadata!
            tmin = -1*max_tone_dur,
            tmax = max_tone_dur,
            baseline = (-1*max_tone_dur, 0),
            preload = True
        )
        # and remove non-B tones
        epo = epo[epo.metadata.tone_type == 'B']
        # and store to combine with other task's data
        epochs.append(epo)

    # combine epochs across tasks into one mne.Epochs object
    if TASK_TO_USE == 'both':
        epochs = mne.concatenate_epochs(epochs)
    else: # use just discrimination task, which has no A tones between B tones
        epochs = epochs[np.where(np.array(tasks) == TASK_TO_USE)[0][0]]

    # reject trials that violate amplitude threshold
    epochs = epochs.drop_bad(reject = dict(eeg = THRES))

    ffr_amps = []

    for condition in ['systole', 'diastole']:

        # compute time domain FFR for each condition
        ffr = epochs[condition].average()
        # and save them to disk
        fpath = sink.get_path(
            subject = sub,
            task = None,
            desc = condition,
            suffix = 'ave',
            extension = '.fif.gz'
        )
        ffr.save(fpath)

        # compute dB vs. baseline
        psd_args = dict(fmin = PASSBAND[0], fmax = PASSBAND[1])
        psd_before = ffr.compute_psd(tmax = 0, **psd_args)
        psd_after = ffr.compute_psd(tmin = 0, **psd_args)
        dB = 10*np.log10(psd_after.get_data() / psd_before.get_data())[0, :]
        # and save
        fpath = sink.get_path(
            subject = sub,
            task = None,
            desc = condition,
            suffix = 'power',
            extension = '.tsv'
        )
        dB_df = pd.DataFrame(dict(freq = psd_after.freqs, dB = dB))
        dB_df.to_csv(fpath, sep = '\t', index = False)

        # extract metric of interest
        idx = np.argmin(np.abs(psd_after.freqs - tone_freq))
        dB_of_interest = dB[idx]
        ffr_amps.append(dict(
            subject = sub,
            condition = condition,
            amplitude = dB_of_interest,
            n = ffr.nave # number of trials
        ))

    amplitudes = pd.DataFrame(ffr_amps)
    fpath = sink.get_path(
        subject = sub,
        task = None,
        desc = '%dHz'%tone_freq,
        suffix = 'power',
        extension = '.tsv'
    )
    amplitudes.to_csv(fpath, sep = '\t', index = False)

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
            main(layout, s)
    else:
        print('Processing sub-%s...'%sub)
        main(layout, sub)
    t1 = time()
    print('Done in %.02f minutes.'%((t1 - t0)/60))
