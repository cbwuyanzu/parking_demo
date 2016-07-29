# -*- coding: utf-8 -*-

from parking_api import db_operator
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import DayLocator, HourLocator, DateFormatter, drange

if __name__ == '__main__':
    print "Starting"
    db = db_operator()
    print "DB initialized"
    history = db.get_usages_last_24h()
    x = [history[i][0] for i in range(len(history))] # usage
    y = [history[i][1] for i in range(len(history))] # time
    fig, ax = plt.subplots()
    ax.plot_date(y, x)
    ax.fmt_xdata = DateFormatter('%Y-%m-%d %H:%M:%S')
    fig.autofmt_xdate()          #设置x轴时间外观  
#     ax.xaxis.set_major_locator(autodates)       #设置时间间隔  
#     ax.xaxis.set_major_formatter(yearsFmt)      #设置时间显示格式  
#     ax.set_xticks() #设置x轴间隔  
#     ax.set_xlim()   #设置x轴范围  
    
#     plt.plot(X,C)
    plt.show()