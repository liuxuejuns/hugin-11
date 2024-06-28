import time
import datetime
import json

from django.utils import timezone
from django.http import JsonResponse
from django.db import connections
from django.views import View
from django.shortcuts import render
from django.core import serializers

from history.models import TestItemHistoryRecord
from testrecord.models import TestItemRecord


# Create your views here.


class GetRackHistory(View):
    def get(self, request, *args, **kwarg):
        '''
        search Rack History
        '''
        rack_id = request.GET.get("rack_id", "")
        rack_sn = request.GET.get("rack_sn", "")
        current_stage = request.GET.get("current_stage", "")
        operatorid = request.GET.get("operatorid", "")
        teststatus = request.GET.get("teststatus", "")
        isvalid = request.GET.get("isvalid", "")
        startcreatedtime = request.GET.get("startcreatetime", "")
        endcreatedtime = request.GET.get("endcreatetime", "")
        startupdatedtime = request.GET.get("startupdatedtime", "")
        endupdatedtime = request.GET.get("endupdatedtime", "")
        #构建查询语句的前半部分，指定要查询的列以及对"createdtime"和"updatedtime"进行格式化。
        query = 'select "rack_id","rack_sn","current_stage","operatorid","teststatus","isvalid",to_char("createdtime",\'yyyy-MM-dd hh24:mi:ss\'),to_char("updatedtime",\'yyyy-MM-dd hh24:mi:ss\')'
        sql = ' from "rackhistory" where true ' #构建查询语句的后半部分，初始化为where true。后续会根据查询条件进行动态拼接。

        if rack_id: #通过一系列的if条件语句，根据每个查询条件的存在与否，将对应的筛选条件拼接到sql语句中。
            sql = sql + 'and "rack_id" = \'' + rack_id + '\''
        if rack_sn:
            sql = sql + 'and "rack_sn" = \'' + rack_sn + '\''
        if current_stage:
            sql = sql + 'and "current_stage" = \'' + current_stage + '\''
        if operatorid:
            sql = sql + 'and "operatorid" = \'' + operatorid + '\''
        if teststatus:
            sql = sql + 'and "teststatus" = \'' + teststatus + '\''
        if isvalid:
            sql = sql + 'and "isvalid" = \'' + isvalid + '\''
        if startcreatedtime:
            sql = sql + ' and "createdtime" >= \'' + startcreatedtime + '\''
        if endcreatedtime:
            sql = sql + ' and "createdtime" <= \'' + endcreatedtime + '\''
        if startupdatedtime:
            sql = sql + ' and "updatedtime" >= \'' + startupdatedtime + '\''
        if endupdatedtime:
            sql = sql + ' and "updatedtime" <= \'' + endupdatedtime + '\''
        try:
            connection = connections['l11_test_primary'] #根据数据库配置名称获取数据库连接对象
            cur = connection.cursor() #创建游标对象
            cur.execute(query + sql) #执行查询语句，将前半部分的查询列和后半部分的筛选条件拼接并执行。
            query_data = cur.fetchall() #获取查询结果的所有数据。
            cur.close()
            all_data = []
            k = [
                'rack_id',
                'rack_sn',
                'current_stage',
                'operatorid',
                'teststatus',
                'isvalid',
                'createtime',
                'updatedtime',
            ]
            for i in query_data:
                jsondata = dict(zip(k, i)) #获取查询结果的所有数据。
                all_data.append(jsondata)
            return JsonResponse(
                {
                    'code': 200,
                    'data': all_data,
                    'message': 'Query rack history success',
                }
            )
        except:
            return JsonResponse(
                {
                    'code': 400,
                    'data': 'no data',
                    'message': 'Query rack history error',
                }
            )


class GetTestItemRecordHistory(View):
    def get(self, request, *args, **kwarg):
        '''
        search test item record history
        '''
        # 获取数据
        rack_sn = request.GET.get("rack_sn", "")
        component_id = request.GET.get("component_id", "")
        component_sn = request.GET.get("component_sn", "")
        stage = request.GET.get("stage", "")
        testitem = request.GET.get("testitem", "")
        waittime = request.GET.get("waittime", "")
        starttime = request.GET.get("starttime", "")
        endtime = request.GET.get("endtime", "")
        teststatus = request.GET.get("teststatus", "")
        errorcode = request.GET.get("errorcode", "")
        errordescription = request.GET.get("errordescription", "")
        operatorid = request.GET.get("operatorid", "")
        startcreatetime = request.GET.get("startcreatetime", "")
        endcreatetime = request.GET.get("endcreatetime", "")
        isvalid = request.GET.get("isvalid", "")
        is_manual = request.GET.get("is_manual", "")
        # is_manual判断
        if (not is_manual) or (is_manual == "1") or (is_manual.upper() == "TRUE"):
            manual = True
        else:
            manual = False

        query = 'select "rack_sn","component_id","component_sn","stage","testitem","waittime",to_char("starttime",\'yyyy-MM-dd hh24:mi:ss\'),to_char("endtime",\'yyyy-MM-dd hh24:mi:ss\'),"teststatus","errorcode","errordescription","operatorid",to_char("createtime",\'yyyy-MM-dd hh24:mi:ss\'),"isvalid","ismanual"'
        sql = ' from "testitemrecordhistory" where true '
        if rack_sn:
            sql = sql + 'and "rack_sn" = \'' + rack_sn + '\''
        if component_id:
            sql = sql + 'and "component_id" = \'' + component_id + '\''
        if component_sn:
            sql = sql + 'and "component_sn" = \'' + component_sn + '\''
        if stage:
            sql = sql + 'and "stage" = \'' + stage + '\''
        if testitem:
            sql = sql + 'and "testitem" = \'' + testitem + '\''
        if waittime:
            sql = sql + 'and "waittime" = \'' + waittime + '\''
        if starttime:
            sql = sql + ' and "starttime" >= \'' + starttime + '\''
        if endtime:
            sql = sql + ' and "endtime" <= \'' + endtime + '\''
        if teststatus:
            sql = sql + 'and "teststatus" = \'' + teststatus + '\''
        if errorcode:
            sql = sql + 'and "errorcode" = \'' + errorcode + '\''
        if errordescription:
            sql = sql + 'and "errordescription" = \'' + errordescription + '\''
        if operatorid:
            sql = sql + 'and "operatorid" = \'' + operatorid + '\''
        if startcreatetime:
            sql = sql + 'and "createtime">= \'' + startcreatetime + '\''
        if endcreatetime:
            sql = sql + 'and "createtime" <= \'' + endcreatetime + '\''
        if isvalid:
            sql = sql + 'and "isvalid" = \'' + isvalid + '\''
        if is_manual:
            sql = sql + 'and "ismanual" = \'' + manual + '\''
        try:
            connection = connections['l11_test_primary']
            cur = connection.cursor()
            cur.execute(query + sql)
            query_data = cur.fetchall()
            cur.close()
            all_data = []
            k = [
                'rack_sn',
                'component_id',
                'component_sn',
                'stage',
                'testitem',
                'waittime',
                'starttime',
                'endtime',
                'teststatus',
                'errorcode',
                'errordescription',
                'operatorid',
                'createtime',
                'isvalid',
                'is_manual',
            ]
            for i in query_data:
                jsondata = dict(zip(k, i))
                all_data.append(jsondata)
            return JsonResponse(
                {
                    'code': 200,
                    'data': all_data,
                    'message': 'Query test item record history success',
                }
            )
        except:
            return JsonResponse(
                {
                    'code': 400,
                    'data': 'no data',
                    'message': 'Query test item record history error',
                }
            )
