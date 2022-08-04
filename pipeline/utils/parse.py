import numpy as np
import warnings
import re
from pathlib import Path
import sys
utils_path = str((Path(__file__).parent / '..').resolve())
sys.path.append(utils_path)
from utils.io import load_neo


def get_base_type(datatype):
    if hasattr(datatype, 'dtype'):
        datatype = datatype.dtype
    elif not type(datatype) == type:
        datatype = type(datatype)

    if datatype == list:
        warnings.warn("List don't have a defined type!")

    if np.issubdtype(datatype, np.integer):
        return 'int'
    elif np.issubdtype(datatype, float):
        return 'float'
    elif np.issubdtype(datatype, str):
        return 'str'
    elif np.issubdtype(datatype, complex):
        return 'complex'
    elif np.issubdtype(datatype, bool):
        return 'bool'
    else:
        warnings.warn(f"Did not recognize type {datatype}!")
    return None


def guess_type(string):
    try:
        out = int(string)
    except:
        try:
            out = float(string)
        except:
            out = str(string)
            if out == 'None':
                out = None
            elif out == 'True':
                out = True
            elif out == 'False':
                out = False
    return out


def str2dict(string):
    """
    Transforms a str(dict) back to dict
    """
    if string[0] == '{':
        string = string[1:]
    if string[-1] == '}':
        string = string[:-1]
    my_dict = {}
    # list or tuple values
    brackets = [delimiter for delimiter in ['[',']','(',')']
                if delimiter in string]
    if len(brackets):
        for kv in string.split("{},".format(brackets[1])):
            k,v = kv.split(":")
            v = v.replace(brackets[0], '').replace(brackets[1], '')
            values = [guess_type(val) for val in v.split(',')]
            if len(values) == 1:
                values = values[0]
            my_dict[k.strip()] = values
    # scalar values
    else:
        for kv in string.split(','):
            k,v = kv.split(":")
            my_dict[k.strip()] = guess_type(v.strip())
    return my_dict


def parse_string2dict(kwargs_str, **kwargs):
    if type(kwargs_str) == list:
        if len(kwargs_str) == 0:
            return {}
        elif len(kwargs_str) == 1:
            kwargs = kwargs_str[0]
        else:
            kwargs = ''.join(kwargs_str)[1:-1]
    else:
        kwargs = str(kwargs_str)
    if guess_type(kwargs) is None:
        return {}

    my_dict = {}
    # match all nested dicts
    pattern = re.compile("[\w\s]+:{[^}]*},*")
    for match in pattern.findall(kwargs):
        nested_dict_name, nested_dict = match.split(":{")
        nested_dict = nested_dict[:-1]
        my_dict[nested_dict_name] = str2dict(nested_dict)
        kwargs = kwargs.replace(match, '')
    # match entries with word value, list value, or tuple value
    pattern = re.compile("[\w\s]+:(?:[\w\.\s\/\-\&\+]+|\[[^\]]+\]|\([^\)]+\))")
    for match in pattern.findall(kwargs):
        my_dict.update(str2dict(match))
    return my_dict


# def ordereddict_to_dict(input_dict):
#     if isinstance(input_dict, dict):
#         for k, v in input_dict.items():
#             if isinstance(v, dict):
#                 input_dict[k] = ordereddict_to_dict(v)
#         return dict(input_dict)
#     else:
#         return input_dict


def none_or_X(value, dtype):
    if value is None or not bool(value) or value == 'None':
        return None
    try:
        return dtype(value)
    except ValueError:
        return None

none_or_int = lambda v: none_or_X(v, int)
none_or_float = lambda v: none_or_X(v, float)
none_or_str = lambda v: none_or_X(v, str)
str_list = lambda v: s.split(',')


def parse_plot_channels(channels, input_file):
    channels = channels if isinstance(channels, list) else [channels]
    channels = [none_or_int(channel) for channel in channels]
    # ToDo:
    #   * check is channel exists, even when there is no None
    #   * use annotation channel ids instead of array indices
    if None in channels:
        dim_t, channel_num = load_neo(input_file, object='analogsignal',
                                      lazy=True).shape
        for i, channel in enumerate(channels):
            if channel is None or channel >= channel_num:
                channels[i] = np.random.randint(0,channel_num)
    return channels


def determine_spatial_scale(coords):
    coords = np.array(coords)
    dists = np.diff(coords[:,0])
    dists = dists[np.nonzero(dists)]
    return np.min(dists)


def determine_dims(coords):
    # spatial_scale = determine_spatial_scale(coords)
    # int_coords = np.round(np.array(coords)/spatial_scale).astype(int)
    int_coords = np.round(np.array(coords)).astype(int)
    dim_x, dim_y = np.max(int_coords[:,0])+1, np.max(int_coords[:,1])+1
    return dim_x, dim_y
