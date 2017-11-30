
import db
from freeswitch import *
# import md5
import logging
import os
import datetime
import pytz




condb = db.ncbDB("IVR")
logFilePath = condb.getParam(logging, log_file)
logLevel = condb.getParam(logging, log_level)
internalIP = condb.getParam(bridge, bridge_internal_ip)
gatewayIP = condb.getParam()

logging.basicConfig(filename=logFilePath, level=logLevel)

def hangup_hook(session, what):
    consoleLog("info", "hangup hook for %s!!\n\n" % what)
    return


def bridge2conf(session, mod_flag, conf_id):
    session.execute("set", "call_timeout=30")
    session.execute("set", "continue_on_fail=false")
    session.execute("set", "hangup_after_bridge=true")
    session.execute("set", "ringback=%(2000,4000,440.0,480.0)")
    called_number = session.getVariable("destination_number")
    session.execute("set", "sip_h_X-CallerIS = %s" % (mod_flag,))
    session.execute("set", "sip_h_Diversion=<sip:{}@{}>;reason=forwarded".format(called_number, internalIP))
    conf2bridge = 'conf_' + conf_id
    called_number = session.getVariable("destination_number")
    bridge_var = 'sofia/internal/{}@{}'.format(conf2bridge, gatewayIP)
    session.execute("bridge", bridge_var)

    #  TODO : Test part of this code. This part  we will need to close session on IVR
    #  deflect_test = '%s@65.48.98.217' % (conf2bridge,)
    #  session.execute("deflect", deflect_test)


def listdictodic(listdict):
    return listdict[0]


def timeconvert(timed, dated=0, tzd=0):
    from datetime import datetime, timedelta, date, time
    total_secs = timed.seconds
    secs = total_secs % 60
    total_mins = total_secs / 60
    mins = total_mins % 60
    hours = total_mins / 60
    tz = pytz.timezone(tzd)
    dt_db = datetime.combine(dated, time(hours, mins)).replace(tzinfo=tz).astimezone(pytz.timezone("GMT"))
    return (dt_db)


def tmzconvert(datedt, tzd):
    tz = pytz.timezone(tzd)
    dt_db = datedt.replace(tzinfo=tz).astimezone(pytz.timezone("GMT"))
    return (dt_db)


def confcheck(session, startt, nowt):
    if startt > nowt:
        session.streamFile("conference/8000/conf-conference_will_start_shortly.wav")
        session.hangup()
        exit(1)


def uni2list(uni_day):
    day_list = list()
    uni_day = uni_day.replace(' ', '').split(',')
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
    temp_date = datetime.datetime.combine(now_dtime.date(), start_date.time()).replace(tzinfo=pytz.timezone("GMT"))
    if start_date > now_dtime:
        session.streamFile("conference/8000/conf-conference_will_start_shortly.wav")
        session.hangup()
        exit(1)
    if persd['end_date'] is not None:
        end_date = tmzconvert(persd['end_date'], persd['TMZ'])
        end_date = persd['end_date'].time.replace(tzinfo=pytz.timezone(persd['TMZ'])).astimezone(pytz.timezone("GMT"))
        end_date = end_date + datetime.timedelta(minutes=int(persd['duration']))
        if end_date < now_dtime:
            session.speak("Conference has been ended")
            session.hangup()
            exit(1)
    end_date = temp_date + datetime.timedelta(minutes=int(persd['duration']))
    if persd['recur'] == 'Day':
        if len(persd['day_week']) < 1:
            day_time = list(rrule(DAILY, dtstart=start_date, interval=persd['rec_interval'], until=now_dtime))
            for day in day_time:
                if day.date() == now_dtime.date():
                    if day.time() <= now_dtime.time() <= end_date.time():
                        flag = 1
            if flag == 0:
                session.speak("Conference not active. Check you conference time")
                session.hangup()
                exit(1)
        else:
            day_week = uni2list(persd['day_week'])
            day_time = list(rrule(DAILY, dtstart=start_date, interval=persd['rec_interval'], until=now_dtime, byweekday=day_week))
            for day in day_time:
                logging.info(day)
                logging.info(end_date)
                logging.info(now_dtime)
                if day.date() == now_dtime.date():
                    if day.time() <= now_dtime.time() <= end_date.time():
                        flag = 1
            if flag == 0:
                session.speak("Conference not active. Check you conference time")
                session.hangup()
                exit(1)
    elif persd['recur'] == 'Week':
        if len(persd['day_week']) < 1:
            week_time = list(rrule(WEEKLY, dtstart=start_date, interval=persd['rec_interval'], until=now_dtime))
            for day in week_time:
                if day.date() == now_dtime.date():
                    if day.time() <= now_dtime.time() <= end_date.time():
                        flag = 1
            if flag == 0:
                session.speak("Conference not active. Check you conference time")
                session.hangup()
                exit(1)
        else:
            day_week = uni2list(persd['day_week'])
            week_time = list(rrule(WEEKLY, dtstart=start_date, interval=persd['rec_interval'], until=now_dtime, byweekday=day_week))
            for day in week_time:
                if day.date() == now_dtime.date():
                    if day.time() <= now_dtime.time() <= end_date.time():
                        flag = 1
            if flag == 0:
                session.speak("Conference not active. Check you conference time")
                session.hangup()
                exit(1)
    elif persd['recur'] == 'Month':
        if len(persd['day_week']) < 1:
            month_time = list(rrule(MONTHLY, dtstart=start_date, interval=persd['rec_interval'], until=now_dtime))
            for day in month_time:
                if day.date() == now_dtime.date():
                    if day.time() <= now_dtime.time() <= end_date.time():
                        flag = 1
            if flag == 0:
                session.speak("Conference not active. Check you conference time")
                session.hangup()
                exit(1)
        else:
            day_week = uni2list(persd['day_week'])
            month_time = list(rrule(MONTHLY, dtstart=start_date, interval=persd['rec_interval'], until=now_dtime, byweekday=day_week))
            for day in month_time:
                if day.date() == now_dtime.date():
                    if day.time() <= now_dtime.time() <= end_date.time():
                        flag = 1
            if flag == 0:
                session.speak("Conference not active. Check you conference time")
                session.hangup()
                exit(1)
    elif persd['recur'] == 'Year':
        if len(persd['day_week']) < 1:
            year_time = list(rrule(YEARLY, dtstart=start_date, interval=persd['rec_interval'], until=now_dtime))
            for day in year_time:
                if day.date() == now_dtime.date():
                    if day.time() <= now_dtime.time() <= end_date.time():
                        flag = 1
            if flag == 0:
                session.speak("Conference not active. Check you conference time")
                session.hangup()
                exit(1)
        else:
            day_week = uni2list(persd['day_week'])
            year_time = list(rrule(YEARLY, dtstart=start_date, interval=persd['rec_interval'], until=now_dtime, byweekday=day_week))
            for day in year_time:
                if day.date() == now_dtime.date():
                    if day.time() <= now_dtime.time() <= end_date.time():
                        flag = 1
            if flag == 0:
                session.speak("Conference not active. Check you conference time")
                session.hangup()
                exit(1)
    else:
        session.speak("Conference has been ended")
        logging.crit('Wrong type of conference')
        session.hangup()
        exit(1)


def conftype(session, room):
    if str(room['type']) == 'scheduled':
        sql = "SELECT * FROM type_scheduled WHERE rid = '{}'".format(room['rid'])
        condb = db.ncbDB("IVR")
        row = condb.ncb_getQuery(sql)
        if row[0]:
            sched = row[1][0]
            room_dtime = tmzconvert(sched['start_date'], sched['TMZ']) - datetime.timedelta(minutes=2)
            end_dtime = room_dtime + datetime.timedelta(minutes=int(sched['duration']))
            now_dtime = datetime.datetime.now().replace(tzinfo=pytz.timezone('GMT'))
            if room_dtime > now_dtime:
                session.streamFile("conference/8000/conf-conference_will_start_shortly.wav")
                session.hangup()
                exit(1)
            if now_dtime > end_dtime:
                session.speak("Conference has been ended")
                session.hangup()
                exit(1)
        else:
            logging.critical("DB Error:" + row[1])
            session.hangup()
            exit(1)
    elif str(room['type']) == 'persistent':
        sql = "SELECT * FROM type_persistent WHERE rid = '{}'".format(room['rid'])
        condb = db.ncbDB("IVR")
        row = condb.ncb_getQuery(sql)
        if row[0]:
            pers = row[1][0]
            room_dtime = tmzconvert(pers['start_date'], pers['TMZ']) - datetime.timedelta(minutes=2)
            now_dtime = datetime.datetime.now().replace(tzinfo=pytz.timezone('GMT'))
            logging.info("persistent; %s" % (pers['end_date'],))
            if pers['end_date'] is not None:
                end_dtime = tmzconvert(pers['end_date'], 'GMT')
                if now_dtime > end_dtime:
                    session.speak("Conference has been ended")
                    session.hangup()
                    exit(1)
            if now_dtime < room_dtime:
                session.streamfile("conference/8000/conf-conference_will_start_shortly.wav")
                session.hangup()
                exit(1)
        else:
            logging.critical("DB Error:" + row[1])
            session.hangup()
            exit(1)
    elif str(room['type']) == 'recurring':
        sql = "SELECT * FROM type_recurring WHERE rid = '%s'" % (room['rid'],)
        condb = db.ncbDB("IVR")
        row = condb.ncb_getQuery(sql)
        if row[0]:
            pers = row[1][0]
            conf_reccuring(session, pers)
        else:
            logging.critical("DB Error:" + row[1])
            session.hangup()
            exit(1)
    else:
        logging.critical('Wrong Conference type' + room["type"])
        session.hangup()
        exit(1)


def search(vroom, what, pip):
    val = [element for element in vroom if element['room_id'] == what]
    if len(val) > 0:
        if pip == 'pin':
            return str(val[0]['room_id'])
        if pip == 'pas':
            return val[0]
    return False


def getSpin(roomI, dtmfI):
    flag = False
    room = ''
    for cell in roomI:
        if cell['spinmod'] == dtmfI:
            flag = 'moderator'
            room = cell
        elif cell['spinuser'] == dtmfI:
            flag = 'user'
            room = cell
    return (flag, room)


def getGreeting(session, vcb):
    query = "SELECT greeting_path FROM vcb where vcb_id ='{}'".format(vcb)
    condb = db.ncbDB("IVR")
    row = condb.ncb_getQuery(sql)
    if row[0]:
        greet_path = row[1][0]
        if os.path.isfile("{}/{}/greetings/{}".format(vcb, condb.conferenceMediaStoragePath ,greet_path['greeting_path'])):
            return (True, str(greet_path['greeting_path']))
        else:
            return (False, '')
    else:
        logging.critical("DB Error:" + row[1])
        session.hangup()
        exit(1)


def handler(session, args):
    session.answer()
    vcb = {}
    room = {}
    attempt = 0
    session.set_tts_params("flite", "kal")
    caller_id = session.getVariable("destination_number")
    console_log("info", "caller id:: %s" % caller_id)
    sql = "SELECT * FROM vcb WHERE vcb_id = '{}'".format(caller_id)
    condb = db.ncbDB("IVR")
    row = condb.ncb_getQuery(sql)
    if row[0]:
        if len(row[1]) < 0:
            logging.critical("Did not find nothing in DB for vcb:" + caller_id)
            session.hangup()
            exit(1)
        vcb = row[1]
    else:
        logging.critical("DB Error:" + row[1])
        session.hangup()
        exit(1)
    sql = "SELECT * FROM conf_room WHERE vcb_id = '{}'".format(caller_id)
    row = condb.ncb_getQuery(sql)
    if row[0]:
        if len(row[1]) < 0:
            logging.critical("Did not find nothing in DB for vcb:" + caller_id)
            session.hangup()
            exit(1)
        room = row[1]
    else:
        logging.critical("DB Error:" + row[1])
        session.hangup()
        exit(1)
    greet = getGreeting(session, caller_id)
    if greet[0]:
        session.streamFile("{}/{}/greetings/{}".format(condb.conferenceMediaStoragePath,caller_id, greet[1]))
    else:
        session.sleep(600)
        session.streamFile("callie/conference/8000/Conf-greetgetnum_short.wav")
    while(attempt <= 3):
        session.sleep(200)
        dtmf_pin = 0
        session.flushDigits()
        dtmf_pin = session.playAndGetDigits(1, 10, 3, 30000, "#", "callie/conference/8000/conf-enter_conf_number.wav", "", "\\d+")
        spin = getSpin(room, dtmf_pin)
        # spin is a tuple of two elements - flag(moderator or user) and "room" dict from "conf_room" table
        if spin[0]:
            conftype(session, spin[1])
            bridge2conf(session, spin[0], str(spin[1]['room_id']))
            exit(1)
        db_pin = search(room, dtmf_pin, 'pin')
        if db_pin != dtmf_pin:
            attempt += 1
            session.streamFile("callie/conference/48000/conf-bad-pin.wav")
            if attempt == 4:
                session.streamFile("callie/conference/48000/conf-goodbye.wav")
                session.hangup()
                exit(1)
        else:
            break  # We need this break to stop executing while loop
    attempt = 0
    while(attempt <= 3):
        dtmf_pass = 0
        session.sleep(200)
        session.flushDigits()
        dtmf_pass = session.playAndGetDigits(1, 10, 3, 30000, "#", "callie/conference/8000/conf-enter_conf_pin.wav", "", "\\d+")
        db_pass = search(room, dtmf_pin, 'pas')
        if db_pass['attendee_pin'] == dtmf_pass or db_pass['moderator_pin'] == dtmf_pass:
            conftype(session, db_pass)
            if db_pass['attendee_pin'] == dtmf_pass:
                flag = 'user'
                bridge2conf(session, flag, db_pin)
                exit(1)
            elif db_pass['moderator_pin'] == dtmf_pass:
                flag = 'moderator'
                bridge2conf(session, flag, db_pin)
                exit(1)
        else:
            attempt += 1
            session.streamFile("callie/voicemail/48000/vm-password_not_valid.wav")
            if attempt == 4:
                session.streamFile("callie/conference/48000/conf-goodbye.wav")
                session.hangup()
                exit(1)
    session.hangup('1')
    exit(1)
