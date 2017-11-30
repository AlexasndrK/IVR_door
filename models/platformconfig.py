"""
 Project code: FCONF
 Development code: NCB-20
 File: PLATFORMCONFIG.PY
 File location: ../flask-dev/models/
 type: Python 2.7
 Description: auxiliary module provides methods to retrieve initial connection data from local config file in order to
            to retrieve platform's configuration from DB. Methods use Configuration Parser handling local configuration
            file. The configuration file consists of sections, led by a [section] header and followed by name: value
            entries, with continuations in the style of RFC 822.
            As per project conventions, configuration file resides as /etc/ncb/<server role>_config.ini
            Server Role is brief server's ID by a role assigned, as follows:
            IVR - VoIP front-end server
            CE - Conference Engine server, VoIP back-end
            AS - Application Server
            HA - DBMS front-end server
Arguments: the server takes literal server's ID as it is mentioned in the section Description above.
            FYI!! The class ncbDB is going to extend Pconfig class to handle platform configuration. New class inherits
             properties of the class Pconfig

            NOTE!! For security reason, you should use user account in DBMS with restricted authority, such as READ-ONLY

"""

from ConfigParser import ConfigParser
import logging


class Pconfig(object):
    conferenceConfigDBname = None
    db_server = None
    conferenceConfigDBname_user = None
    conferenceConfigDBname_passwd = None
    conffile = [('IVR', 'ivr_conf.ini'), ('CE', 'ce_conf.ini'), ('AS', 'as_conf.ini')]

    def __init__(self, srvrole):
        self.lconfig = ConfigParser(allow_no_value=True)
        for i in self.conffile:   # look for local config file name that match server's role
            if i[0] == srvrole:
                self.localconf = "/etc/ncb/{}".format(i[1])  # set up local configuration URL
                break
        try:
            with open(self.localconf) as f:  # check whether ini file exist, otherwise - piss ncbDB out
                self.lconfig.readfp(f)
        except IOError:
            errmsg = "CONFIG: can not open local configuration file"
            logging.critical(errmsg)
            raise IOError       # TODO: Check failure exit from the process

        self.db_server = self.lconfig.get('serverdb', 'db_host', 0)  # It's HA Proxy - DB front-end server
        self.conferenceConfigDBname = self.lconfig.get('serverdb', 'db_name', 0)  # platform configuration is there
        self.conferenceConfigDBname_user = self.lconfig.get('serverdb', 'db_user', 0)  # account login
        self.conferenceConfigDBname_passwd = self.lconfig.get('serverdb', 'db_pass', 0)  # account password

    def getParam(self, section, name):
        return self.lconfig.get(section, name, 0)

# Eventually, all object variables carry necessary data for DB connector defined in child object.
# It also makes them accessible wherever from
