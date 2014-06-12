import os
import time

from configparser import ConfigParser, ExtendedInterpolation

import config as cf
conf = cf.Config()

class MetaData:
    # Defining a shared state according to the Borg design pattern.
    __shared_state = {}

    def __init__(self):
        # Copy the shared state according to the Borg design pattern.
        self.__dict__ = self.__shared_state



    def load(self):
        """
        Load meta data file. Location of the file will be automatically
        determined, if a Config object has been initialised beforehand.
        """
        self.conf = conf

        # Read metadata from file:
        self.data = ConfigParser(interpolation=ExtendedInterpolation())
        self.data.read(self.conf["Files"]["metadata file"])

        if "Modification time" not in self.data.keys():
            self.data["Modification time"] = {}


    def save(self):
        "Saves the current metadata to a file."
        #print("Saving modification times to {}".format(self.conf["Files"]["metadata file"]))
        with open(self.conf["Files"]["metadata file"], 'w') as f:
            self.data.write(f)


    def has_changed(self, material):
        """
        Check whether a file has changed since last run.
        Returns True if it has, otherwise False.
        """

        if self.conf.getboolean("TeXing","force TeXing of all files"):
            return True
        
        else:
            if type(material).__name__ == 'Material':
                file_mod_time = os.stat(material.path).st_mtime
                
                try:
                    last_changed = float(self.data["Modification time"][material.path])
                except KeyError:
                    # The file has not been logged before, i.e. it is new.
                    return True

            elif type(material) is str and material[-3:] == 'pdf':
                # TODO: having a PDF object like Material with a path attribute would
                # make this a lot cleaner...
                file_mod_time = os.stat(material).st_mtime
                
                try:
                    last_changed = float(self.data["Modification time"][material])
                except KeyError:
                    # The file has not been logged before, i.e. it is new.
                    return True

            try:
                if file_mod_time > last_changed:
                    return True
                else:
                    return False
            except NameError:
                print("Cannot check cache for object of type {}. "
                      "Normal execution continued.".format(type(material).__name__))



    def update_mod_time(self, material):
        """
        Updates the metadata about the file.
        """

        # Make sure we only save the filename, not the path.
        #path, fname = os.path.split(filename.strip())
 
        if type(material).__name__ == 'Material':
            self.data["Modification time"][material.path] = str(os.stat(material.path).st_mtime)
        
        elif type(material) is str and material[-3:] == 'pdf':
            self.data["Modification time"][material] = str(os.stat(material).st_mtime)



