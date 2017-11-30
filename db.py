import pymysql
import logging
import socket
from models.platformconfig import Pconfig


class ncbDB(Pconfig):
    # I have to retrieve basic configuration attributes, listed below, from system config file
    # on ApplSrv, for example : /etc/ncb_applsrv/ncb_applsrv.conf

    hostname = None
    conferenceMediaStoragePath = '/media/conference/'  # NFS mount point
    conferenceDBcurs = None
    connect_db = None

    def __init__(self, srvrole):
        super(ncbDB, self).__init__(srvrole)  # run constructor of parent object

        self.hostname = socket.gethostname()  # get local hostname TODO: validate hostname with that one in config file
        self.conferenceMediaStoragePath = self.lconfig.get('media', 'media_path')  # TODO: if valid to remove it above
        try:
            self.connect_db = pymysql.connect(self.db_server,
                                              self.conferenceConfigDBname_user,
                                              self.conferenceConfigDBname_passwd,
                                              self.conferenceConfigDBname,
                                              charset='utf8mb4',
                                              cursorclass=pymysql.cursors.DictCursor)
            # self.conferenceDBcurs = self.connect_db.cursor()
        except pymysql.Error as er:
            logging.critical("Can not establish connection to configuration DB: %s", self.conferenceConfigDBname)
            raise Exception(er[0], er[1])

    # the method executes SQL query and returns all fetched rows. Otherwise it returns None
    def ncb_getQuery(self, querySQL):
        result = []
        try:
            with self.connect_db.cursor() as self.conferenceDBcurs:
                self.conferenceDBcurs.execute(querySQL)
                result = self.conferenceDBcurs.fetchall()
                return True, result
        except pymysql.ProgrammingError as er:
            logging.critical('ERROR: ProgrammingError in Conference DB. Call to support immediately - %s, %s' % (er[0], er[1]))
            return False, er[1]
        except pymysql.InternalError as er:
            logging.critical('ERROR: InternallError in Conference DB. Call to support immediately - %s, %s' % (er[0], er[1]))
            return False, er[1]
        except pymysql.Error as er:
            logging.critical('ERROR: Can not get a data from Conference DB. Call to support immediately - %s, %s' % (er[0], er[1]))
            return False, er[1]

    # the method executes SQL query to push data into DB.
    def ncb_pushQuery(self, querySQL):
        try:
            with self.connect_db.cursor() as self.conferenceDBcurs:
                self.conferenceDBcurs.execute(querySQL)
                self.connect_db.commit()
                return (True, [])
        except pymysql.Error as er:
            logging.critical('ERROR: Can not push a data into Conference DB. Call to support immediately - %s, %s' % (er[0], er[1]))
            return False, er[1]
        except pymysql.IntegrityError as er:
            logging.critical('ERROR: IntegrityError in Conference DB. Call to support immediately %s, %s' % (er[0], er[1]))
            return False, er[1]
        except pymysql.OperationalError as er:
            logging.critical('ERROR: OperationalError in Conference DB. Call to support immediately - %s, %s' % (er[0], er[1]))
            return False, er[1]
        except pymysql.InternalError as er:
            logging.critical('ERROR: InternallError in Conference DB. Call to support immediately - %s, %s' % (er[0], er[1]))
            return False, er[1]

    # if more than one rows are retrieved - it gets first row from the list as a dictionary
    def listdicttodict(self, listdict):
        return listdict[1][0]

    def getGlobalMediaPath(self):
        if not os.path.exists(self.conferenceMediaStoragePath):  # check it out whether it exist
            return None  # if it doesn't - return None
        else:
            return self.conferenceMediaStoragePath  # otherwise return the path

    def __del__(self):
        self.connect_db.close()
