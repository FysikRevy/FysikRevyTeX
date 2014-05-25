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


    def has_changed(self, filename):
        """
        Check whether a file has changed since last run.
        Returns True if it has, otherwise False.
        """

        if self.conf.getboolean("TeXing","force TeXing of all files"):
            return True
        
        else:
            # Make sure we only check the filename, not the path.
            # No! We need to allow for similarly named songs and sketches!
            #path, fname = os.path.split(filename.strip())

            file_mod_time = os.stat(filename).st_mtime
            
            try:
                last_changed = float(self.data["Modification time"][filename])
            except KeyError:
                # The file has not been logged before, i.e. it is new.
                return True

            if file_mod_time > last_changed:
                return True
            else:
                return False


    def update_mod_time(self, filename):
        """
        Updates the metadata about the file.
        """

        # Make sure we only save the filename, not the path.
        #path, fname = os.path.split(filename.strip())
        
        self.data["Modification time"][filename] = str(os.stat(filename).st_mtime)



