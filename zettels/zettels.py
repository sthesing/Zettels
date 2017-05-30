#! /usr/bin/env python3

# -*- coding: utf8 -*-
## Copyright (c) 2017 Stefan Thesing
##
##This file is part of Zettels.
##
##Zettels is free software: you can redistribute it and/or modify
##it under the terms of the GNU General Public License as published by
##the Free Software Foundation, either version 3 of the License, or
##(at your option) any later version.
##
##Zettels is distributed in the hope that it will be useful,
##but WITHOUT ANY WARRANTY; without even the implied warranty of
##MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##GNU General Public License for more details.
##
##You should have received a copy of the GNU General Public License
##along with Zettels. If not, see http://www.gnu.org/licenses/.

"""
Zettels is a command line tool implementing Niklas Luhmann's system of a "Zettelkasten".
"""

__version__ = '0.2.1'
__author__  = 'Stefan Thesing'

# Libraries
import argparse
import collections.abc
import logging
import os
import sys
import xdg.BaseDirectory
import yaml

# local imports
from zettels.zettelparser import Zettelparser
from zettels.zettelkasten import Zettelkasten
import zettels.zettels_setup as setup

# Module variables
settings_base_dir = xdg.BaseDirectory.save_config_path('Zettels')
logger = logging.getLogger('Zettels')


#################################
# Internal methods used by main #
#################################

def _connect_dev_arguments(parser):
    # Standard settings dir:
    
    
    # Command line arguments that are "Developer options" should be available
    # in all subcommands. To make it available to both parser and subparsers,
    # and to avoid redundant code, this function connects them to the specified
    # argument parser.
    
    group_dev = parser.add_argument_group('Developer options', 'These are \
        probably only useful for developers.')
    
    group_dev.add_argument('-s', '--settings',  help='relative or absolute \
        path to a settings file. Useful if you have several distinct \
        collections of Zettels (e.g. one for testing the program and one \
        you actually use.). Default is "' + settings_base_dir + '/zettels.cfg.yaml"',
        default= settings_base_dir + '/zettels.cfg.yaml')
    group_dev.add_argument('-v', '--verbose', help='output verbose logging messages',
        action="store_true")

def _setup_logging(verbose=False):
    logger = logging.getLogger('Zettels')
    
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - ' 
        + '%(name)s - '
        + '%(levelname)s - '
        + '%(message)s'
        ))
    
    logger.addHandler(handler)
    
    return logger

def _read_settings(f):
    try:
        f = open(f, 'r')
        settings = yaml.safe_load(f.read())
        f.close()
        # We should have received a Dictionary or other mapping type
        if isinstance(settings, collections.abc.Mapping):
            rootdir = settings['rootdir']
            # check wether rootdir exists
            if os.path.exists(os.path.abspath(os.path.expanduser(rootdir))):
                rootdir = os.path.abspath(os.path.expanduser(rootdir))
            else:
                # TODO Raise an appropriate error
                logger.error("Rootdir path: " + 
                      os.path.abspath(os.path.expanduser(rootdir)) + 
                      " doesn't exist. Exiting")
                exit()
            indexfile = settings['indexfile']
            indexfile = os.path.abspath(os.path.expanduser(indexfile))
            outputformat = settings['outputformat']
            return rootdir, indexfile, outputformat
        else:
            print("There seems to be a problem with your settings \
                file. Zettels expected to receive a dictionary or other \
                mapping type. Received" , str(type(settings)), " instead.")
            exit()
    except FileNotFoundError:
        logger.error(sys.exc_info()[1])
        #print(sys.exc_info()[2])
        logger.error("Settings file not found. Please specify a correct one or run \
            Zettels with the --setup parameter to generate one.")
        exit()
    except yaml.YAMLError:
        logger.error("There seems to be a problem with your settings file. Is it \
            valid YAML?")
        logger.error(sys.exc_info()[1])
        exit()
    except KeyError:
        logger.error("There seems to be a problem with your settings file. At least \
            one required setting is missing:" , str(sys.exc_info()[1]))
        exit()
    
def _query(args):
    logger.debug(args)
    
    # Next, let's read the settings file. _read_settings(settings) does the
    # error handling
    rootdir, indexfile, outputformat = _read_settings(args.settings)
    # If we're still running, we have valid settings.
    logger.debug("Root dir: " + rootdir)
    logger.debug("Index file: " + indexfile)
    
    if args.update:
        index = Zettelparser.update_index(rootdir)
        logger.debug("Writing index to file " + indexfile)
        Zettelparser.write_index(index, indexfile)
        logger.debug("Done")
    else:
        logger.debug("Reading index...")
        try:
            index = Zettelparser.read_index(indexfile)
        except FileNotFoundError:
            logger.error(sys.exc_info()[1])
            logger.error("If you run Zettels with these settings for the "
                + "first time, please run it once without any arguments, "
                + "first. Or set the --update flag.")
            logger.error("Otherwise, please check your settings or run " 
                + "Zettels with the --setup parameter to generate new settings.")
            logger.error("Exiting")
            exit()
        logger.debug("Done")
    
    
    # Initialize a Zettelkasten
    zk = Zettelkasten(index, rootdir)
    # Now, let's do what we're told:
        
    if not args.Zettel:
        for entry in zk.get_list_of_zettels(as_output=True, 
                                            outputformat=outputformat):
            print(entry)
    else:
        if not args.followups and not args.targets and not args.incoming:
            # If no output flag is set, all of them are set.
            args.followups = True
            args.targets = True
            args.incoming = True
        
        if args.followups:
            print("Followups:")
            for entry in zk.get_followups_of(args.Zettel, 
                                             as_output=True, 
                                             outputformat=outputformat):
                print(entry)
        
        if args.targets:
            print("Targets:")
            for entry in zk.get_targets_of(args.Zettel, 
                                           as_output=True,
                                           outputformat=outputformat):
                print(entry)
        
        if args.incoming:
            print("Incoming links:")
            for entry in zk.get_incoming_of(args.Zettel, 
                                            as_output=True,
                                            outputformat=outputformat):
                print(entry)

def _parse(args):
    logger.debug(args)
    
    # First check the --setup argument, because it overrides everything else
    if args.setup:
        setup.generate_settings()

    # Next, let's read the settings file. _read_settings(settings) does the
    # error handling
    rootdir, indexfile, _ = _read_settings(args.settings)
    # If we're still running, we have valid settings.
    logger.debug("Root dir: " + rootdir)
    logger.debug("Index file: " + indexfile)
    
    index = Zettelparser.update_index(rootdir)
    logger.debug("Writing index to file " + indexfile)
    Zettelparser.write_index(index, indexfile)
    logger.debug("Done")

#################################
# Main function                 #
#################################

if __name__ == "__main__":
    main()
    
def main():
    """
    Zettels is a little tool to index markdown files. It reads yaml-metadata 
    blocks as defined by pandoc and parses the hyperlinks in each file.
    The resulting index contains the metadata and the targets of the 
    hyperlinks.
    It's intended to be used for a "Zettelkasten" like Niklas Luhmann used it.
    """ 
    #################################################
    # Define command line arguments                 #
    #################################################
    
    # Standard settings dir:
    settings_base_dir = xdg.BaseDirectory.save_config_path('Zettels')
    
    # Define the parser
    parser = argparse.ArgumentParser(description=
        "Zettels is an implementation of Niklas Luhmann's system of a \
        Zettelkasten.")
    parser.set_defaults(func=_parse)
    
    # top-level parameters
    # Setup
    group_setup = parser.add_argument_group('Setup option')
    # The overriding setup flag
    group_setup.add_argument('--setup',  help='interactively generate a new \
        settings file. If this argument is given, all others are ignored.',
        action="store_true")
    
    _connect_dev_arguments(parser)
   
    # Container for the subparser
    subparsers = parser.add_subparsers(title="Commands")
    
    # Subparser for querying the index
    q_parser = subparsers.add_parser('query', aliases=['q'], 
        help='query the Zettelkasten index, run Zettels with \
            "query --help" for details.')
    q_parser.set_defaults(func=_query)
    
    group_general = q_parser.add_argument_group('General options')
    # One (optional) postional argument, which is a Zettel
    group_general.add_argument('Zettel', 
                        metavar='ZETTEL', 
                        nargs='?',
                        help='Optional: specify a Zettel file.')
    group_general.add_argument('-u', '--update', action="store_true",
        help='Update the index before the query.')
    
    # Output arguments
    group_output = q_parser.add_argument_group('Output options', 'Flags to \
        determine the output. They only take effect if the ZETTEL argument is \
        given. If none of these flags is set, the program outputs the an \
        overview over the specified Zettel, equivalent to setting all of \
        these flags.')
    group_output.add_argument('-f', '--followups', action="store_true",
        help='Output followups of the specified Zettel.')
    group_output.add_argument('-t', '--targets', action="store_true",
        help='Show the targets of hyperlinks in the specified Zettel.')
    group_output.add_argument('-i', '--incoming', action="store_true",
        help='Show all Zettels that link to the specified Zettel.')
        
    # Developer options
    _connect_dev_arguments(q_parser)
    
    #################################################
    # Parse and process command line arguments      #
    #################################################
    
    args = parser.parse_args()
    
    # Perpare the logger
    logger = _setup_logging(args.verbose)
    
    # Call the respective function for each subcommand
    # That is _parse(args) for the main command and _query(args) for the query 
    # subcommand
    args.func(args)
        
