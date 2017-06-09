#! /usr/bin/env python3

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
Setup tool for Zettels
"""
import os
import sys
import xdg.BaseDirectory

def _generate_settings():
    """
    Interactively generate settings.
    """
    # Get the standard directory for settings. Create it, if not present.
    settings_base_dir = xdg.BaseDirectory.save_config_path('Zettels')
    
    # Defaults
    rootdir = os.getcwd()
    indexfile = settings_base_dir + '/index.yaml'
    outputformat = '{0[1]}'
    prettyformat = '{0[0]:<40}| {0[1]}'
    ignore = ['*~', '.*']
    
    # Ask the user
    
    # Root dir
    print('Please specify the root directory of your Zettelkasten.')
    print('It will contain the Zettel files.')
    rootdir = input("Default is the current directory: '" 
        + rootdir + "': ") or rootdir
        
    # Index file
    print('Please specify the file containing the index of your Zettelkasten.')
    indexfile = input("Default is: '" + indexfile + "': ") or indexfile
 
    print()
    print("These are your settings:")
    print("------------------------")
    print("Root directory:", rootdir)
    print("Index file:", indexfile)

    correct = input("Are these correct? y/n, Default is 'y': ")
    if correct == "n" or correct == "N":
        startover = input("Do you want so start over? y/n, Default is y: ")
        if startover == "n" or startover == "N":
            exit()
        else:
            print("Starting over...")
            print()
            generate_settings()
    else:
        f = open(os.path.join(settings_base_dir, 'zettels.cfg.yaml'), 'w')
        f.write("# This is a settings file for Zettels\n")
        f.write("# see https://github.com/sthesing/Zettels\n")
        f.write('rootdir: ' + rootdir + '\n')
        f.write('indexfile: ' + indexfile + '\n')
        f.write('outputformat: \'' + outputformat + '\'\n')
        f.write('prettyformat: \'' + prettyformat + '\'\n')
        f.write('ignore: {\n')
        f.write('    # temporal files, hidden files\n')
        for p in ignore:
            f.write('    \''+ p + '\',\n')
        f.write('}\n')
        f.close()
    
    print("Settings written to '" + os.path.join(settings_base_dir, 'zettels.cfg.yaml') + "'.") 
    exit()

def generate_settings():
    try:
        _generate_settings()
    except KeyboardInterrupt:
        print()
        print("Aborted by user")

if __name__ == "__main__":
    generate_settings()
