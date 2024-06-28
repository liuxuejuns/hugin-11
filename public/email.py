import datetime
import re

from django.http import JsonResponse
import pandas as pd
from zeep import Client

from rack.models import RackNode
from component.models import ComponentNode,RackComponentNode


def send_email(Receivers, ccReceivers, title, html_string,data):
    client = Client("http://10.41.95.141:90/webservice/?wsdl")
    subject = title
    Message = html_string
    enclosure_list = {}
    enclosure_Value = {'name': title, 'type': '', 'data': data}
    enclosure_list['_Value'] = [enclosure_Value]
    result = client.service.SendMail(toReceivers=Receivers,
                                     ccReceivers=ccReceivers, 
                                     subject=subject,
                                     content=Message,
                                     contentImageNameList={}, 
                                     enclosureList=enclosure_list)

def get_component_test_data():
    '''
        获取所有component为fail的数据
    '''
    component_fields = ['id','sn','testitemrecord__stage','testitemrecord__testitem','testitemrecord__starttime',
    'testitemrecord__endtime','testitemrecord__errorcode','testitemrecord__errordescription','component_id__name']
    componet_node_lis = ComponentNode.objects.filter(is_valid=True,testitemrecord__teststatus=4).values(*component_fields)
    # print("componet_node_lis",componet_node_lis)
    res = list()
    for c_n_item in componet_node_lis:
        rack_node_id = RackComponentNode.objects.filter(component_node_id=c_n_item["id"]).values('rack_node_id')[0]['rack_node_id']
        print("rack_node_id",rack_node_id)
        rack_node_fields = ['id','rack_id__name','rack_id__model_name','racklocation__area_id__area','racklocation__area_id__floor']
        rack_node_obj = RackNode.objects.filter(id=rack_node_id).values(*rack_node_fields)[0]
        print("rack_node_obj",rack_node_obj)
        current_time = datetime.datetime.now()
        s_time = c_n_item['testitemrecord__starttime'].strftime('%Y-%m-%d %H:%M:%S')
        e_time = c_n_item['testitemrecord__endtime'].strftime('%Y-%m-%d %H:%M:%S')
        first_time = datetime.datetime.strptime(s_time, "%Y-%m-%d %H:%M:%S")
        end_time = datetime.datetime.strptime(e_time, "%Y-%m-%d %H:%M:%S")
        test_total_seconds = (current_time - first_time).total_seconds()
        fail_total_seconds = (current_time - end_time).total_seconds()

        # 来获取准确的时间差，并将时间差转换为秒,四舍五入，保留一位小数
        test_hours = round(test_total_seconds / 3600,1)
        fail_hours = round(fail_total_seconds / 3600,1)
        data_dict = {
            "id":c_n_item['id'],
            "stage":c_n_item["testitemrecord__stage"],
            "test_item":c_n_item['testitemrecord__testitem'],
            "start_time":c_n_item['testitemrecord__starttime'].strftime("%m/%d/%Y/ %H:%M"),
            "end_time":c_n_item['testitemrecord__endtime'].strftime("%m/%d/%Y/ %H:%M"),
            "error_code":c_n_item['testitemrecord__errorcode'],
            "error_description":c_n_item['testitemrecord__errordescription'],
            "sn":c_n_item['sn'],
            "component_name":c_n_item['component_id__name'],
            "rack_name":rack_node_obj['rack_id__name'],
            "rack_model_name":rack_node_obj['rack_id__model_name'],
            "area":rack_node_obj['racklocation__area_id__area'],
            "floor":rack_node_obj['racklocation__area_id__floor'],
            "testing_time":test_hours,
            "fail_time":fail_hours,
        }
        res.append(data_dict)

    return res

def set_html_color(html_string):
    # 找到浮点数
    result = re.findall(r"<td>\d+\.\d</td>",html_string)
    for i in result:
        num = re.findall(r"\d+\.\d",i)[0]
        if float(num) >= 10:
            # 如果距离现在超过10小时，则设置红色
            html_string = re.sub("<td>{}</td>".format(num),"<td style='color:red;'><b>{}</b></td>".format(num),html_string)
    return html_string



def email_data(request):
    # 具体要执行的代码
    res =  get_component_test_data()
    df = pd.DataFrame(res)
    now_time = datetime.datetime.now()
    current_time = datetime.datetime.strftime(now_time,'%Y%m%d_%H:%M:%S')
    # 转化HTML
    html_string = '''
        <html>
        <head><title>HTML Pandas Dataframe with CSS</title></head>
        <link rel="stylesheet" type="text/css" href="df_style.css"/>
        <body>
            <h1>{}</h1>
            {}
        </body>
        </html>
    '''.format("test"+current_time,df.to_html(header = True,index = False))    

    html_string = set_html_color(html_string)
    writer = pd.ExcelWriter('my1.xlsx')
    df.to_excel(writer,float_format='%.5f',index=False)
    writer.save()
    with open('my1.xlsx','rb') as fd:
        send_email("Maple_Liu@wistron.com,Sean_TS_Wang@wistron.com", "", 'my1.xlsx',html_string,fd.read())

    return JsonResponse({"test":"ok"})