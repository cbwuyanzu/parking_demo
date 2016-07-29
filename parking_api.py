# -*- coding: utf-8 -*-

"""
Module implementing pm25.
"""
import json, time, threading
import urllib
import urllib2
import MySQLdb
import random, datetime

class Enum(set):
    def __getattr__(self, name):
        if name in self:
            return name
        raise AttributeError
 
class park_handler:
    """
    Class documentation goes here.
    """
    def __init__(self, monitor = True):
        """
        Constructor
        """        
        self.TOTAL_LOT_NUMBER = 600
        self.KEY = "63ea0ebede2448298c61eb71acd2be42"
        self.PARKCODE = "wju5bhs8"
        
        self.API_CMD = Enum(["CMD_PARKSPACE_NUM", "CMD_SEARCHCAR", "CMD_PARKSPACE_INFO", "CMD_DEVICE_INFO"])
        
        self.API_URL = {
            self.API_CMD.CMD_PARKSPACE_NUM:  "http://cloud.bluecardsoft.com.cn/main/open/api/parkSpaceNumBypark",
            self.API_CMD.CMD_SEARCHCAR: "http://cloud.bluecardsoft.com.cn/main/open/pubApi/searchCar",
            self.API_CMD.CMD_PARKSPACE_INFO: "http://cloud.bluecardsoft.com.cn/main/open/api/parkSpaceNumBycarInfo",
            self.API_CMD.CMD_DEVICE_INFO: "http://cloud.bluecardsoft.com.cn/main/open/api/getDeviceError"}
        
        self.monitor = monitor # if monitor is True, start thread to automatically log availability into history
        self.MONITOR_INTERVAL  = 300 # 5 minutes
        self.realtime_lot = [0,]
        self.stop_monitoring = False
        
        self.db = db_operator()
        self.db.create_usage_table(False)
        
        self.monitor_thread = None
        if self.monitor == True:
            self.start_monitor()
        print "### Monitor task started" 

        
    def post(self, u, d):  
        req = urllib2.Request(url = u,
                              headers = {'Content-Type' : 'text/json'},
                              data = d)
        response = urllib2.urlopen(req)
        return response.read()
    
    def api_post (self, cmd, **param):
        
        url = self.API_URL[cmd]
        newparam = {'key': self.KEY, 'parkCode': self.PARKCODE}
        newparam.update(param)
        data = json.dumps(newparam)
#         print time.asctime() + "  ### Post:" + data
        try:
            f =  self.post(url, data)
#             print f
            return json.loads(f,encoding='utf-8')   
        except Exception , e:
            print e
            return {"status":"error"}
        
    def get_lever_free(self,  lever):
        """
http://cloud.bluecardsoft.com.cn/main/open/api/parkSpaceNumBypark
请求： {"key":"63ea0ebede2448298c61eb71acd2be42", "parkCode":"wju5bhs8", "parkLever":"1"}
        """
        response = self.api_post(self.API_CMD.CMD_PARKSPACE_NUM, parkLever = lever)
        if u'status' in response.keys() and response[u'status'] == u'success':
            return response[u'spaceLeverList'][0][1]
        else:
            return 0
    
    def get_freepark_info(self, lever):
        response = self.api_post(self.API_CMD.CMD_PARKSPACE_INFO, parkLever = lever)
        if u'status' in response.keys() and response[u'status'] == u'success':
            return response[u'spaceNumList']
        else:
            return []
    
    def search_car(self, searchstr):
        response = self.api_post(self.API_CMD.CMD_SEARCHCAR, plateId = searchstr)
        if u'status' in response.keys() and response[u'status'] == u'success':
            return response[u'datas']
        else:
            return []

    def get_level_free_cached(self, lever):
        if lever is not 1:
            return 0
        if self.monitor == True:
            return self.realtime_lot[lever]
        else:
            return self.get_lever_free(lever)
    
    def start_monitor(self):
        #currently only lever 1 is monitored
        self.realtime_lot[0] = self.get_lever_free(1)
        self.stop_monitoring = False
        self.monitor_thread = threading.Thread(target = self.monitor_task)
        self.monitor_thread.start()
        
    def monitor_task(self):
        while (not self.stop_monitoring):
#             print time.asctime() + " Monitoring..."
            self.realtime_lot = self.get_lever_free(1)
            print datetime.datetime.now(), "\t", self.realtime_lot
            self.db.insert_usage_history(self.realtime_lot)
            time.sleep(self.MONITOR_INTERVAL)
            
    def stop_monitor(self):
        self.stop_monitoring = True
        
class db_operator():
    def __init__(self):
        self.DB = "test"
        self.DB_USER = "root"
        self.DB_PORT = 3306
        self.DB_PASSWORD = 'p0o9i8u7'
        self.DB_TB_USAGE = 'USAGE_HISTORY'
   #     self.DB_TB_PARKSPACE = "PARK_SPACE" TODO
        self.db = MySQLdb.connect(
            host = 'localhost',
            port = self.DB_PORT,
            user = self.DB_USER,
            passwd= self.DB_PASSWORD,
            db = self.DB
        )
        self.cur = self.db.cursor()
        
    def __del__(self):
        print "### DB wrapped up"
        self.cur.close()
        self.db.commit()
        self.db.close()  
        
    def create_usage_table(self, force=False):
        if force:
           self.cur.execute("show tables")
           rec = self.cur.fetchall() 
           for i in range(len(rec)):
               if rec[i][0].lower() == self.DB_TB_USAGE.lower():
                   self.cur.execute("drop table " + self.DB_TB_USAGE)
                   print "### Table deleted"
        sql = "create table if not exists " + self.DB_TB_USAGE + """
        ( id INT NOT NULL AUTO_INCREMENT,
          freespace INT NOT NULL,
          updatetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          PRIMARY KEY (id)
          )
        """
        print "### MySQL table initialized"
        self.cur.execute(sql)
        self.db.commit()
        return
    
    def insert_usage_history(self, num):
        sql = "insert into " + self.DB_TB_USAGE + " (freespace) values (" + str(num) + ")" 
        self.cur.execute(sql)
        self.db.commit()
        
    def get_latest_usage(self):
        sql = "select freespace from " + self.DB_TB_USAGE + " order by id desc limit 1"
        self.cur.execute(sql)
        rec = self.cur.fetchone()
        print rec[0]
        return rec
    
    def get_usages_history(self, starttime, endtime):
        sql = "select freespace, updatetime from " + self.DB_TB_USAGE + " where updatetime >= '" + str(starttime) + "' and updatetime <= '" +str(endtime) +"'"
        self.cur.execute(sql)
        rec = self.cur.fetchall()
        print "###Usage History within given period:"
        for i in range(len(rec)):
            print rec[i][0] , "\t|\t" , str(rec[i][1])
        return rec
    
    def get_usages_last_24h(self):
        print "###Usage History within last 24 hours:"
        now = datetime.datetime.now()
        return self.get_usages_history(now - datetime.timedelta(hours=24), now)
    

if __name__ == '__main__':
    #unit test
    park = park_handler(monitor = True)
#    print park.search_car(u"沪A")
    
    ##DB test
#     db = db_operator()
#     db.create_usage_table(False)
#     db.insert_usage_history(random.randint(1,200))
#     db.get_latest_usage()
#     now = datetime.datetime.now()
#     db.get_usages_history(now - datetime.timedelta(minutes=5), now)
#     db.get_usages_last_24h()