import os
import time

class MetaData:

    def __init__(self, confobj):
        self.conf = confobj

        # Read metadata from file:
        self.data = ConfigParser()
        self.data.read(self.conf["Files"]["metadata file"])


    def has_changed(self, filename):
        """
        Check whether a file has changed since last run.
        Returns True if it has, otherwise False.
        """
        # TODO: Add support for an -f (--force) flag, which will
        # make this method return True always.

        # Make sure we only check the filename, not the path.
        path, fname = os.path.split(filename.strip())

        file_mod_time = os.stat(filename).st_mtime
        
        try:
            last_changed = float(self.data["Modfication time"][fname])
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
        path, fname = os.path.split(filename.strip())
        
        self.data["Modfication time"][fname] = os.stat(filename).st_mtime


    def save(self):
        "Saves the current metadata to a file."
        self.data.write(self.conf["Files"]["metadata file"])


        
