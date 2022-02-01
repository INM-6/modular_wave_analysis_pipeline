import neo
import os
import argparse
import numpy as np
import pandas as pd
import re
from utils.io import load_neo, save_plot
from utils.parse import none_or_str
from utils.neo import remove_annotations


if __name__ == '__main__':
    CLI = argparse.ArgumentParser(description=__doc__,
                   formatter_class=argparse.RawDescriptionHelpFormatter)
    CLI.add_argument("--data", nargs='?', type=str, required=True,
                     help="path to input data in neo format")
    CLI.add_argument("--output", nargs='?', type=str, required=True,
                     help="path of output file")
    CLI.add_argument("--output_img", nargs='?', type=none_or_str, default=None,
                     help="path of output image file")
    CLI.add_argument("--event_name", "--EVENT_NAME", nargs='?', type=str, default='wavefronts',
                     help="name of neo.Event to analyze (must contain waves)")
    CLI.add_argument("--ignore_keys", "--IGNORE_KEYS", nargs='+', type=str, default=[],
                     help="neo object annotations keys to not include in dataframe")
    CLI.add_argument("--include_keys", "--INCLUDE_KEYS", nargs='+', type=str, default=[],
                     help="neo object annotations keys to include in dataframe")
    CLI.add_argument("--profile", "--PROFILE", nargs='?', type=none_or_str, default=None,
                     help="profile name")
    args, unknown = CLI.parse_known_args()
    args.ignore_keys = [re.sub('[\[\],\s]', '', key) for key in args.ignore_keys]
    args.include_keys = [re.sub('[\[\],\s]', '', key) for key in args.include_keys]
    if len(args.include_keys):
        args.ingnore_keys = []

    block = load_neo(args.data)

    asig = block.segments[0].analogsignals[0]
    evts = block.filter(name=args.event_name, objects="Event")[0]

    df = pd.DataFrame(evts.labels, columns=[f'{args.event_name}_id'])
    df['channel_id'] = evts.array_annotations['channels']
    args.ignore_keys += ['channels']

    remove_annotations(evts, del_keys=['nix_name', 'neo_name']+args.ignore_keys)
    remove_annotations(asig, del_keys=['nix_name', 'neo_name']+args.ignore_keys)

    for key, value in evts.annotations.items():
        if not len(args.include_keys) or key in args.include_keys:
            df[key] = [value] * len(df.index)

    for key, value in evts.array_annotations.items():
        if not len(args.include_keys) or key in args.include_keys:
            if key not in df.columns:
                df[key] = value

    for key, value in asig.annotations.items():
        if not len(args.include_keys) or key in args.include_keys:
            if key not in df.columns:
                df[key] = [value] * len(df.index)

    for key, value in asig.array_annotations.items():
        if not len(args.include_keys) or key in args.include_keys:
            if key not in df.columns:
                df[key] = value[df.index]

    df['profile'] = [args.profile] * len(df.index)
    df['sampling_rate'] = asig.sampling_rate
    df['recording_length'] = asig.t_stop - asig.t_start
    df['dim_x'] = int(max(asig.array_annotations['x_coords']))+1
    df['dim_y'] = int(max(asig.array_annotations['y_coords']))+1

    df.to_csv(args.output)

    # ToDo
    save_plot(args.output_img)