import json
import logging

from django.db import IntegrityError
from django.views import View
from django.http import JsonResponse
from django.http.request import QueryDict
from django.core.paginator import Paginator
from django.db import transaction


from component.models import Component,RackComponent,SN,PN,MO,ComponentNode,RackComponentNode
from component.form import ComponentForm,ComponentAllForm,SnForm,PnForm,MoForm,ModelNameForm
from public.sfcs import CheckRoute
# from component.form import FilterTypeForm

# Create your views here.
logger_api = logging.getLogger('api')


class ComponentList(View):

    def get(self,request):
        '''
            获取component
        '''
        # 分页
        page = request.GET.get('page',1) # 获取第几页
        limit = request.GET.get('limit',10) # 每页有多少条数据

        fields = ["id",'name','model','test_plan','stage', 'is_iperf', 'col','row']
        component_list = Component.objects.all().values(*fields)
        paginator = Paginator(component_list,limit) #创建一个Paginator对象，将component_list作为要进行分页的数据集合，并指定每页显示的数据条数为limit。
        page_1 = paginator.get_page(page) #获取第page页的数据。
        res = get_sn_pn_mo(page_1) #调用get_sn_pn_mo函数，将page_1作为参数传递给它，获取关联的SN、PN和MO对象的数据。
        list1 = [] #创建空的列表，用于存储component对象的字典。
        for item in res:
            if item['is_iperf']:
                item['is_iperf'] = 1
            else:
                item['is_iperf'] = 0 #根据is_iperf的值将其替换为0或1，以适应前端的需要。
            list1.append(item) #将处理后的组件信息添加到列表中
        data = {
            "code":200,
            "data":list1,
            "msg":"success",
            "count":paginator.count
        }
        return JsonResponse(data)
    
    def post(self,request):
        '''
            创建component
        '''
        form = ComponentAllForm(request.POST) 
        if form.is_valid(): 
            cleaned_data = form.cleaned_data  #获取表单经过验证后的数据，清理并存储在cleaned_data字典中。
            sn = cleaned_data["sn"]  #获取cleaned_data字典中的sn值。
            pn = cleaned_data["pn"] 
            mo = cleaned_data["mo"]
            c_type = cleaned_data["type"]  
            component_data = {  #创建component_data字典，用于存储component对象的数据。
                "test_plan":cleaned_data["test_plan"], 
                "col":cleaned_data["col"], 
                "row":cleaned_data["row"],
                "name":cleaned_data["name"],
                "model":cleaned_data["model"], 
                "type":cleaned_data["type"],
                "stage":cleaned_data["stage"], 
                "is_iperf": cleaned_data['is_iperf'] if cleaned_data['is_iperf'] else 0, 
            }

            # if int(c_type):
            #     component_data["stage"] = "SV"
            # else:
            #     component_data["stage"] = cleaned_data["stage"]
            # return JsonResponse({"code":201,"msg":"test component success"})
            try:
                with transaction.atomic(using='l11_test_primary'): #在使用事务时，将数据库连接切换到l11_test_primary数据库。
                    component_obj = Component.objects.create(**component_data) #创建component对象。
                    if sn: 
                        SN.objects.create(sn=sn,component_id=component_obj)  #如果sn存在，则创建一个关联到该组件对象的SN对象，并将其保存到数据库中。
                    if pn:
                        PN.objects.create(pn=pn,component_id=component_obj) #如果pn存在，则创建一个关联到该组件对象的PN对象，并将其保存到数据库中。
                    if mo:
                        MO.objects.create(mo=mo,component_id=component_obj)
            except Exception as e:
                logger_api.error(e)
                return JsonResponse({"code":400,"msg":repr(e)})
            return JsonResponse({"code":201,"msg":"add component success"})
        else:
            return JsonResponse({"code":400,"msg":form.errors})

def get_sn_pn_mo(data):

    for item in data:
        sn_obj = SN.objects.filter(component_id=item["id"]).values()  #根据当前元素的id从SN对象中进行过滤，获取关联的SN对象的查询集。
        pn_obj = PN.objects.filter(component_id=item["id"]).values() #根据当前元素的id从PN对象中进行过滤，获取关联的PN对象的查询集。
        mo_obj = MO.objects.filter(component_id=item["id"]).values()
        sn_list = list() #创建空的列表，用于存储SN、PN和MO对象的字典
        pn_list = list() #创建空的列表，用于存储SN、PN和MO对象的字典
        mo_list = list()
        for sn_item in list(sn_obj): #遍历SN对象的查询集，将每个SN对象的id和sn存储到字典中，然后将字典添加到列表中。
            sn_dic = dict() #创建空的字典，用于存储SN对象的id和sn
            sn_dic["id"] = sn_item["id"] 
            sn_dic["sn"] = sn_item["sn"] #将SN对象的"id"和"sn"值分别存储在字典中。
            sn_list.append(sn_dic) #将SN对象的字典添加到SN列表中。
        else:
            item["sns"] = sn_list #将SN列表添加到当前元素的字典中。
        for pn_item in list(pn_obj): #遍历PN对象的查询集，将每个PN对象的id和pn存储到字典中，然后将字典添加到列表中。
            pn_dic = dict()
            pn_dic["id"] = pn_item["id"]
            pn_dic["pn"] = pn_item["pn"]
            pn_list.append(pn_dic)
        else:
            item["pns"] = pn_list
        for mo_item in list(mo_obj):
            mo_dic = dict()
            mo_dic["id"] = mo_item["id"]
            mo_dic["mo"] = mo_item["mo"]
            mo_list.append(mo_dic)
        else:
            item["mos"] = mo_list
    return data


class ComponentNodeDetail(View):

    def get(self,request,id):
        fields = ['operator_id','sn','current_stage']
        component_node_obj = ComponentNode.objects.filter(id=id).values(*fields)
        if component_node_obj.exists():
            data = {
                "code":200,
                "data":[data for data in component_node_obj],
                "msg":"success"
            }
            return JsonResponse(data)
        else:
            return JsonResponse({"code":404,"msg":"Component_node is not exist"})


class ComponentDetail(View):

    def get(self,request,id):
        fields = ["id",'name','model','test_plan','stage','col','row']
        component_obj = Component.objects.filter(id=id).values(*fields)
        if component_obj.exists():
            res = get_sn_pn_mo(component_obj)
            data = {
                "code":200,
                "data":res[0],
                "msg":"success",
            }
            return JsonResponse(data)
        else:
            return JsonResponse({"code":404,"msg":"Component is not exist"})

    def patch(self,request,id):
        '''
            修改component
        '''
        component_obj = Component.objects.filter(id=id).values()
        if component_obj.exists():
            fields = ['name','model','stage','test_plan','col','row']
            datas = QueryDict(request.body).dict()  #获取请求体中的数据，并将其转换为字典。
            for field in fields:
                if field not in datas:
                    datas[field] = component_obj[0][field] #如果请求体中没有某个字段，则将该字段的值设置为原来的值。
            form = ComponentForm(datas) #将datas字典传递给ComponentForm表单，进行验证。
            if form.is_valid():
                cleaned_data = form.cleaned_data
                cleaned_data.pop("row")
                cleaned_data.pop("col")
                Component.objects.filter(id=id).update(**cleaned_data)
                return JsonResponse({"code":201,"msg":"Component update success"})
            else:
                return JsonResponse({"code":400,"msg":form.errors})
        else:
            return JsonResponse({"code":404,"msg":"Component is not exist"})

    def delete(self,request,id):
        '''
            删除component
        '''
        component_obj = Component.objects.filter(id=id)
        # rack_component_obj = RackComponent.objects.filter(component_id=id)
        component_node_obj = ComponentNode.objects.filter(component_id=id)

        if component_obj.exists() and not component_node_obj.exists():
            component_obj.delete()
            return JsonResponse({"code":204,"msg":"del success"})
        else:
            return JsonResponse({"code":404,"msg":"Component is not exist or componentnode is binding"})


class SnList(View):

    def get(self,request,component_id):
        component_obj = Component.objects.filter(id=component_id)
        if component_obj.exists():
            fields = ['id','sn','component_id__id']
            sn_list = SN.objects.filter(component_id=component_id).values(*fields)
            data = {
                "code":200,
                "data":[data for data in sn_list],
                "msg":"success"
            }
            return JsonResponse(data)
        else:
            return JsonResponse({"code":400,"msg":"Component is not exist"})
    
    def post(self,request,component_id):
        component_obj = Component.objects.filter(id=component_id)
        if component_obj.exists():
            form = SnForm(request.POST)
            if form.is_valid():
                cleaned_data = form.cleaned_data
                cleaned_data["component_id"] = component_obj[0]
                try:
                    SN.objects.create(**cleaned_data)
                except IntegrityError:
                    return JsonResponse({"code":400,"msg":"sn is exist"})
                return JsonResponse({"code":201,"msg":"add Sn success"})
            else:
                return JsonResponse({"code":400,"msg":form.errors})
        else:
            return JsonResponse({"code":400,"msg":"Component is not exist"})


class Sndetail(View):

    def delete(self,request,id):
        try:
            sn_obj = SN.objects.get(id=id)
        except Exception as r:
            msg = '%s' % r
            return JsonResponse({"code":400,"msg":msg})
        sn_obj.delete()
        return JsonResponse({"code":204,"msg":"del success"})


class PnList(View):

    def get(self,request,component_id):
        component_obj = Component.objects.filter(id=component_id)
        if component_obj.exists(): 
            fields = ['id','pn','component_id__id']
            pn_list = PN.objects.filter(component_id=component_id).values(*fields)
            data = {
                "code":200,
                "data":[data for data in pn_list],
                "msg":"success"
            }
            return JsonResponse(data)
        else:
            return JsonResponse({"code":400,"msg":"Component is not exist"})
    
    def post(self,request,component_id):
        component_obj = Component.objects.filter(id=component_id)
        if component_obj.exists():
            form = PnForm(request.POST)
            if form.is_valid():
                cleaned_data = form.cleaned_data
                cleaned_data["component_id"] = component_obj[0]
                try:
                    PN.objects.create(**cleaned_data)
                except IntegrityError:
                    return JsonResponse({"code":400,"msg":"Pn is exist"})
                return JsonResponse({"code":201,"msg":"add Pn success"})
            else:
                return JsonResponse({"code":400,"msg":form.errors})
        else:
            return JsonResponse({"code":400,"msg":"Component is not exist"})


class Pndetail(View):

    def delete(self,request,id):
        try:
            pn_obj = PN.objects.get(id=id)
        except Exception as r:
            msg = '%s' % r
            return JsonResponse({"code":400,"msg":msg})
        pn_obj.delete()
        return JsonResponse({"code":204,"msg":"del success"})

       
class MoList(View):

    def get(self,request,component_id):
        component_obj = Component.objects.filter(id=component_id)
        if component_obj.exists():
            fields = ['id','mo','component_id__id']
            mo_list = MO.objects.filter(component_id=component_id).values(*fields)
            data = {
                "code":200,
                "data":[data for data in mo_list],
                "msg":"success"
            }
            return JsonResponse(data)
        else:
            return JsonResponse({"code":400,"msg":"Component is not exist"})
    
    def post(self,request,component_id):
        component_obj = Component.objects.filter(id=component_id)
        if component_obj.exists():
            form = MoForm(request.POST)
            if form.is_valid():
                cleaned_data = form.cleaned_data
                cleaned_data["component_id"] = component_obj[0]
                try:
                    MO.objects.create(**cleaned_data)
                except IntegrityError:
                    return JsonResponse({"code":400,"msg":"Mo is exist"})
                return JsonResponse({"code":201,"msg":"add Mo success"})
            else:
                return JsonResponse({"code":400,"msg":form.errors})
        else:
            return JsonResponse({"code":400,"msg":"Component is not exist"})


class Modetail(View):

    def delete(self,request,id):
        try:
            mo_obj = MO.objects.get(id=id)
        except Exception as r:
            msg = '%s' % r
            return JsonResponse({"code":400,"msg":msg})
        mo_obj.delete()
        return JsonResponse({"code":204,"msg":"del success"})


class GetComponentBySn(View):

    def get(self,request):
        form = SnForm(request.GET)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            componentnode_obj = ComponentNode.objects.filter(**cleaned_data).values("id","component_id_id","current_stage","teststatus") 
            if componentnode_obj.exists():
                fields = ["id","name",'test_plan','stage','col','row','type']
                component_obj = Component.objects.filter(id=componentnode_obj[0]["component_id_id"]).values(*fields)[0]
                r_c_n = RackComponentNode.objects.filter(component_node_id=componentnode_obj[0]["id"]).values("rack_node_id__sn")
                component_obj["current_stage"] = componentnode_obj[0]["current_stage"]
                component_obj["staus"] = componentnode_obj[0]["teststatus"]
                component_obj["rack_sn"] = r_c_n[0]["rack_node_id__sn"]
                data = {
                    "code":200,
                    # "data":[data for data in component_obj],
                    "data":component_obj,
                    "msg":"success"
                }
                return JsonResponse(data) 
            else:
                return JsonResponse({"code":400,"msg":"this component sn %s is not exists" % cleaned_data['sn']})
        else:
           return JsonResponse({"code":400,"msg":form.errors})

 
# class GetComponentBySn(View):

#     def get(self,request):
#         form = SnForm(request.GET)
#         if form.is_valid():
#             cleaned_data = form.cleaned_data
#             sn_obj = SN.objects.filter(**cleaned_data).values("id","component_id")
#             fields = ["id","component_name",'test_plan','stage','col','row','component_type_id__id','rackcomponent__rack_id__rack_name']
#             # fields = ["id","component_name",'test_plan','stage','col','row','component_type_id__id']
#             component_obj = Component.objects.filter(id=sn_obj[0]["component_id"]).values(*fields)[0]
#             data = {
#                 "code":200,
#                 # "data":[data for data in component_obj],
#                 "data":component_obj,
#                 "msg":"success"
#             }
#             return JsonResponse(data) 
#         else:
#            return JsonResponse({"code":400,"msg":form.errors}) 


# class GetComponentByPn(View):

#     def get(self,request):
#         form = PnForm(request.GET)
#         if form.is_valid():
#             cleaned_data = form.cleaned_data
#             pn_obj = PN.objects.filter(**cleaned_data).values("id")
#             fields = ["id","component_name",'test_plan','stage','col','row','component_type_id__id','rackcomponent__rack_id__rack_name']
#             component_obj = Component.objects.filter(id=pn_obj[0]["id"]).values(*fields)[0]
#             data = {
#                 "code":200,
#                 # "data":[data for data in component_obj],
#                 "data":component_obj,
#                 "msg":"success"
#             }
#             return JsonResponse(data) 
#         else:
#            return JsonResponse({"code":400,"msg":form.errors}) 


# class GetComponentByMo(View):

#     def get(self,request):
#         form = MoForm(request.GET)
#         if form.is_valid():
#             cleaned_data = form.cleaned_data
#             mo_obj = MO.objects.filter(**cleaned_data).values("id")
#             fields = ["id","component_name",'test_plan','stage','col','row','component_type_id__id','rackcomponent__rack_id__rack_name']
#             component_obj = Component.objects.filter(id=mo_obj[0]["id"]).values(*fields)
#             data = {
#                 "code":200,
#                 # "data":[data for data in component_obj],
#                 "data":component_obj,
#                 "msg":"success"
#             }
#             return JsonResponse(data) 
#         else:
#            return JsonResponse({"code":400,"msg":form.errors}) 

