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
import pathspec
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
    def _ignorify(patterns=['*~']):
        """
        pathspec implements gitignore style pattern matching. However, 
        it doesn't ignore patterns, it *matches* patterns.
        So every pattern needs to be reversed by adding a '!' (or removing)
        it.
        """
        patterns = list(patterns)
        # First, add everything
        reversed_patterns = ['*']
        
        # Then reverse every single pattern
        for p in patterns:
            # If the pattern starts with '!', remove the '!'
            if p.startswith('!'):
                reversed_patterns.append(p.replace('!', '', 1))
            else:
                reversed_patterns.append('!' + p)
        
        return reversed_patterns
    
    @staticmethod
    def _list_files(dirname, ignore_patterns=None):
        # Reverse pattern
        ignore_patterns = Zettelparser._ignorify(ignore_patterns)
        
        spec = pathspec.PathSpec.from_lines('gitwildmatch', ignore_patterns)
        matches = spec.match_tree(dirname)
        files = []
        for match in matches:
            files.append(os.path.join(dirname, match))
        
        return files
    
    @staticmethod
    def _get_updated_files(dirname, index=None, ignore_patterns=None):
        # Take care of optional parameters
        index = index or dict(files=dict())
        
        ## Maybe our index has no timestamp, yet.
        try:
            timestamp = '@' + str(int(index['timestamp']))
        except KeyError:
            timestamp = '@0'
        ignore_patterns = ignore_patterns or []
        
        # Prepare ignore_patterns, i.e. reverse them
        ignore_patterns = Zettelparser._ignorify(ignore_patterns)
        spec = pathspec.PathSpec.from_lines('gitwildmatch', ignore_patterns)
                
        
        cmd = ['find', dirname, '-type', 'f', '-newerct', timestamp]
        # TODO (MEMO): should we need to get rid of the ./ at the beginning:
        # we can pipe it through sed 's/\.\///'
                
        output = []
        for line in subprocess.check_output(cmd).splitlines():
            line = line.decode()
            if spec.match_file(line):
                output.append(line)
                
        return output
        
    @staticmethod
    def _grep_files(dirname, index=None, ignore_patterns=None):
        # Calls grep to get the yaml-Blocks and markdown-Links as specified
        # in the file "zettels-grep-patterns"
        files = Zettelparser._get_updated_files(dirname, index, ignore_patterns)
        
        # Call grep only if there are any updated files
        grepoutput = None
        if files:
            # Path of the patterns file is 
            # [installation directory]/resources/zettels-grep-patterns
            #patterns_file = os.path.join(sys.path[0], 
            #                             "resources", 
            #                             "zettels-grep-patterns ")
            
            patterns_file = pkg_resources.resource_filename('zettels', 'resources/zettels-grep-patterns')
            
            # pass it to grep
            grepcmd = ['grep', '-n', '-E', '-o', '-f', patterns_file]
            try:
                grepoutput = subprocess.check_output(grepcmd + files)
            except subprocess.CalledProcessError as e:
                # This may be caused by an empty file
                if e.returncode == 1 and e.output.decode() == "":
                    logger.debug("grep returned an error, probably caused by"
                                +"an empty file:", e)
                    logger.debug("Carrying on ignoring the file.")
                else:
                    raise
        
        grepoutput = grepoutput or ""
        
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
                    int(for_yaml[f]['stop'])
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
    def _prune_index(rootdir, index):
        logger.debug("Pruning index...")
        to_prune = []
        try:
            files = index['files']
            # Make a list of all files in the root directory
            cmd = ['find', rootdir, '-type', 'f']
            found_files = subprocess.check_output(cmd).splitlines()

            for entry in files:
                to_be_compared = os.path.join(rootdir, entry).encode(encoding='UTF-8')
                logger.debug("Current entry:")
                logger.debug(to_be_compared)
                if not to_be_compared in found_files:
                    logger.error("Current entry is not in found_files. Well be pruned.")
                    # The file listed in the index doesn't exist anymore.
                    # Let's remove the entry
                    to_prune.append(entry)                    
        except TypeError as e:
            logger.error("Failed pruning the index. No valid index.", e)
        except KeyError as e:
            logger.error("Failed pruning the index. It doesn't contain a "
                         + "field 'files'", e)
        
        for entry in to_prune:
            del index['files'][entry]
        
        logger.debug("After pruning: index looks like this:")
        logger.debug(index)
        
        logger.debug("Pruning index: Done")

        return index
        
    @staticmethod
    def update_index(rootdir, index=None, ignore_patterns=None):
        """
        Update/build an index for the specified directory.
        
        If an index is already available, only files with modification dates
        newer then the timestampt of the index are parsed.
        
        If no index is specified, a new index will be built.
        
        The function uses grep to parse the YAML-Metadata and the Markdown
        links in the Zettel files. It won't work on a system without grep.

        :param rootdir: the directory containing the Zettel files.
        :param index: An existing index, if available.
        :param ignore_patterns: a list of gitignore-style patterns to be ignored by grep
        :return: The index in dictionary format. 
        """
        logger.debug("Updating index:")
        
        # Generate a empty index, if necessary
        # It's necessary if
        # a) index is None
        # b) index is not a valid dictionary
        # c) if the list of files in index is empty
        
        built_index_from_scratch = False
        zfi = [] # zfi: Zettels from index
        try:
            zfi = index['files']
        except (KeyError, TypeError):
            # index is None or not a dictionary with an entry called files
            logger.debug("index is none or invalid. Building from scratch.")
            built_index_from_scratch = True
            index = dict(files=dict())
        
        n = 0
        try:
            n = len(zfi)
        except TypeError:
            # index['files'] contained something without a length => invalid
            logger.debug("index is invalid. Building from scratch.")
            built_index_from_scratch = True
            index = dict(files=dict())
        
        if n == 0:
            logger.debug("index had an empty list of files. Building from scratch.")
            built_index_from_scratch = True
            index = dict(files=dict())
        
        logger.debug("Before calling grep, the index looked like this:")
        if built_index_from_scratch:
            logger.debug("--Oh, by the way, we built it from scratch.")
        logger.debug(index)
        
        
        # get the list of updated files and the grep output
        files, grepoutput = Zettelparser._grep_files(rootdir, index, ignore_patterns)
        logger.debug("Here's what find and grep returned:")
        logger.debug("files:")
        logger.debug(files)
        logger.debug("grepoutput:")
        logger.debug(grepoutput)
        
        # generate an empty entry for each updated file, if necessary
        for f in files:
            # Make the path to the file relative to the root directory
            f = os.path.relpath(f, rootdir)
            if not f in index['files']:
                index['files'][f] = dict(title="untitled", 
                                         targets=[], 
                                         tags=[], 
                                         followups=[])
        
        if built_index_from_scratch:
            logger.debug("The empty index looks like this:")
        else:
            logger.debug("index should be untouched by grep")
        logger.debug(index)

        if grepoutput:
            #A temporary dict for in which information is 
            #stored that are needed to parse the metadata
            for_yaml = dict()
            for line in grepoutput.splitlines():
                #because grepoutput is in bytestring format, 
                #decode it before taking it apart.
                line = bytes.decode(line)
                logger.debug("current line of grep output: " + line)
            
                #In the first partition, we get the filepath
                #of the occurrence file
                f, _, rest = line.partition(':')
                logger.debug("the rest looks like this: " + rest)
                
                # Make the path to the file relative to the root directory
                f = os.path.relpath(f, rootdir)
                
                logger.debug("Current file: " + f)
                #In the second partition, we get the line
                #number and the pattern that is responsible 
                #for this line
                ln, _, pat = rest.partition(':')
                
                # First occurence for that file? Create an empty
                # entry
                if not f in for_yaml:
                    for_yaml[f] = dict(start='', stop='')
                
                if pat == "---":
                # get the line number currently stored for the
                # pattern
                    current_ln = for_yaml[f]['start']
                    # current_ln might be an empty string
                    if current_ln:
                        # we want to store the smallest linenumber
                        # where this pattern occurs
                        if int(current_ln) > int(ln):
                            logger.debug("Storing start: " + ln)
                            for_yaml[f]['start'] = ln
                        else:
                            # we might have a YAML block that ends with
                            # '---' instead of '...'
                            current_ln = for_yaml[f]['stop']
                            # same game
                            if current_ln:
                                if int(current_ln) > int(ln):
                                    logger.debug("Storing stop: " + ln)
                                    for_yaml[f]['stop'] = ln
                            else:
                                logger.debug("Storing stop: " + ln)
                                for_yaml[f]['stop'] = ln
                    else:
                        # Yay, our value is new and shiny! Let's store it!
                        logger.debug("Storing start: " + ln)
                        for_yaml[f]['start'] = ln                    
                elif pat == "...":
                # get the line number currently stored for the
                # pattern
                    current_ln = for_yaml[f]['stop']
                    # current_ln might be an empty string
                    if current_ln:
                        # we want to store the smallest linenumber
                        # where this pattern occurs
                        # or the second smallest where '---' occurs, which 
                        # is handled above
                        if int(current_ln) > int(ln):
                            logger.debug("Storing stop: " + ln)
                            for_yaml[f]['stop'] = ln
                    else:
                        # Yay, our value is new and shiny! Let's store it!
                        logger.debug("Storing stop: " + ln)
                        for_yaml[f]['stop'] = ln
                #Other patterns are hyperlinks. Write the targets 
                #of those to the index
                else:
                    logger.debug("MD inline link found: " + pat)
                    # We still have the complete inline link, e.g.
                    # [Pipes](https://en.wikipedia.org/Pipelines_(Unix))
                    # We only want the URL-part. The target.
                    #only the target in parentheses
                    pat = pat.split("]")[1]
                    #strip away the front parenthesis
                    pat = pat.strip("(")
                    #and the end parenthesis
                    target = pat.rsplit(")", 1)[0]                    
                    
                    if not target in index['files'][f]['targets']:
                        index['files'][f]['targets'].append(target)
        
            logger.debug("Before parsing, for_yaml looks like this:")
            logger.debug(for_yaml)
            
            logger.debug("Parsing metadata...")
            # Parse the metadata contained in for_yaml and write it to index
            index = Zettelparser._parse_metadata(rootdir, for_yaml, index)
            logger.debug("Parsing metadata...")
        
        if not built_index_from_scratch:
            # prune the index
            index = Zettelparser._prune_index(rootdir, index)
            
        # write the timestamp and return the completed index
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
