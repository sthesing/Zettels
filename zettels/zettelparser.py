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

import linecache
import logging
import os
import pkg_resources
import shlex
import subprocess
import sys
import time
import yaml

logger = logging.getLogger('Zettels.' + __name__)

class Zettelparser:
    """
    Zettelparser contains some methods necessary to build and update the index.
    
    It uses grep for parsing the Zettels. So if grep is not present
    on your OS, it won't work.
    
    The central method is probably Zettelparser.update_index(), it calls 
    most of the other methods, which can be viewed as sub-methods.
    
    The only other independent functions are Zettelparser.read_index() 
    and Zettelparser.write_index()
    
    See the class Zettelkasten for functionality of working with the index.        
    """
    
    @staticmethod
    def _list_files(dirname):
        # Returns a list of files in the specified directory        
        files = []
        for root, _, filenames in os.walk(dirname):
            for f in filenames:
                if not f.endswith("~"):
                    files.append(os.path.join(root, f))
        return files
        
    @staticmethod
    def _get_updated_files(dirname, index=None):

        
        #Get the current list of files
        files = Zettelparser._list_files(dirname)
        
        if index:
            for f in files:
                if index['files']:
                    #remove files from index that are no longer there
                    if not f in index['files']:
                        del index['files'][f]
                
                if index['timestamp']:
                    #remove all files from the list that 
                    # a) are in the index already
                    # and
                    # b) haven't been modified since the index has last been updated
                    if (f in index['files']) and (os.stat(f, follow_symlinks=False).st_mtime <= index['timestamp']):
                        files.remove(f)
        
        return files
        
    @staticmethod
    def _grep_files(dirname, index=None):
        # Calls grep to get the yaml-Blocks and markdown-Links as specified
        # in the file "zettels-grep-patterns"
        files = Zettelparser._get_updated_files(dirname, index)
        
        # Call grep only, if there are any updated files
        if not files:
            grepoutput = None
        else:
            # Path of the patterns file is 
            # [installation directory]/resources/zettels-grep-patterns
            #patterns_file = os.path.join(sys.path[0], 
            #                             "resources", 
            #                             "zettels-grep-patterns ")
            
            patterns_file = pkg_resources.resource_filename('zettels', 'resources/zettels-grep-patterns')
            
            # pass it to grep
            grepcmd = "grep --exclude=\"*~\" -n -E -o -f " + patterns_file
            grepoutput = subprocess.check_output(shlex.split(grepcmd) + files)
        
        return files, grepoutput
    
    @staticmethod    
    def _parse_metadata(rootdir, for_yaml, index):
        origcwd = os.getcwd()
        os.chdir(rootdir)
        logger.debug("Parsing metadata:")
        for f in for_yaml:
            # Make the path to the file relative to the root directory
            #f = os.path.relpath(f, rootdir)
            
            logger.debug("Current file:")
            logger.debug(f)
            #only if there is more than the backbone.
            if for_yaml[f]['start'] != '':
                logger.debug("start: " + for_yaml[f]['start'])
                logger.debug("stop: " + for_yaml[f]['stop'])
                y = ''
                for i in range(
                    int(for_yaml[f]['start']), 
                    int(for_yaml[f]['stop'])+1
                    ):
                    y = y + linecache.getline(f, i)
            
                logger.debug("y: " + str(y))
                
                metadata = yaml.safe_load(y)
                #write the metadata to the index.
                for item in metadata:
                    index['files'][f][item] = metadata[item]
        
        linecache.clearcache()
        os.chdir(origcwd)
        logger.debug("Parsing metadata: Done.")
        return index
    
    @staticmethod
    def update_index(rootdir, index=None):
        """
        Update/build an index for the specified directory.
        
        If an index is already available, only files with modification dates
        newer then the timestampt of the index are parsed.
        
        If no index is specified, a new index will be built.
        
        The function uses grep to parse the YAML-Metadata and the Markdown
        links in the Zettel files. It won't work on a system without grep.

        :param rootdir: the directory containing the Zettel files.
        :param index: An existing index, if available.
        :return: The index in dictionary format. 
        """
        logger.debug("Updating index:")
        # get the list of updated files and the grep output
        files, grepoutput = Zettelparser._grep_files(rootdir, index)
        
        # generate a empty index, if necessary
        if not index:
            index = dict(files=dict())
        
        # generate an empty entry for each updated file, if necessary
        for f in files:
            # Make the path to the file relative to the root directory
            f = os.path.relpath(f, rootdir)
            if not f in index['files']:
                index['files'][f] = dict(title="untitled", 
                                         targets=[], 
                                         tags=[], 
                                         followups=[])
        
        logger.debug("The empty index looks like this:")
        logger.debug(index)
        
        #A temporary dict for in which information is 
        #stored that are needed to parse the metadata
        for_yaml = dict()
        
        if grepoutput:
            for line in grepoutput.splitlines():
                #because grepoutput is in bytestring format, 
                #decode it before taking it apart.
                line = bytes.decode(line)
            
                #In the first partition, we get the filepath
                #of the occurrence file
                f, _, rest = line.partition(':')
                
                # Make the path to the file relative to the root directory
                f = os.path.relpath(f, rootdir)
                
                logger.debug("Current file: " + f)
                #In the second partition, we get the line
                #number and the pattern that is responsible 
                #for this line
                ln, _, pat = rest.partition(':')
                
                if not f in for_yaml:
                    for_yaml[f] = dict(start='', stop='')
                
                if pat == "---":
                    for_yaml[f]['start'] = ln
                elif pat == "...":
                    for_yaml[f]['stop'] = ln
                #The rest are hyperlinks. Write the targets 
                #of those to the index
                else:
                    target = pat.rsplit("(")[1].strip(")")
                    
                    if not target in index['files'][f]['targets']:
                        index['files'][f]['targets'].append(target)
        
        logger.debug("Before parsing, for_yaml looks like this:")
        logger.debug(for_yaml)
        
        # Parse the metadata contained in for_yaml, write it to index and return
        # the completed index
        index = Zettelparser._parse_metadata(rootdir, for_yaml, index)
        index['timestamp'] = time.time()
        
        logger.debug("Updating index: Done.")
        return index
    
    @staticmethod
    def read_index(filename="index.yaml"):
        """
        Read index from file
        
        :param filename: path to the index file (YAML)
        :return: The index in dictionary format. 
        """
        f = open(filename, 'rt')
        index = yaml.safe_load(f.read())
        f.close()
        return index
    
    @staticmethod
    def write_index(index, filename="index.yaml"):
        """
        Write index to file
        
        :param index: dictionary containing the index
        :param filename: path to the index file (YAML) to be written
        """
        f = open(filename, 'wt')
        yaml.dump(index, f)
        f.close()
