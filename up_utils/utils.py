# -*- coding: utf-8 -*-
"""
created on Fri May 15 12:00:00 2020

@author: Kra33

Some utilities shared by multiple files
"""

import shutil
import random
import pathlib
import numpy as np
import pandas as pd
import psutil

PROGRESS_BAR_SIZE = 60


def progress_bar(
        infostring,
        size=PROGRESS_BAR_SIZE):
    """
    progress_bar

    Returns a function which displays a progress bar with
    preceding text `infostring` and of total width `size`.

    Arguments:
    infostring -- String to display before the progress bar
    size -- The total width of the progress bar, including infostring
    """

    try:
        # Attempt to get terminal size. Will fail in non-interactive mode
        size = shutil.get_terminal_size(
            fallback=(PROGRESS_BAR_SIZE, 1)).columns
    except OSError:
        # We have already supplied a default size value
        pass

    infostring += ' '
    width = size - len(infostring)
    width -= 2  # Allowing for '[' and ']'

    def progress(blocksize, blocks, filesize=None):
        """
        progress

        Displays a progress bar, where the total progress is
          (blocksize*blocks)/filesize
        or
          blocksize/blocks
        depending on whether filesize was supplied. The former form
        is a valid function for the `urlretrieve` downloading function
        (from urllib.request). The latter form is intended for a simple
        progress bar where the percentage of completion is known.

        Arguments:
        blocksize -- The size of each block downloaded
        blocks -- Number of blocks downloaded
        filesize -- The total filesize of file on remote
        """

        if not filesize:
            filesize = blocks
            blocks = 1

        print('\b'*(width + 2 + len(infostring)), end='')
        print(infostring, end='')
        print("[", end='')
        current_progress = int(blocksize*blocks/(filesize-1)*width)
        print('#'*current_progress, end='')
        print('-'*(width-current_progress), end='')
        print("]", end='', flush=True)

        # Print newline after finishing
        if current_progress >= width:
            print("", flush=True)

    # Function currying, using python's closures
    return progress


def to_list(str_list):
    """
    to_list

    Create a new list from the representative `str_list`.

    Arguments:
    str_list -- A list, in string format.

    Returns:
    A list, represented by `str_list`.
    """

    if isinstance(str_list, list):
        return str_list
    if not not_nan(str_list):
        return []
    trimmed = str_list[1:-1]
    if len(trimmed) == 0:
        return []
    return map(int, trimmed.split(','))


def is_nan(nan):
    """
    is_nan

    Convenience function for positive nan_checking.
    """
    return not not_nan(nan)


def not_nan(nan):
    """
    not_nan

    Arguments:
    nan -- Possibly NaN

    Returns:
    True if `nan` is truthful.
    False if `nan` is not NaN or empty array, or falsey.
    """

    if isinstance(nan, float) and np.isnan(nan):
        return False
    if isinstance(nan, str) and nan.replace(' ', '') == '[]':
        return False
    if nan:
        return True
    return False


def __get_data_frame(data):
    """ Ensure data is a data frame. Make it so if data is a path. """
    if isinstance(data, str):
        data = pd.read_csv(
            data,
            index_col=0,
            sep='|',
            )
    assert isinstance(data, pd.DataFrame)
    return data


def get_masters(data):
    """ Return set of masters in data (path, or data frame) """
    data = __get_data_frame(data)
    duplicates = get_duplicates(data)
    masters = set(filter(
        lambda x: not_nan(data.loc[x, 'duplicates']),
        data.index,
        ))
    # Remove masters which are also duplicates
    return masters - duplicates


def get_duplicates(data):
    """ Return set of duplicates in data (path, or data frame) """
    data = __get_data_frame(data)
    return set(filter(
        lambda x: not_nan(data.loc[x, 'master']),
        data.index,
        ))


def get_singletons(data):
    """ Return set of singletons in data (path, or data frame) """
    data = __get_data_frame(data)
    return set(filter(
        lambda x: (is_nan(data.loc[x, 'master'])
                   and is_nan(data.loc[x, 'duplicates'])),
        data.index,
        ))


def _get_orphans(dataframe):
    """
    Return the set of bugs in `dataframe` whose master is not in `dataframe`
    """
    orphans = set()
    for bug in dataframe.index:
        master = dataframe.loc[bug, 'master']
        if not_nan(master) and master not in dataframe.index:
            orphans.add(bug)
    return orphans


def remove_orphans(dataframe, copy=True):
    """
    remove_orphans

    Some duplicates have a master not in the dataframe.
    This can happen when when downloading bugs, bug downloading is aborted
    before their master has been downloaded.  Here we remove these orphaned
    duplicates.

    Arguments:
    dataframe -- A data frame holding bugs
    copy -- Whether or not to work on a copy of the dataframe

    Returns:
    If `copy` is True, then a new dataframe where orphaned duplicates
    have been removed. If `copy` is False, then orphaned duplicates have
    been removed from dataframe (mutating) and the datframe (same) returned.
    """

    if copy:
        dataframe = dataframe.copy()

    # Sometimes master-duplicate relations form trees deeper than 1. Thus we
    # may need to do several passes of orphan removal, since on a given pass
    # a new orphan may have been created.
    size_pre = len(dataframe.index)
    size_post = -1
    while size_pre != size_post:
        size_pre = len(dataframe.index)
        orphans = _get_orphans(dataframe)
        dataframe.drop(orphans, inplace=True)
        size_post = len(dataframe.index)
    return dataframe


def remove_missing_duplicates(dataframe, copy=True):
    """
    remove_missing_duplicates

    Some bugs have non-existent duplicates
    e.g. https://bugzilla.mozilla.org/rest/bug?id=1111
    which has a duplicate 1234705, but it does not exist.
    Here we remove these non-existent references in our dataset.

    Arguments:
    dataframe -- A data frame holding bugs
    copy -- Whether or not to work on a copy of the dataframe

    Returns:
    If `copy` is True, then a new dataframe where references to missing
    duplicates, have been removed. If `copy` is False, then references to
    missing duplicates have been removed from the dataframe (mutating) and the
    datframe (same) returned.
    """

    if copy:
        dataframe = dataframe.copy()

    size_pre = len(dataframe.index)
    size_post = -1
    while size_pre != size_post:
        size_pre = len(dataframe.index)
        for node in dataframe.index:
            duplicates = set(to_list(dataframe.loc[node, "duplicates"]))
            missing_duplicates = set()
            # Linearly search for missing duplicate
            for duplicate in duplicates:
                if duplicate not in dataframe.index:
                    missing_duplicates.add(duplicate)
            # Handle missing duplicates
            if len(missing_duplicates) != 0:
                present_duplicates = duplicates - missing_duplicates
                duplicates_str = ''
                if len(present_duplicates) == 0:
                    duplicates_str = "[]"
                else:
                    duplicates_str = "[{}]".format(
                        str(present_duplicates)[1:-1].replace(' ', ''))
                dataframe.loc[node, "duplicates"] = duplicates_str
        size_post = len(dataframe.index)
    return dataframe


def print_bug_group(bug, data=None):
    """
    Print a regex string of duplicates of `bug` to use in TensorBoard Projector
    search
    """
    # Printing bugs which are missing is not a problem here
    data = __get_data_frame(data)

    # Find master of duplicates
    master = bug
    if not_nan(data.loc[bug, 'master']):
        master = data.loc[bug, 'master']

    # Create duplicate set
    duplicates = to_list(data.loc[master, 'duplicates'])
    bugs = set(list(duplicates) + [int(master)])

    # Print regex string
    print("^(", end='')
    for bug in bugs:  # pylint: disable=redefined-argument-from-local
        print(f"{bug}|", end='')
    print('\b)')  # Remove extra |


def print_bug_groups(N=1, data=None):  # pylint: disable=invalid-name
    """ Print `N` bug groups from `data` """
    data = __get_data_frame(data)
    for bug in random.sample(list(data.index), N):
        print_bug_group(bug, data)


def delete_by_glob(*args, directory='./'):
    """ Remove file(s) specified by a POSIX glob, from dir `directory` """
    files = []
    path = pathlib.Path(directory)
    for glob in args:
        files.extend(path.glob(glob))
    for f in files:  # pylint: disable=invalid-name
        f.unlink(missing_ok=True)


def virt_mem():
    """ Return free memory in GB """
    return psutil.virtual_memory().free/2**33
