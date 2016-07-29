# -*- coding: utf-8 -*-

"""
Module implementing pm25.
"""

from PyQt4.QtCore import pyqtSignature, QString, QSize, QTimer, QTime, QObject, \
    SIGNAL, Qt
from PyQt4.QtGui import *
from Ui_parking import Ui_Form
import json, time
import urllib
import urllib2
from parking_api import park_handler

try:
    _fromUtf8 = QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s
 
class parking(QWidget, Ui_Form):
    """
    Class documentation goes here.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference  to the parent widget
        @type QWidget
        """
        QWidget.__init__(self, parent)
        self.setupUi(self)
        
        self.TOTAL_LOT_NUMBER = 600
        self.QUERY_INTERVAL = 300 #second
        
        self.timer = QTimer()
        QObject.connect(self.timer, SIGNAL(_fromUtf8("timeout()")), self.timer_action)
        self.timer.start(self.QUERY_INTERVAL *1000)
        self.lineEdit.selectAll()
        self.lineEdit.setFocus()
        self.connect(self.lineEdit, SIGNAL("returnPressed()"), self.update_search_result) #信号绑定到槽
        self.park = park_handler(monitor = True)
        
    def timer_action(self):
        print "Updating UI...."
        self.update_lots()
        
    def ui_update_lots(self,  free,  total):
        self.lcdFreeLot.display("%d" % free)
        self.lcdTotalLot.display("%d" % total)
     
    def ui_update_search_list(self, cars):
        model = QStandardItemModel(self.listView)
#        model.clear()
        for car in cars:
            # Create an item with a caption
            item = QStandardItem(car["plateId"] +"\t\t" + car["parkSpace"] )
            model.appendRow(item)
        self.listView.setModel(model)
        return
    
    def update_lots(self):
        free = self.park.get_lever_free(1)
        self.ui_update_lots(free,  self.TOTAL_LOT_NUMBER)
    
    def update_search_result(self):
        try:
            text = unicode(self.lineEdit.text())
            self.ui_update_search_list(self.park.search_car(text))
        except:
            self.ui_update_search_list([])
            
if __name__ == '__main__':

    import sys
    from PyQt4 import QtGui
    app = QtGui.QApplication(sys.argv)
    window = parking()
    #window.get_rt_data_yunchuang('61728')
    #print json.dumps(window.search_car(u"沪A"), ensure_ascii=False)
    #window.ui_update_search_list(window.search_car(u"沪A"))
    window.update_lots()
    window.show()
    
    sys.exit(app.exec_())
