import pymysql
from freeswitch import *
import   md5, logging
# from datetime import datetime, timedelta, date, time  as dt
import datetime
import pytz

logging.basicConfig(filename='/var/log/pyth.log',level=logging.DEBUG)

def hangup_hook(session, what):
    consoleLog("info","hangup hook for %s!!\n\n" % what)
    return


def bridge2conf(session, mod_flag, conf_id):
    session.execute("set","call_timeout=30")
    session.execute("set","continue_on_fail=false")
    session.execute("set","hangup_after_bridge=true")
    session.execute("set", "ringback=%(2000,4000,440.0,480.0)")
    called_number = session.getVariable("destination_number")
    session.execute("set", "sip_h_X-CallerIS = %s" %(mod_flag,))
    session.execute("set", "sip_h_Diversion=<sip:%s@65.48.99.135>;reason=forwarded" % (called_number,))
    conf2bridge = 'conf_' + conf_id
    called_number = session.getVariable("destination_number")
    bridge_var = 'sofia/internal/%s@65.48.98.217' % (conf2bridge,)
    session.execute("bridge" ,bridge_var)


def listdictodic(listdict):
    return listdict[0]


def timeconvert(timed,dated=0,tzd=0):
    from datetime import datetime, timedelta, date, time
    total_secs = timed.seconds
    secs = total_secs % 60 
    total_mins = total_secs / 60
    mins = total_mins % 60
    hours = total_mins / 60
    tz = pytz.timezone(tzd)
    dt_db = datetime.combine(dated ,time(hours, mins)).replace(tzinfo=tz).astimezone(pytz.timezone("GMT"))   
    return (dt_db)


def tmzconvert(datedt, tzd):
    tz = pytz.timezone(tzd) 
    logging.info(tz)
    dt_db = datedt.replace(tzinfo=tz).astimezone(pytz.timezone("GMT"))
    return (dt_db)


def confcheck(session, startt, nowt):
    if startt > nowt:
        session.streamFile("conference/8000/conf-conference_will_start_shortly.wav")
        session.hangup()
        exit(1)


def uni2list(uni_day):
    day_list = list() 
    uni_day = uni_day.replace(' ','' ).split(',')
    for word in uni_day:
        word = word.upper()
        if word == 'MO':
            day_list.append(0)
        elif word == 'TU':
            day_list.append(1)
        elif word == 'WE':
            day_list.append(2)
        elif word == 'TH':
            day_list.append(3)
        elif word == 'FR':
            day_list.append(4)
        elif word == 'SA':
            day_list.append(5)
        elif word == 'SU':
            day_list.append(6)
    return day_list
    
    
def conf_reccuring(session, persd):
    from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY, YEARLY, SU, MO, TU, WE, TH, FR, SA
    flag = 0
    now_dtime = datetime.datetime.now().replace(tzinfo=pytz.timezone('GMT'))
    start_date = tmzconvert(persd['start_date'], persd['TMZ']) - datetime.timedelta(minutes=2)
     
    if start_date > now_dtime:
        session.streamFile("conference/8000/conf-conference_will_start_shortly.wav")
        session.hangup()
        exit(1)
    if persd['end_date'] != None:
        end_date = tmzconvert(persd['end_date'], persd['TMZ'])
        end_date = persd['end_date'].time.replcae(tzinfo=pytz.timezone(persd['TMZ'])).astimezone(pytz.timezone("GMT"))
        end_date = end_date + datetime.timedelta(minutes=int(persd['duration']))
        if end_date < now_dtime:
            session.speak("Conference has been ended")
            session.hangup()
            exit(1)
     #else:
    end_date = now_dtime + datetime.timedelta(minutes=int(persd['duration']))
        #if end_date < now_dtime:
         #   session.speak("Conference has been ended")
         #   session.hangup()
         #  exit(1)
    if persd['recur'] == 'Day':
        if len(persd['day_week']) < 1:
            day_time = list(rrule(DAILY, dtstart=start_date, interval = persd['rec_interval'], until = now_dtime))
            for day in day_time:
                if end_date > day >=  now_dtime:
                    flag = 1
            if flag == 0:
                session.speak("Conference not active. Check you conference time")
                session.hangup()
                exit(1)
#                    confcheck(session, day, now_dtime)
        else:
            day_week = uni2list(persd['day_week'])
            day_time = list(rrule(DAILY, dtstart=start_date, interval = persd['rec_interval'], until = now_dtime, byweekday=day_week))
            for day in day_time:
                if end_date > day >= now_dtime:
                    flag = 1
            if flag == 0:
                session.speak("Conference not active. Check you conference time")
                session.hangup()
                exit(1)
#                    confcheck(session, day, now_dtime)              
    elif persd['recur'] == 'Week':
        logging.info(type(persd['rec_interval']))
        logging.info(type(persd['day_week']))
        if len(persd['day_week']) < 1:    
            week_time = list(rrule(WEEKLY, dtstart=start_date, interval = persd['rec_interval'], until = now_dtime))
            for day in week_time:
                if end_date > day >=  now_dtime:
                    flag = 1
            if flag == 0:
                session.speak("Conference not active. Check you conference time")
                session.hangup()
                exit(1)
#                    confcheck(session, day, now_dtime)
        else: 
            logging.info(start_date.hour)
            day_week = uni2list(persd['day_week'])
            week_time = list(rrule(WEEKLY, dtstart=start_date, interval = persd['rec_interval'], until = now_dtime, byweekday=day_week))  
            logging.info(week_time) 
            logging.info(day_week)  
            for day in week_time:
                if end_date > day >=  now_dtime:       
                    flag = 1
            if flag == 0:
                session.speak("Conference not active. Check you conference time")
                session.hangup()  
                exit(1)
    elif persd['recur'] == 'Month': 
        if len(persd['day_week']) < 1:
            month_time = list(rrule(MONTHLY, dtstart=start_date, interval = persd['rec_interval'], until = now_dtime))
            for day in month_time:
                if end_date > day >=  now_dtime:
                    flag = 1
            if flag == 0:
                session.speak("Conference not active. Check you conference time")
                session.hangup()
                exit(1)
#                    confcheck(session, day, now_dtime)
        else:
            day_week = uni2list(persd['day_week'])
            month_time = list(rrule(MONTHLY, dtstart=start_date, interval = persd['rec_interval'], until = now_dtime, byweekday=day_week))
            for day in month_time:
                if end_date > day >=  now_dtime:
                    flag = 1
            if flag == 0:
                session.speak("Conference not active. Check you conference time")
                session.hangup()
                exit(1)
#                    confcheck(session, day, now_dtime)        
       # month_time = list(rrule(MONTHLY, dtstart=start_date, interval = persd['rec_interval'], until = now_dtime))
       # confcheck(session, month_time, now_dtime)
    elif persd['recur'] == 'Year': 
        if len(persd['day_week']) < 1:
            year_time = list(rrule(YEARLY, dtstart=start_date, interval = persd['rec_interval'], until = now_dtime))
            for day in year_time:
                if end_date >  day >=  now_dtime:
                    flag = 1
            if flag == 0:
                session.speak("Conference not active. Check you conference time")
                session.hangup()
                exit(1)
#                    confcheck(session, day, now_dtime)
        else:
            day_week = uni2list(persd['day_week'])
            year_time = list(rrule(YEARLY, dtstart=start_date, interval = persd['rec_interval'], until = now_dtime, byweekday=day_week))
            for day in year_time:
                if end_date > day >=  now_dtime:
                    flag = 1
            if flag == 0:
                session.speak("Conference not active. Check you conference time")
                session.hangup()
                exit(1)
#                    confcheck(session, day, now_dtime)    
       # year_time = list(rrule(YEARLY, dtstart=start_date, interval = persd['rec_interval'], until = now_dtime))
       # confcheck(session, year_time, now_dtime)
    else: 
         session.speak("Conference has been ended")
         logging.crit('Wrong type of conference')
         session.hangup()
         exit(1)


def conftype(session, room):
    # convert local and time from DB to UTC accroding TimeZone
    # logging.info('room_id = %s', room['rid'])
    if str(room['type']) == 'scheduled':
        query = "SELECT * FROM type_scheduled WHERE rid = '%s'" % (room['rid'],)
        sched = listdictodic(db_connect(session, query)) 
        room_dtime = tmzconvert(sched['start_date'],sched['TMZ']) - datetime.timedelta(minutes=2)
        # room_dtime  = timeconvert(sched['time'],sched['date'],sched['TMZ']) # date and time in normal format
        end_dtime = room_dtime + datetime.timedelta(minutes=int(sched['duration']))
        now_dtime = datetime.datetime.now().replace(tzinfo=pytz.timezone('GMT'))
        logging.info(room_dtime)
        logging.info(now_dtime)
        logging.info(end_dtime)
        if room_dtime  >  now_dtime:
            session.streamFile("conference/8000/conf-conference_will_start_shortly.wav")
            session.hangup()
            exit(1)
        if now_dtime > end_dtime:
            session.speak("Conference has been ended")
            session.hangup()
            exit(1)
    elif str(room['type']) == 'persistent':
        query = "SELECT * FROM type_persistent WHERE rid = '%s'" % (room['rid'],)
        pers = listdictodic(db_connect(session, query))
        # room_dtime = timeconvert(pers['time'],pers['date'],pers['TMZ'])
        room_dtime = tmzconvert(pers['start_date'],pers['TMZ']) - datetime.timedelta(minutes=2)
        now_dtime = datetime.datetime.now().replace(tzinfo=pytz.timezone('GMT'))
        # logging.info(now_dtime)
        # logging.info(room_dtime)
        if now_dtime < room_dtime:
           session.streamfile("conference/8000/conf-conference_will_start_shortly.wav")
           session.hangup()
    elif str(room['type']) == 'recurring': 
        query = "SELECT * FROM type_recurring WHERE rid = '%s'" % (room['rid'],)
        pers = listdictodic(db_connect(session, query))
        # logging.info(pers)
        # session.speak("Conference reccuring")
        conf_reccuring(session, pers)
    else:
        logging.critical('No or Wrong Conf type') 
        session.hangup()


def db_connect(session, sql_quer):
    connect_db = pymysql.connect(host = '65.48.98.242',
                                 user = 'haproxy',
                                 password = 'haproxy',
                                 db = 'nbs_conf',
                                 charset = 'utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    try:
       with connect_db.cursor() as cursor:
           cursor.execute(sql_quer)
           result = cursor.fetchall()
           cursor.close()
           connect_db.close()
           return(result)
    except:
        logging.critical('Error: unable to fecth data')
	consoleLog("critical", "Database error")
        connect_db.close()
	session.hangup()
        exit(1)


# Think deeper how to improve
def search(vroom, what, pip):
   val  = [element for element in vroom if element['room_id'] == what] 
   if len(val) > 0:
      if pip == 'pin':
          return str(val[0]['room_id'])
      if pip == 'pas':
          return val[0]
   else: return 0 


def handler(session, args):
    session.answer()
    vcb = {}

    room = {}
    attempt = 0 
    session.set_tts_params("flite", "kal")
    caller_id = session.getVariable("destination_number")
    console_log("info", "caller id:: %s" % caller_id)
    query = "SELECT * FROM vcb WHERE vcb_id = '%s'" % (caller_id,)
    vcb = db_connect(session, query)
    if len(vcb) < 0:
        # add alert or log 
	session.hangup() 
        exit(1)
    query = "SELECT * FROM conf_room WHERE vcb_id = '%s'" % (caller_id,)
    room = db_connect(session, query)
    session.sleep(1000)
    session.streamFile("/usr/local/freeswitch-1.6/share/freeswitch/sounds/en/us/callie/conference/8000/conf-welcome.wav")
    session.sleep(300)
    while(attempt <= 3):
        session.sleep(200)
        dtmf_pin = 0 
        session.flushDigits()
        dtmf_pin = session.playAndGetDigits (4, 4, 3, 30000, "#", "/usr/local/freeswitch-1.6/share/freeswitch/sounds/en/us/callie/conference/8000/conf-enter_conf_number.wav", "/usr/local/freeswitch-1.6/share/freeswitch/sounds/en/us/callie/conference/8000/conf-bad-pin.wav","\\d+")
        # logging.info(dtmf_pin)
        db_pin = search(room, dtmf_pin, 'pin')
        # logging.info(room)
        if db_pin == dtmf_pin: 
           break
        else:
            attempt += 1
            if attempt == 4:
		session.streamFile("/usr/local/freeswitch-1.6/share/freeswitch/sounds/en/us/callie/conference/48000/conf-bad-pin.wav")
                session.streamFile("/usr/local/freeswitch-1.6/share/freeswitch/sounds/en/us/callie/conference/48000/conf-goodbye.wav")
                session.hangup()
                exit(1)
    attempt = 0 
    session.sleep(1000)
    while(attempt <= 3):
        dtmf_pass = 0 
        session.sleep(200)
        session.flushDigits()
        dtmf_pass = session.playAndGetDigits (4, 4, 3, 30000, "#", "/usr/local/freeswitch-1.6/share/freeswitch/sounds/en/us/callie/conference/8000/conf-enter_conf_pin.wav", "/usr/local/freeswitch-1.6/share/freeswitch/sounds/en/us/callie/voicemail/8000/vm-password_not_valid.wav","\\d+")
        db_pass = search(room, dtmf_pin, 'pas')
        if db_pass['attendee_pin'] == dtmf_pass or db_pass['moderator_pin'] == dtmf_pass :
            conftype(session, db_pass)
            if db_pass['attendee_pin'] == dtmf_pass: 
                flag = 'user'
                bridge2conf(session, flag, db_pin)
            elif db_pass['moderator_pin'] == dtmf_pass:
                flag = 'moderator'
                bridge2conf(session, flag, db_pin)
        else:
            attempt += 1
            if attempt == 4:
                session.streamFile("/usr/local/freeswitch-1.6/share/freeswitch/sounds/en/us/callie/voicemail/48000/vm-password_not_valid.wav")
                session.streamFile("/usr/local/freeswitch-1.6/share/freeswitch/sounds/en/us/callie/conference/48000/conf-goodbye.wav")
                session.hangup()            
                exit(1)
    session.hangup('1')
    exit(1)
