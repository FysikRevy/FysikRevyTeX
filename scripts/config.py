import os
from configparser import ConfigParser, ExtendedInterpolation

class Config:
    # Defining a shared state according to the Borg design pattern.
    __shared_state = {}

    def __init__(self):
        # Copy the shared state according to the Borg design pattern.
        self.__dict__ = self.__shared_state

    def __getitem__(self, key):
        return self.conf[key]

    def __setitem__(self, key, value):
        self.conf[key] = value

    def getboolean(self, *args):
        return self.conf.getboolean(*args)

    def load(self, config_file = "revytex.conf"):
        "Load a configuration file."
        self.conf = ConfigParser(interpolation = ExtendedInterpolation(),
                                 inline_comment_prefixes = "#"
                                )
        self.conf.read(config_file, encoding="utf8" )
        self.name = self.conf["Revue info"]["revue name"]
        self.year = self.conf["Revue info"]["revue year"]
        self.modification_time = os.stat( config_file ).st_mtime


    def add_args(self, args):
        "Add command line arguments to the configuration."

        self.cmd_args = args[1:]
        self.cmd_options = []       # Store options prepended by either - or --
        self.cmd_parts = []         # Store which parts of the revue to create    
        
        for i,arg in enumerate(self.cmd_args):
            if arg[0] == '-':
                self.cmd_options.append(arg)
            else:
                self.cmd_parts.append(arg)

            if arg == '--verbose':
                self.conf["TeXing"]["verbose output"] = "yes"

            elif arg == '-v':
                # Change version number
                self.conf["Frontpage"]["version"] = self.cmd_args[i+1]
                self.cmd_options.append(self.cmd_args[i+1])
            
            elif arg == '-f' or arg == '--force':
                self.conf["TeXing"]["force TeXing of all files"] = "yes"


configuration = Config()
configuration.load()
