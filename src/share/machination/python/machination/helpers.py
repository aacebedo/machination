#
# Machination
# Copyright (c) 2014, Alexandre ACEBEDO, All rights reserved.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3.0 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library.
#
"""
This file contains a set of helpers used in machination
"""
import random
import os
import functools
import socket
import fcntl
import struct
import array
import hashlib

from machination.exceptions import InvalidArgumentNumberError
from machination.exceptions import ArgumentValidationError


def ordinal(num):
    '''
    Returns the ordinal number of a given integer, as a string.
    eg. 1 -> 1st, 2 -> 2nd, 3 -> 3rd, etc.
    '''
    if 10 <= num % 100 < 20:
        return '{0}th'.format(num)
    else:
        val = {1: 'st', 2: 'nd', 3: 'rd'}.get(num % 10, 'th')
        return '{0}{1}'.format(num, val)


def accepts(*accepted_arg_types):
    '''
    A decorator to validate the parameter types of a given function.
    It is passed a tuple of types. eg. (<type 'tuple'>, <type 'int'>)

    Note: It doesn't do a deep check, for example checking through a
          tuple of types. The argument passed must only be types.
    '''
    def accept_decorator(validate_function):
        """
        Decorator acceptance function
        """
        # Check if the number of arguments to the validator
        # function is the same as the arguments provided
        # to the actual function to validate. We don't need
        # to check if the function to validate has the right
        # amount of arguments, as Python will do this
        # automatically (also with a TypeError).
        @functools.wraps(validate_function)
        def decorator_wrapper(*function_args, _):
            """
            Decorator wrapper
            """
            if len(accepted_arg_types) is not len(accepted_arg_types):
                raise InvalidArgumentNumberError(validate_function.__name__)

            # We're using enumerate to get the index, so we can pass the
            # argument number with the incorrect type to
            # ArgumentValidationError.
            for arg_num, (actual_arg, accepted_arg_type) \
              in enumerate(zip(function_args, accepted_arg_types)):

                if accepted_arg_type is not None and \
                not isinstance(actual_arg, accepted_arg_type):
                    ord_num = ordinal(arg_num + 1)
                    raise ArgumentValidationError(ord_num,
                                                  validate_function.__name__,
                                                  accepted_arg_type)

            return validate_function(*function_args)
        return decorator_wrapper
    return accept_decorator


def list_path(dir_to_list):
    """
    Get the list of files in the given directory
    """
    if os.path.exists(dir_to_list):
        return [os.path.join(dir_to_list, f) for f in os.listdir(dir_to_list)]
    else:
        return []

def generate_random_mac():
    """
    Generate a randomized MAC
    """
    mac = [0x00, 0x16, 0x3e,
           random.randint(0x00, 0x7f),
           random.randint(0x00, 0xff),
           random.randint(0x00, 0xff)]
    print_hex = lambda val: "%02x" % val
    return ':'.join([print_hex(el) for el in mac])


def generate_hash_of_dir(directory, hash_value):
    """
    Compute the hash of a directory
    """
    if os.path.exists(directory):
        for root, _, files in os.walk(directory):
            for names in files:
                filepath = os.path.join(root, names)
                generate_hash_of_file(filepath, hash_value)


def generate_hash_of_file(file_path, hash_value):
    """
    Compute the hash of a file
    """
    if os.path.exists(file_path):
        file_to_process = open(file_path, 'rb')
        while True:
            buf = file_to_process.read(4096)
            if not buf:
                break
            hash_value.update(hashlib.sha1(buf).hexdigest())
        file_to_process.close()


def get_all_net_interfaces():
    """
    Get all network interface of the host
    """
    max_possible = 128  # arbitrary. raise if needed.
    vals = max_possible * 32
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    names = array.array('B', '\0' * vals)
    outbytes = struct.unpack('iL', fcntl.ioctl(
        sock.fileno(),
        0x8912,  # SIOCGIFCONF
        struct.pack('iL', vals, names.buffer_info()[0])
    ))[0]
    namestr = names.tostring()
    lst = []
    for i in range(0, outbytes, 40):
        name = namestr[i:i + 16].split('\0', 1)[0]
        if name != "lo":
            lst.append(name)
    return lst
