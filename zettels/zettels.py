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

__version__ = '0.5.0'
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
    # Command line arguments that are "Developer options" should be available
    # in subcommands, too. To make it available to both parser and 
    # eventual subparsers, while avoiding redundant code, this function 
    # connects them to the parser specified as this function's parameter.
    
    #group_dev = parser.add_argument_group('Developer options', 'These are \
    #    probably only useful for developers.')
    group_dev = parser.add_argument_group('Developer options')
    
    group_dev.add_argument('-s', '--settings',  help='relative or absolute \
        path to a settings file. Useful if you have several distinct \
        collections of Zettels (e.g. one for testing the program and one \
        you actually use.). Default is "' + settings_base_dir + '/zettels.cfg.yaml"',
        default= settings_base_dir + '/zettels.cfg.yaml')
    group_dev.add_argument('-v', '--verbose', help='Output verbose logging \
        messages to stdout. VERY verbose messages.',
        action="store_true")

def _setup_logging(verbose=False):
    logger = logging.getLogger('Zettels')
    
    if verbose:
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
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
            outputformat    = settings['outputformat']
            prettyformat    = settings['prettyformat']
            ignore_patterns = settings['ignore']
            return rootdir, indexfile, outputformat, prettyformat, ignore_patterns
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
    rootdir, indexfile, outputformat, prettyformat, ignore_patterns = _read_settings(args.settings)
    # If we're still running, we have valid settings.
    logger.debug("Root dir: " + rootdir)
    logger.debug("Index file: " + indexfile)
    
    if args.update:
        index = Zettelparser.update_index(rootdir, ignore_patterns=ignore_patterns)
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
    # When no Zettel argument is given, this implies the pretty flag, 
    # but only of -o is not used.
        args.pretty = True
    else:
    # If no output flag is set, all them get set. This also implies
    # the pretty flag
        if not args.followups and not args.links and not args.incoming:
            # If no output flag is set, all them get set. The pretty flag
            # as well.
            args.followups = True
            args.links = True
            args.incoming = True
            args.pretty = True
    
    # Did the user set the output flag?
    if args.output:
        outputformat = args.output
    #Has the pretty flag been set (explicitly or implicitly)?
    elif args.pretty:
        outputformat = prettyformat
      
    if not args.Zettel:
        for entry in zk.get_list_of_zettels(as_output=True, 
                                            outputformat=outputformat):
            print(entry)
    else:
        # In case our zettel arguments came from a pipe via stdin,
        # it's not a list, but a io.TextIOWrapper. We'll want to know
        # it's length before iterating through it, so convert it into 
        # a list.
        args.Zettel = list(args.Zettel)
        for zettel_arg in args.Zettel:
            # In case our zettel arguments came from a pipe via stdin,
            # they each end with a line break. We have to strip those away.
            zettel_arg = zettel_arg.rstrip()
            # If we're dealing with more than one zettel argument, let's 
            # structure output a bit:
            if len(args.Zettel) > 1: print("[", zettel_arg, "]")
                
            if args.followups:
                if args.pretty: print("[", "- Followups:" , "]")
                for entry in zk.get_followups_of(zettel_arg, 
                                                 as_output=True, 
                                                 outputformat=outputformat):
                    print(entry)
            
            if args.links:
                if args.pretty: print("[", "- Link targets:" , "]")
                for entry in zk.get_targets_of(zettel_arg, 
                                               as_output=True,
                                               outputformat=outputformat):
                    print(entry)
            
            if args.incoming:
                if args.pretty: print("[", "- Incoming links:" , "]")
                for entry in zk.get_incoming_of(zettel_arg, 
                                                as_output=True,
                                                outputformat=outputformat):
                    print(entry)

def _parse(args):
    logger.debug(args)
    
    # Read the settings file. _read_settings(settings) does the
    # error handling
    rootdir, indexfile, _, _, ignore_patterns = _read_settings(args.settings)
    # If we're still running, we have valid settings.
    logger.debug("Root dir: " + rootdir)
    logger.debug("Index file: " + indexfile)
    
    index = Zettelparser.update_index(rootdir, ignore_patterns=ignore_patterns)
    logger.debug("Writing index to file " + indexfile)
    Zettelparser.write_index(index, indexfile)
    logger.debug("Done")

#################################
# Main function                 #
#################################
    
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
    parser.set_defaults(func=_query)
    
    # top-level parameters
    parser.add_argument('--setup',  help='interactively generate a new \
        settings file. If this argument is given, all others are ignored.',
        action="store_true")
    parser.add_argument('-su', '--silentupdate', action="store_true",
        help='Silently build or update the index and exit.')
    
    group_query = parser.add_argument_group('Query options')
    # One (optional) postional argument, which is a Zettel
    
    if sys.stdin.isatty():
        # Interactive, don't wait for the user if he or she hasn't
        # given any arguments
        zettel_arg_default = None
    else:
        # Piped, let's see what sys.stdin gives us.
        zettel_arg_default = sys.stdin
    
    group_query.add_argument('Zettel', 
                        metavar='ZETTEL', 
                        nargs='*',
                        default=zettel_arg_default,
                        help='Optional: specify one or several Zettel \
                        files. If no Zettel \
                        file is given, zettels will list the titles and \
                        paths of all the Zettels in the Zettelkasten \
                        (implying the --pretty flag).')
    group_query.add_argument('-u', '--update', action="store_true",
        help='Update the index before the query.')
    
    
    # Output arguments
    group_output = parser.add_argument_group('Query output options', 'Flags to \
        determine the output. They only take effect if at least one \
        ZETTEL argument is given. If none of these flags is set, the \
        program outputs an overview over the specified Zettel(s), \
        equivalent to setting all of these flags. Furthermore, this \
        overview implicitly sets the --pretty flag for output format.')
    group_output.add_argument('-f', '--followups', action="store_true",
        help='Output followups of the specified Zettel(s).')
    group_output.add_argument('-l', '--links', action="store_true",
        help='Show the targets of hyperlinks in the specified Zettel(s).')
    group_output.add_argument('-i', '--incoming', action="store_true",
        help='Show all Zettels that link to the specified Zettel(s).')
    
    # Output format
    # It actually should be a mutually exclusive group, but that currently
    # supports neither title nor description...
    #group_format = q_parser.add_mutually_exclusive_group()
    group_format = parser.add_argument_group('Output format options', 'Tweak \
        output format. Output is formatted as a Python Format String, (see \
        https://docs.python.org/3/library/string.html#format-string-syntax \
        for details). The output of the query command gives two fields that \
        can be accessed in this manner: title as "{0[0]}" and path as "{0[1]}". \
        In the settings file, two output formats are specified: \
        a standard format and a "pretty" format.')
    group_format.add_argument('-p', '--pretty', action="store_true", 
        help='Switch output to the pretty format as defined in settings \
        (Default: "{0[0]:<40}| {0[1]}"). So with default settings, this is \
        equivalent to -o "{0[0]:<40}| {0[1]}".')
    group_format.add_argument('-o', '--output', metavar='OUTPUTFORMAT', 
        help='Override output format settings with OUTPUTFORMAT (a Python \
        Format String). If this option is used, the --pretty flag is \
        ignored.')
    
    # Developer options
    #_connect_dev_arguments(q_parser)
    _connect_dev_arguments(parser)
    
    #################################################
    # Parse and process command line arguments      #
    #################################################
    
    args = parser.parse_args()
    
    # First check the --setup argument, because it overrides everything else
    if args.setup:
        setup.generate_settings()
    
    # Next, see if we're supposed to parse only or query, too.
    if args.silentupdate:
        args.func = _parse # default is _query, set in the argparser options.
    
    # Perpare the logger
    logger = _setup_logging(args.verbose)
    
    # Call the respective function for each subcommand
    # That is _parse(args) for the main command and _query(args) for the query 
    # subcommand
    args.func(args)
        
if __name__ == "__main__":
    main()