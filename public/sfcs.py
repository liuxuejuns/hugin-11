from requests import Session
from zeep import Client
from zeep.transports import Transport
from django.http import JsonResponse
from django.core.exceptions import ValidationError

from component.models import ComponentNode, Component


# WS_URL1 = "https://mic136.wistron.com:126//Tester.webservice/WebService.asmx?WSDL"
WS_URL1 = "https://10.41.16.183:126//Tester.webservice/WebService.asmx?WSDL"  # 测试
session = Session()
session.verify = False
transport = Transport(session=session)


def test_webservice(s):
    # {'pn': '74-105537-17', 'mo': 'V10000093270', 'model': '7841'}
    # component_obj = ComponentNode.objects.get(id=52).component_id
    # component_data = Component.objects.filter(id=component_obj.id).values("pn__pn","mo__mo","modelname__model_name")
    # print("component_obj",component_obj.id)
    # data = {
    #     "pn":component_data[0]["pn__pn"],
    #     "mo":component_data[0]["mo__mo"],
    #     "model":component_data[0]["modelname__model_name"],
    # }
    # g_args = ['WZP254105GA']
    # res = GetDynamicData(*g_args)
    # print("data",data)
    # print("res",res)

    # isverify = False
    # if isinstance(res,dict):
    #     for key in data:
    #         print(key)
    #         if data[key]:
    #             if data[key] == res[key]:
    #                 isverify = True
    #                 break
    #             else:
    #                 break
    # c_args = ['11','TP']
    # # c_args = ['TLABL11001','TN']
    # res = CheckRoute(*c_args)
    # print("res",res)
    # if res['state'] in (-1,0):
    #     print('error')
    # elif res['state'] == 2:
    #     print('break')
    # print(isverify)
    return JsonResponse({"test": "ok"})


# def GetDynamicData(id, name, value):
def GetDynamicData(sn):
    mes = {'sn': "", 'pn': "", 'mo': "", 'model': ""}
    try:
        client = Client(WS_URL1, transport=transport)
    except Exception as e:
        return repr(e)

    # id = client.get_type('xsd:string')(id)
    # name = client.get_type('xsd:string')(name)
    sn = client.get_type('xsd:string')(sn)
    ans = client.service.GetDynamicData(
        DynQueryID="GETINFOFORIPQC",
        CriteriaName="USN",
        CriteriaValue=sn,
    )
    # print("ans",ans)
    if '_value_1' in ans['_value_1']:
        datas = ans['_value_1']['_value_1']
        data = datas[0]
        mes["sn"] = data['Table']['USN']
        mes["pn"] = data['Table']['UPN']
        mes["mo"] = data['Table']['MO']
        mes["model"] = data['Table']['MODEL']
    return mes


def CheckRoute(USN, stage):
    '''
    SFCF01426: Unit: 11 not exist!
    SFCF00002: Please go to [TN - Pre-Runin].  This USN as [TLABL11001] Route error
    OK
    state: 0:sn not exist 1:stage error 2:ok
    '''
    try:
        client = Client(WS_URL1, transport=transport)
        USN = client.get_type('xsd:string')(USN)
        stage = client.get_type('xsd:string')(stage)
        ans = client.service.CheckRoute(
            UnitSerialNumber=USN,
            StageCode=stage,
        )
    except Exception as e:
        res = {"state": -1, "msg": repr(e)}
        return res
    if "not exist" in ans:
        res = {"state": 0, "msg": "sn not exist"}
        return res
    elif ans == 'OK':
        res = {"state": 2, "msg": "ok"}
        return res
    else:
        res = {"state": 1, "msg": "stage error"}
        return res


def Complete(sn, stage, errorcode, employeeID, teststatus):
    try:
        # client = Client(WS_URL1, transport=transport)
        # if teststatus == "fail":
        #     errorcode_list = []
        #     errorcode_list.append(errorcode)
        #     ans = client.service.Complete(
        #         UnitSerialNumber=sn,
        #         Line="",
        #         StageCode=stage,
        #         StationName=stage,
        #         EmployeeID=employeeID,
        #         Pass=False,
        #         TrnDatas=errorcode_list,
        #     )
        # elif teststatus == "pass":
        #     ans = client.service.Complete(
        #         UnitSerialNumber=sn,
        #         Line="",
        #         StageCode=stage,
        #         StationName=stage,
        #         EmployeeID=employeeID,
        #         Pass=True,
        #         TrnDatas=[],
        #     )
        ans = "OK"  # 测试时候不需要上传sfcs则注释上面并打开这个
        return ans
    except Exception as e:
        raise ValidationError('upload sfcs error' + e)
