import json
from json import *
from datetime import date
from datetime import time
from datetime import timedelta
from datetime import datetime
from ee_plugin import Map
from itertools import groupby
import pathlib
from pathlib import Path


def docdstinh():
    dir1 = str(Path(__file__).parent.absolute()) + '\jsons\provincelist.json'
    with open(dir1) as f1:
        datax1 = json.load(f1)
        return datax1
def docdshuyen():
    dir2 = str(Path(__file__).parent.absolute()) + '\jsons\districtlist.json'
    with open(dir2) as f2:
        datax2 = json.load(f2)
        return datax2
        
def docdsxa():
    dir3 = str(Path(__file__).parent.absolute()) + '\jsons\communelist.json'
    with open(dir3) as f3:
        datax3 = json.load(f3)
        return datax3

def getdate(datestring):
    input_date = datestring
    str_Input = [int(''.join(i)) for is_digit, i in groupby(input_date, str.isdigit) if is_digit]
       
    str_Output = date(int(str_Input[1]), int(str_Input[2]), int(str_Input[3]))
    
    result = str(str_Output)
    return result
    
def getdatebubffer(tmp_imagedate, nday):

    str_tmp = tmp_imagedate.split('-')

    imagedate = date(int(str_tmp[0]), int(str_tmp[1]), int(str_tmp[2]))    
    today = date.today()
    dtime = timedelta(days=nday)
 
    hs = today - imagedate
    if hs < dtime:
      sdate = imagedate - hs - dtime
      edate = today
    else:
      sdate = imagedate - dtime
      edate = imagedate + dtime

    template_value = {
      'bd': str(sdate),
      'kt': str(edate),
    }    
    return template_value