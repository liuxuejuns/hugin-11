from ast import operator
import logging
import json
import requests

from django.views import View
from django.http import JsonResponse
from django.http.request import QueryDict
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Q

from rack.models import Rack, RackLocation, RackNode, TestStep
from rack.form import (
    RackInfoForm,
    RackComponentForm,
    RackLocationForm,
    RackLocationCheckinForm,
)
from rack.form import (
    RackLocationDeleaveForm,
    RackLocationDeleaveMoreForm,
    ScanInForm,
    RackSnForm,
)
from testrecord.models import TestItemRecord, ComponentObject
from component.models import RackComponent, ComponentNode, Component, RackComponentNode
from area.models import Area
from history.models import TestItemHistoryRecord, RackHistory

from public.sfcs import Complete

# Create your views here.
logger_api = logging.getLogger('api')


class RackList(View):
    def get(self, request):
        '''
        获取所有rack
        '''
        # 分页
        page = request.GET.get('page', 1)  # 获取第几页
        limit = request.GET.get('limit', 10)  # 每页有多少条数据
        fields = [
            'id',
            'name',
            'model_name',
            'operator_id',
            'stage',
            'rack_row',
            'rack_col',
        ]
        rack_list = Rack.objects.all().values(*fields)
        paginator = Paginator(rack_list, limit)
        page_1 = paginator.get_page(page)
        data = {
            "code": 200,
            "data": [rack for rack in page_1],
            "msg": "success",
            "count": paginator.count,
        }
        return JsonResponse(data)

    def post(self, request):
        '''
        添加rack
        '''
        form = RackInfoForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            stage_lis = cleaned_data["stage"].split(",") #将stage字段拆分为一个列表，通过逗号进行分隔。
            test_step_list = []
            or_index = 0
            try:
                with transaction.atomic(using='l11_test_primary'):
                    rack_obj = Rack.objects.create(**cleaned_data)
                    for index in range(1, len(stage_lis)):
                        stage_type = 0  # 0:L10;1:非L10
                        if index == 4:
                            stage_type = 1
                        test_step_data = {
                            "current_stage": stage_lis[or_index],
                            "next_stage": stage_lis[index],
                            "rack": rack_obj.id,
                            "stage_type": stage_type,
                        }
                        test_step_list.append(TestStep(**test_step_data))
                        or_index, index = index, index + 1
                    else:
                        if len(stage_lis) == 4:
                            stage_type = 1
                        else:
                            stage_type = 0
                        test_step_data = {
                            "current_stage": stage_lis[or_index],
                            "next_stage": "-1",
                            "rack": rack_obj.id,
                            "stage_type": stage_type,
                        }
                        test_step_list.append(TestStep(**test_step_data))
                    TestStep.objects.bulk_create(test_step_list) #使用bulk_create()方法将整个test_step_list批量创建为TestStep对象，并将其保存到数据库中。
            except Exception as e:
                print(e)
                logger_api.error(e)
                return JsonResponse({"code": 400, "msg": repr(e)})
            return JsonResponse({"code": 201, "msg": "add rack success"})
        else:
            return JsonResponse({"code": 400, "msg": form.errors})


class RackDetail(View):
    def patch(self, request, id):
        rack_obj = Rack.objects.filter(id=id).values()[0]
        is_stage = False
        if len(rack_obj):
            fields = [
                'name',
                'model_name',
                'operator_id',
                'stage',
                'rack_col',
                'rack_row',
            ]
            datas = QueryDict(request.body).dict()
            if datas["stage"]:
                if not datas["stage"] == rack_obj["stage"]:
                    is_stage = True
            for field in fields:
                if field not in datas:
                    datas[field] = rack_obj[field]
            form = RackInfoForm(datas)
            if form.is_valid():
                cleaned_data = form.cleaned_data
                try:
                    Rack.objects.filter(id=id).update(**cleaned_data)
                    if is_stage:
                        TestStep.objects.filter(rack=rack_obj["id"]).delete()
                        stage_lis = cleaned_data["stage"].split(",")
                        test_step_list = []
                        or_index = 0
                        for index in range(1, len(stage_lis)):
                            stage_type = 0  # 0:L10;1:非L10
                            if index == 4:
                                stage_type = 1
                            test_step_data = {
                                "current_stage": stage_lis[or_index],
                                "next_stage": stage_lis[index],
                                "rack": rack_obj["id"],
                                "stage_type": stage_type,
                            }
                            test_step_list.append(TestStep(**test_step_data))
                            or_index, index = index, index + 1
                        else:
                            if len(stage_lis) == 4:
                                stage_type = 1
                            else:
                                stage_type = 0
                            test_step_data = {
                                "current_stage": stage_lis[or_index],
                                "next_stage": "-1",
                                "rack": rack_obj["id"],
                                "stage_type": stage_type,
                            }
                            test_step_list.append(TestStep(**test_step_data))
                        TestStep.objects.bulk_create(test_step_list)
                except IntegrityError:
                    return JsonResponse(
                        {
                            "code": 400,
                            "msg": "model_name %s is exist"
                            % cleaned_data["model_name"],
                        }
                    )
                return JsonResponse({"code": 201, "msg": "Rack update success"})
            else:
                return JsonResponse({"code": 400, "msg": form.errors})
        else:
            return JsonResponse({"code": 404, "msg": "rack is not exist"})

    def delete(self, request, id):
        rack_obj = Rack.objects.filter(id=id)
        rack_node_obj = RackNode.objects.filter(rack_id=id)
        if rack_obj.exists() and not len(rack_node_obj):
            rack_obj.delete()
            return JsonResponse({"code": 204, "msg": "del success"})
        else:
            return JsonResponse(
                {"code": 404, "msg": "rack is not exist or rack is isbinded"}
            )


class RackComponentList(View):
    def get(self, request, rack_id):
        fields = [
            'id',
            'name',
            'model_name',
            'operator_id',
            'rack_col',
            'rack_row',
        ]
        rack_obj = Rack.objects.filter(id=rack_id).values(*fields)
        if rack_obj.exists():
            rack_data = rack_obj[0]
            rack_component_fields = [
                'id',
                'start_row',
                'end_row',
                'start_col',
                'end_col',
                'component_id__id',
                'component_id__name',
            ]
            # rack_component_fields = ['id','start_row','end_row','start_col','end_col',
            # 'component_id__id','componentnode__id','componentnode__testitemrecord__id','componentnode__testitemrecord__teststatus']
            rack_component_list = RackComponent.objects.filter(rack_id=rack_id)
            rack_data["rackcomponents"] = (
                [
                    rack_component
                    for rack_component in rack_component_list.values(
                        *rack_component_fields
                    )
                ]
                if rack_component_list.exists()
                else []
            )
            data = {"code": 200, "data": rack_data, "msg": "success"}
            return JsonResponse(data)
        else:
            return JsonResponse({"code": 404, "msg": "rack is not exist"})


class RackComponentNodeList(View):
    def get(self, request, rack_node_id):
        fields = [
            'id',
            'rack_id__id',
            'rack_id__name',
            'rack_id__stage',
            'rack_id__rack_row',
            'rack_id__rack_col',
            'current_stage',
            'operator_id',
            'sn',
            'change',
            'type',
        ]
        racknode_obj = RackNode.objects.filter(id=rack_node_id).values(*fields)
        if racknode_obj.exists():
            rack_data = racknode_obj[0]
            # rack_c_n_fields = ['id','start_row','end_row','start_col','end_col','component_id__id','component_id__name']
            rack_c_n_fields = [
                'id',
                'start_row',
                'end_row',
                'start_col',
                'end_col',
                'component_node_id__component_id',
                'component_node_id__id',
                'component_node_id__sn',
                'component_node_id__change',
                'component_node_id__current_stage',
                'component_node_id__teststatus',
                'component_node_id__component_id__name',
            ]
            rack_data["rackcomponentnodes"] = []
            rack_c_n_list = RackComponentNode.objects.filter(
                rack_node_id=rack_node_id, component_node_id__is_valid=True
            )
            for rack_c_n in rack_c_n_list.values(*rack_c_n_fields):
                t_i_r_fields = ['id', 'teststatus', 'testitem']
                t_i_r_obj = TestItemRecord.objects.filter(
                    sn=rack_c_n["component_node_id__sn"],
                    stage=rack_c_n["component_node_id__current_stage"],
                    isvalid=True,
                ).values(*t_i_r_fields)
                if t_i_r_obj.exists():
                    rack_c_n["testitemrecord_id"] = t_i_r_obj[0]["id"]
                    rack_c_n["testitemrecord_testitem"] = t_i_r_obj[0]["testitem"]
                else:
                    rack_c_n["testitemrecord_id"] = None
                    rack_c_n["testitemrecord_testitem"] = 'NA'
                t_i_r_ismanual = TestItemRecord.objects.filter(
                    sn=rack_c_n["component_node_id__sn"], ismanual=True, teststatus='2'
                )
                if t_i_r_ismanual.exists():
                    rack_c_n["ismanual"] = True
                else:
                    rack_c_n["ismanual"] = False
                rack_data["rackcomponentnodes"].append(rack_c_n)
            data = {"code": 200, "data": rack_data, "msg": "success"}
            return JsonResponse(data)
        else:
            return JsonResponse({"code": 404, "msg": "racknode is not exist"})


class RackComponentDeleave(View):
    def delete(self, request, id):
        '''
        解绑rack和component;
        r_c:rack_component
        '''
        r_c_obj = RackComponent.objects.filter(id=id)
        if r_c_obj.exists():
            r_c_obj.delete()
            return JsonResponse({"code": 204, "msg": "Deleave success"})
        else:
            return JsonResponse({"code": 404, "msg": "rackcomponent is not exist"})


class RackComponentAssembly(View):
    def post(self, request):
        form = RackComponentForm(request.POST)
        if form.is_valid():
            clean_data = form.cleaned_data
            RackComponent.objects.create(**clean_data)
            return JsonResponse({"code": 201, "msg": "add rackcomponent success"})
        else:
            return JsonResponse({"code": 400, "msg": form.errors})


class RackLocationList(View):
    def get(self, request, area_id):
        area_fields = ['id', 'area', 'floor', 'current_count']
        area_lis = Area.objects.filter(id=area_id).values(*area_fields)
        if area_lis.exists():
            racklocation_fields = [
                'id',
                'name',
                'coordinateX',
                'coordinateY',
                'index',
                'rack_node_id',
                'rack_node_id__current_stage',
                'rack_node_id__teststatus',
                'rack_node_id__change',
                'rack_node_id__type',
                'rack_node_id__rack_id__model_name',
                'rack_node_id__rack_id__stage',
            ]
            racklocation_lis = RackLocation.objects.filter(area_id=area_id).values(
                *racklocation_fields
            )
            for r_l_item in racklocation_lis:
                r_n_id = r_l_item["rack_node_id"]
                if r_n_id:
                    r_c_n_objs = RackComponentNode.objects.filter(
                        rack_node_id=r_n_id
                    ).values("component_node_id__sn")
                    for r_c_n_item in r_c_n_objs:
                        t_i_r_ismanual = TestItemRecord.objects.filter(
                            sn=r_c_n_item["component_node_id__sn"],
                            ismanual=True,
                            teststatus='2',
                        )
                        if t_i_r_ismanual.exists():
                            r_l_item["ismanual"] = True
                            break
                    else:
                        r_l_item["ismanual"] = False
                else:
                    r_l_item["ismanual"] = False
            data_lis = area_lis[0]
            if racklocation_lis.exists():
                data_lis["racklocation"] = [item for item in racklocation_lis]
            else:
                data_lis["racklocation"] = []
            data = {"code": 200, "data": data_lis, "msg": "success"}
            return JsonResponse(data)
        else:
            return JsonResponse({"code": 404, "msg": "area not exist"})


class CreateRackLocation(View):
    def post(self, request, area_id):
        area_lis = Area.objects.filter(id=area_id)
        if area_lis.exists():
            datas = request.POST.dict()
            datas["area_id"] = area_id
            form = RackLocationForm(datas)
            if form.is_valid():
                cleaned_data = form.cleaned_data
                index = cleaned_data["coordinateX"] * 3 + cleaned_data["coordinateY"]
                cleaned_data["index"] = index
                cleaned_data["area_id"] = area_lis[0]
                try:
                    with transaction.atomic(using='l11_test_primary'):
                        RackLocation.objects.create(**cleaned_data)
                        rackloc_lis = RackLocation.objects.filter(area_id=area_id)
                        count = len(rackloc_lis)
                        Area.objects.filter(id=area_id).update(current_count=count)
                except Exception as e:
                    logger_api.error(e)
                    return JsonResponse({"code": 400, "msg": repr(e)})
                return JsonResponse({"code": 201, "msg": "add racklocation success"})
            else:
                return JsonResponse({"code": 400, "msg": form.errors})
        else:
            return JsonResponse({"code": 404, "msg": "area not exist"})


class RackLocationView(View):
    def get(self, request, area_id, id):
        fields = [
            "id",
            'name',
            "area_id__id",
            'coordinateX',
            'coordinateY',
            'rack_node_id',
            'rack_node_id__operator_id',
            'rack_node_id__sn',
            'rack_node_id__rack_id',
            'rack_node_id__rack_id__model_name',
            'rack_node_id__current_stage',
        ]
        racklocation_obj = RackLocation.objects.filter(id=id, area_id=area_id).values(
            *fields
        )
        if racklocation_obj.exists():
            racklocation_data = racklocation_obj[0]
            racknode_id = racklocation_data["rack_node_id"]
            # rack_c_n:rack_component_node
            rack_c_n_fields = [
                'start_row',
                'end_row',
                'start_col',
                'end_col',
                'component_node_id__operator_id',
                'component_node_id__sn',
            ]
            rack_c_n_objs = RackComponentNode.objects.filter(
                rack_node_id=racknode_id
            ).values(*rack_c_n_fields)

            # component_node_obj = ComponentNode.objects.filter(rack_location_id=id).values('id','operator_id','sn')
            racklocation_data["rackcomponentnodes"] = [
                r_c_n_item for r_c_n_item in rack_c_n_objs
            ]
            data = {
                "code": 200,
                # "data":[item for item in racklocation_obj],
                "data": racklocation_data,
                "msg": "success",
            }
            return JsonResponse(data, status=200)
        else:
            return JsonResponse({"code": 404, "msg": "racklocation not exist"})

    def patch(self, request, area_id, id):
        '''
        修改racklocation信息
        '''
        area_lis = Area.objects.filter(id=area_id)
        if area_lis.exists():
            racklocation_lis = RackLocation.objects.filter(id=id)
            if racklocation_lis.exists():
                racklocation_fields = ['coordinateX', 'coordinateY']
                racklocation_obj = racklocation_lis.values()[0]
                datas = QueryDict(request.body).dict()
                for field in racklocation_fields:
                    if field not in datas:
                        datas[field] = racklocation_obj[field]
                datas["area_id"] = area_id
                form = RackLocationForm(datas)
                if form.is_valid():
                    cleaned_data = form.cleaned_data
                    index = (
                        cleaned_data["coordinateX"] * 3 + cleaned_data["coordinateY"]
                    )
                    cleaned_data["index"] = index
                    cleaned_data.pop('area_id')
                    RackLocation.objects.filter(id=id).update(**cleaned_data)
                    return JsonResponse({"code": 201, "msg": "update success"})
                else:
                    return JsonResponse({"code": 400, "msg": form.errors})
            else:
                return JsonResponse(
                    {"code": 404, "msg": "this racklocation is not exist"}
                )
        else:
            return JsonResponse({"code": 404, "msg": "area not exist"})


class RackLocationCheckin(View):
    def post(self, request):
        form = RackLocationCheckinForm(request.POST)
        if form.is_valid():
            clean_data = form.cleaned_data
            rack_location_id = clean_data["racklocation_id"]
            clean_data.pop("racklocation_id")
            rack_id = clean_data["rack_id"]
            r_c_fields = [
                'start_row',
                'end_row',
                'start_col',
                'end_col',
                'component_id',
            ]
            rackcomponent_objs = RackComponent.objects.filter(rack_id=rack_id).values(
                *r_c_fields
            )
            stage = clean_data["stage"]
            rack_node = {
                "sn": clean_data["sn"],
                "current_stage": clean_data["stage"],
                "operator_id": clean_data["operator_id"],
                "rack_id": clean_data["rack_obj"],
                "type": clean_data["type"],
            }
            try:
                with transaction.atomic(using='l11_test_primary'):
                    rack_node_obj = RackNode.objects.create(**rack_node)
                    rackcomponentnode_list = []  # 批量创建rackcomponentnode
                    for _item in rackcomponent_objs:
                        component_id = _item["component_id"]
                        component_obj = Component.objects.filter(id=component_id)
                        componentnode_obj = ComponentNode.objects.create(
                            component_id=component_obj[0]
                        )
                        rack_c_n_data = {
                            "start_row": _item["start_row"],
                            "end_row": _item["end_row"],
                            "start_col": _item["start_col"],
                            "end_col": _item["end_col"],
                            "rack_node_id": rack_node_obj,
                            "component_node_id": componentnode_obj,
                        }
                        obj = RackComponentNode(**rack_c_n_data)
                        rackcomponentnode_list.append(obj)
                    RackComponentNode.objects.bulk_create(rackcomponentnode_list)
                    RackLocation.objects.filter(id=rack_location_id).update(
                        rack_node_id=rack_node_obj
                    )
            except Exception as e:
                print(e)
                logger_api.error(e)
                return JsonResponse({"code": 400, "msg": repr(e)})
            data = {
                "code": 200,
                "data": {"racknode_id": rack_node_obj.id},
                "msg": "success",
            }
            return JsonResponse(data)
        else:
            return JsonResponse({"code": 400, "msg": form.errors})


class RackLocationDeleave(View):
    def patch(self, request, id):
        datas = dict()
        datas["id"] = id
        form = RackLocationDeleaveForm(datas)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            racklocation_obj = cleaned_data["racklocation_obj"]
            rack_node_obj = cleaned_data["rack_node_obj"]
            r_c_n_objs = cleaned_data["r_c_n_objs"]
            t_r_obj = cleaned_data["t_r_obj"]
            t_i_r_obj = TestItemRecord.objects.filter(
                testrecordid=t_r_obj['id']
            ).values()
            try:
                with transaction.atomic(using='l11_test_primary'):
                    racklocation_obj.update(rack_node_id=None)
                    rack_node_obj.delete()
                    createtestitemrecordhistory = []
                    for i in t_i_r_obj:
                        componentnode_obj = ComponentNode.objects.filter(
                            id=i['component_node_id_id']
                        ).values()[0]
                        sn = componentnode_obj['sn']
                        componentid = componentnode_obj['component_id_id']
                        t_i_r_data = {
                            "component_id": componentid,
                            "stage": i['stage'],
                            "testitem": i['testitem'],
                            "waittime": i['waittime'],
                            "starttime": i['starttime'],
                            "endtime": i['endtime'],
                            "teststatus": i['teststatus'],
                            "errorcode": i['errorcode'],
                            "errordescription": i['errordescription'],
                            "operatorid": i['operatorid'],
                            "createtime": i['createtime'],
                            "isvalid": i['isvalid'],
                            "ismanual": i['ismanual'],
                            "sn": sn,
                        }
                        obj = TestItemHistoryRecord(**t_i_r_data)
                        createtestitemrecordhistory.append(obj)
                        TestItemRecord.objects.filter(id=i['id']).delete()
                    TestItemHistoryRecord.objects.bulk_create(
                        createtestitemrecordhistory
                    )
                    for r_c_n_obj in r_c_n_objs:
                        ComponentNode.objects.filter(
                            id=r_c_n_obj["component_node_id_id"]
                        ).delete()
            except Exception as e:
                print(e)
                logger_api.error(e)
                return JsonResponse({"code": 400, "msg": repr(e)})

            return JsonResponse({"code": 201, "msg": "update success"})
        else:
            return JsonResponse({"code": 400, "msg": form.errors})


class RackLocationDeleaveMore(View):
    def post(self, request):
        form = RackLocationDeleaveMoreForm(request.POST)
        if form.is_valid():
            # print(form.cleaned_data)
            racknode_obj = form.cleaned_data['racknode_objs']  #从表单数据中获取名为racknode_objs的字段值，赋值给racknode_obj。
            racklocation_obj = form.cleaned_data['racklocation_objs'] 
            t_i_h_r_new_data = []  # 批量创建testitemrecordhistory
            rackhistory_objs = []  # 批量创建rackhistory
            racknode_ids = []
            componentnode_ids = []
            t_i_r_ids = []
            c_n_sn_all_pass = []  # sn全部pass的需要保留testitemrecord
            for i in racklocation_obj:  # 批量更新racklocation
                i['rack_node_id_id'] = None #对racklocation_obj进行遍历，将每个元素的rack_node_id_id字段设置为None，用于更新相应的RackLocation对象。
            for racknode_item in racknode_obj:
                rack_sn = racknode_item['sn']
                rack_type = racknode_item['type']
                rack_stage_list = racknode_item['rack_id__stage'].split(',')
                racknode_ids.append(racknode_item['id'])
                rackhistory_data = {
                    "rack_id": racknode_item['rack_id_id'],
                    "rack_sn": racknode_item['sn'],
                    "current_stage": racknode_item['current_stage'],
                    "operatorid": racknode_item['operator_id'],
                    "teststatus": racknode_item['teststatus'],
                }
                rackhistory_objs.append(RackHistory(**rackhistory_data)) #创建一个RackHistory对象，用于批量创建RackHistory对象。
                componentnode_obj = ComponentNode.objects.filter( #查询ComponentNode表相关的对象，并将其id添加到列表中
                    rackcomponentnode__rack_node_id__id=racknode_item['id']
                ).values()
                for componentnode_item in componentnode_obj:
                    componentnode_ids.append(componentnode_item['id'])
                    if componentnode_item['sn'] == 'NA':
                        continue
                    is_all_pass_verify = TestItemRecord.objects.filter(
                        sn=componentnode_item['sn'], teststatus__in=['2', '4', '5']
                    )
                    if not is_all_pass_verify.exists() and rack_type:
                        print("要删除")
                        # 这个sn的testitemrecord需要保留
                        c_n_sn_all_pass.append(componentnode_item['sn'])
                    component_id = componentnode_item['component_id_id']
                    t_i_r_objs = TestItemRecord.objects.filter(
                        sn=componentnode_item['sn']
                    ).values()
                    for item in t_i_r_objs:
                        t_i_h_r = TestItemHistoryRecord.objects.filter(
                            component_sn=item['sn'], stage=item['stage']
                        )
                        t_i_r_ids.append(item['id'])
                        if not t_i_h_r.exists():
                            t_i_h_r_data = {
                                "rack_sn": rack_sn,
                                "component_id": component_id,
                                "component_sn": item['sn'],
                                "stage": item['stage'],
                                "testitem": item['testitem'],
                                "waittime": item['waittime'],
                                "starttime": item['starttime'],
                                "endtime": item['endtime'],
                                "teststatus": item['teststatus'],
                                "errorcode": item['errorcode'],
                                "errordescription": item['errordescription'],
                                "operatorid": item['operatorid'],
                                "ismanual": item['ismanual'],
                            }
                            obj = TestItemHistoryRecord(**t_i_h_r_data)
                            t_i_h_r_new_data.append(obj)
            # print('testitemrecordhistory',t_i_h_r_new_data)
            # print('componentnode_ids',componentnode_ids)
            # print('rackhistory_objs',rackhistory_objs)
            # print('racknode_ids',racknode_ids)
            # print('racklocation_obj',racklocation_obj)
            # print('t_i_r_ids',t_i_r_ids)

            # return JsonResponse({"code": 400, 'data': 'error', "msg": 'test'})
            try:
                with transaction.atomic(using='l11_test_primary'):
                    # 更改racklocation的racknodeid为None
                    # RackLocation.objects.bulk_update(
                    #     racklocation_obj, ['rack_node_id_id']
                    # )
                    for r_l in racklocation_obj:
                        RackLocation.objects.filter(id=r_l["id"]).update(
                            rack_node_id_id=None
                        )
                    # 更改racknode删除
                    RackNode.objects.filter(id__in=racknode_ids).delete()
                    # 批量创建rackhistory
                    RackHistory.objects.bulk_create(rackhistory_objs)
                    # componentnode 删除
                    ComponentNode.objects.filter(id__in=componentnode_ids).delete()
                    # testitemrecord 删除
                    TestItemRecord.objects.exclude(sn__in=c_n_sn_all_pass).filter(
                        id__in=t_i_r_ids
                    ).delete()
                    # 批量创建test item record history
                    TestItemHistoryRecord.objects.bulk_create(t_i_h_r_new_data)
            except Exception as e:
                print(e)
                return JsonResponse({"code": 400, 'data': 'error', "msg": repr(e)})
            return JsonResponse(
                {
                    "code": 200,
                    'data': 'test(item)record move to history success',
                    "msg": "success",
                }
            )
        else:
            return JsonResponse({"code": 400, 'data': 'error', "msg": form.errors})


class ScanIn(View):
    '''
    form_status: 1:需要删除testrecord,并更新componentnode的当前站别和状态
    2:只需要更新componentnode的当前站别和状态
    '''

    def post(self, request):
        form = ScanInForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            componentnode_id = cleaned_data["componentnode_id"]
            stage = cleaned_data["stage"]
            rack_stage = cleaned_data["rack_stage"]
            rack_stage_list = cleaned_data["rack_stage_list"]
            operator_id = cleaned_data['operator_id']
            sn = cleaned_data["sn"]
            rack_node_id = cleaned_data['rack_node_id']
            c_status = cleaned_data['teststatus']
            rack_sn = cleaned_data['rack_sn']
            is_new = cleaned_data['is_new']

            componentnode_data = {
                "sn": sn,
                'teststatus': c_status,
                "current_stage": stage,
                "operator_id": cleaned_data["operator_id"],
            }
            # if is_next_stage:
            try:
                with transaction.atomic(using='l11_test_primary'):
                    ComponentNode.objects.filter(id=componentnode_id).update(
                        **componentnode_data
                    )
                    componentnode_objs = ComponentNode.objects.filter(
                        rackcomponentnode__rack_node_id=rack_node_id
                    ).values()
                    component_id_l10 = []
                    component_id_notl10 = []
                    for i in componentnode_objs:
                        if Component.objects.get(id=i['component_id_id']).type == 0:
                            component_id_l10.append(i['id'])
                        else:
                            component_id_notl10.append(i['id'])
                    componentnode_l10 = ComponentNode.objects.filter(
                        id__in=component_id_l10
                    ).values()
                    component_not_l10 = ComponentNode.objects.filter(
                        id__in=component_id_notl10
                    ).values()
                    # return JsonResponse({"code": 201, "msg": "test"})
                    component_type_id = ComponentNode.objects.get(
                        id=componentnode_id
                    ).component_id
                    c_stage_list = []
                    c_status_list = []
                    ComponentObject.objects.update_or_create(
                        component_sn=sn,
                        defaults={
                            'component_type_id': component_type_id,
                            'operatorid': operator_id,
                        },
                    )

                    # 获取非L10的componentnode id
                if RackNode.objects.get(id=rack_node_id).type == 0:
                    # 跳站准备数据
                    for c_n_item in componentnode_l10:
                        if c_n_item['id'] == componentnode_id:
                            # 如果是scan in 当前的componentnode id
                            cur_component_stage = (
                                -1
                                if componentnode_data['current_stage'] == 'NA'
                                else rack_stage_list.index(
                                    componentnode_data['current_stage']
                                )
                            )
                            c_status_list.append(c_status)
                        else:
                            cur_component_stage = (
                                -1
                                if c_n_item['current_stage'] == 'NA'
                                else rack_stage_list.index(c_n_item['current_stage'])
                            )
                            c_status_list.append(c_n_item['teststatus'])
                        c_stage_list.append(cur_component_stage)
                    min_stage = min(c_stage_list)
                    # 如果rack只有三个站不会执行下面的if
                    # 如果如果scan in 全部L10都TP pass 且不存在PX站的情况(rack4个站)
                    if (
                        min_stage == 2
                        and len(set(c_status_list)) == 1
                        and ("3" in set(c_status_list))
                        and len(rack_stage_list) != 3
                    ):
                        # 4个站别且TP全pass，到SV站别
                        min_stage += 1
                        # 变换rack的teststatus
                        for c_n_item in component_not_l10:
                            if c_n_item['id'] == componentnode_id:
                                # 如果是scan in 当前的componentnode id
                                c_status_list.append(c_status)
                            else:
                                c_status_list.append(c_n_item['teststatus'])
                    # 如果scan in 全部L10都TP pass 且存在PX站的情况，需要回到SV站(5个站别)
                    elif (
                        min_stage == 4
                        and len(set(c_status_list)) == 1
                        and ("2" in set(c_status_list))
                    ):
                        # min_stage -= 1
                        notl10_status = []  # 用于判断是否SVpass跳站
                        for c_n_item in component_not_l10:
                            if c_n_item['id'] == componentnode_id:
                                # 如果是scan in 当前的componentnode id
                                c_status_list.append(c_status)
                                notl10_status.append(c_status)
                            else:
                                c_status_list.append(c_n_item['teststatus'])
                                notl10_status.append(c_n_item['teststatus'])
                        # SV全pass
                        if len(set(notl10_status)) == 1 and ("3" in set(notl10_status)):
                            pass
                        else:  # SV没有pass
                            min_stage -= 1

                    cur_rack_stage = rack_stage_list.index(rack_stage)
                    # 修改站别
                    if min_stage > cur_rack_stage:
                        count = min_stage - cur_rack_stage
                        # 上传到SFCS
                        for i in range(count):
                            sfcs = Complete(
                                rack_sn,
                                rack_stage_list[cur_rack_stage + i],
                                [],
                                operator_id,
                                "pass",
                            )
                            if sfcs != "OK":
                                raise ValueError('Upload SFCS error')
                        RackNode.objects.filter(id=rack_node_id).update(
                            current_stage=rack_stage_list[min_stage]
                        )
                    # 修改状态
                    temp_status = set(c_status_list)
                    if len(temp_status) == 1 and '3' in temp_status:
                        # All Pass
                        sfcs = Complete(
                            rack_sn,
                            rack_stage_list[-1],
                            [],
                            operator_id,
                            "pass",
                        )
                        if sfcs != "OK":
                            raise ValueError('Upload SFCS error')
                        RackNode.objects.filter(id=rack_node_id).update(
                            teststatus='3', change=0
                        )
                    elif not is_new:
                        RackNode.objects.filter(id=rack_node_id).update(teststatus='2')
                    elif len(temp_status) == 1 and "-1" in temp_status:
                        RackNode.objects.filter(id=rack_node_id).update(teststatus='0')
                    elif '0' in temp_status:
                        # unused
                        temp_status.discard('-1')
                        if len(temp_status) == 1:
                            RackNode.objects.filter(id=rack_node_id).update(
                                teststatus='0'
                            )
                        else:
                            RackNode.objects.filter(id=rack_node_id).update(
                                teststatus='2'
                            )
                    else:
                        RackNode.objects.filter(id=rack_node_id).update(teststatus='2')
                rack_current = RackNode.objects.get(id=rack_node_id)
                rack_current_step = TestStep.objects.filter(
                    rack=rack_current.rack_id.id,
                    current_stage=rack_current.current_stage,
                ).values()[0]
                rack_current_type = rack_current_step['stage_type']
                try:
                    rack_upper_type = TestStep.objects.filter(
                        rack=rack_current.rack_id.id,
                        next_stage=rack_current.current_stage,
                    ).values()[0]['stage_type']
                    if rack_upper_type != rack_current_type:
                        change = 1
                        componentnode_objs.filter(
                            current_stage=rack_current.current_stage,
                            teststatus__in=[0, 1, 2],
                        ).update(change=1)
                    else:
                        change = 0
                except:
                    change = 0
                RackNode.objects.filter(id=rack_node_id).update(change=change)

            except Exception as e:
                logger_api.error(e)
                return JsonResponse({"code": 400, "msg": repr(e)})
            return JsonResponse({"code": 201, "msg": "update success"})
        else:
            return JsonResponse({"code": 400, "msg": form.errors})


class ScanInDeleave(View):
    '''
    解绑rackcomponentnode中的一个，id为componentnode ID
    t:test ; i:item ; r:record ; h:history ;
    r_c_n:rack_component_node
    '''

    def patch(self, request, id, racknodeid):
        component_node_obj = ComponentNode.objects.filter(id=id)
        r_c_n_obj = RackComponentNode.objects.filter(
            rack_node_id=racknodeid, component_node_id=id
        )
        if component_node_obj.exists() and r_c_n_obj.exists():
            component_node_data = component_node_obj.values()[0]
            sn = component_node_data["sn"]
            component_id = component_node_data["component_id_id"]
            if sn == "NA":
                return JsonResponse(
                    {"code": 400, "msg": "component_node is not scanin"}
                )
            else:
                t_i_r_objs = TestItemRecord.objects.filter(sn=sn).values()
                racknode_obj = RackNode.objects.filter(id=racknodeid).values(
                    "sn", "rack_id__stage", "type"
                )[0]
                rack_sn = racknode_obj["sn"]
                rack_type = racknode_obj["type"]
                rack_stage = racknode_obj["rack_id__stage"].split(",")
                # t_i_r_objs_verify = TestItemRecord.objects.filter(
                #     sn=sn, teststatus__in=['2', '4', '5']
                # )
                if ComponentNode.objects.filter(sn=sn).values()[0]['teststatus'] != '3':
                    # 判断是否全pass
                    is_all_pass = False
                else:
                    if rack_type == 1:
                        is_all_pass = True
                    else:
                        return JsonResponse(
                            {"code": 400, "msg": "all pass can't deleave"}
                        )
                # end

                t_i_h_r_new_data = []  # 批量创建testitemrecordhistory
                for item in t_i_r_objs:
                    t_i_h_r = TestItemHistoryRecord.objects.filter(
                        component_sn=item['sn'], stage=item['stage']
                    )
                    if not t_i_h_r.exists():
                        t_i_h_r_data = {
                            "rack_sn": rack_sn,
                            "component_id": component_id,
                            "component_sn": item['sn'],
                            "stage": item['stage'],
                            "testitem": item['testitem'],
                            "waittime": item['waittime'],
                            "starttime": item['starttime'],
                            "endtime": item['endtime'],
                            "teststatus": item['teststatus'],
                            "errorcode": item['errorcode'],
                            "errordescription": item['errordescription'],
                            "operatorid": item['operatorid'],
                            "ismanual": item['ismanual'],
                        }
                        obj = TestItemHistoryRecord(**t_i_h_r_data)
                        t_i_h_r_new_data.append(obj)
                # return JsonResponse({"code": 201, "msg": "test"})
                try:
                    with transaction.atomic(using='l11_test_primary'):
                        component_node_obj.update(
                            sn="NA",
                            current_stage="NA",
                            operator_id="",
                            teststatus='-1',
                            change=0,
                        )
                        TestItemHistoryRecord.objects.bulk_create(t_i_h_r_new_data)
                        if not is_all_pass:
                            TestItemRecord.objects.filter(sn=sn).delete()
                except Exception as e:
                    print(e)
                    logger_api.error(e)
                    return JsonResponse({"code": 400, "msg": repr(e)})

                return JsonResponse({"code": 201, "msg": "update success"})
        else:
            return JsonResponse(
                {
                    "code": 400,
                    "msg": "component_node is not exist or racknode and componetnode is not match",
                }
            )


class GetRackBySn(View):
    def get(self, request):
        '''
        rack_c_n:rack_component_node
        '''
        form = RackSnForm(request.GET)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            racknode = cleaned_data["racknode"]
            racknode_id = racknode['id']
            rack_c_n_obj = RackComponentNode.objects.filter(
                rack_node_id=racknode_id
            ).values(
                'component_node_id',
                'component_node_id__sn',
                'component_node_id__component_id',
            )
            components = []
            for rack_c_n in rack_c_n_obj:
                fields = ["id", "name", 'stage', 'col', 'row', 'is_iperf']
                component_obj = Component.objects.filter(
                    id=rack_c_n["component_node_id__component_id"]
                ).values(*fields)
                component_data = component_obj[0]
                if component_data['is_iperf']:
                    component_data['is_iperf'] = 1
                else:
                    component_data['is_iperf'] = 0
                component_data["componentnode_sn"] = rack_c_n['component_node_id__sn']
                components.append(component_data)
            racknode["components"] = components
            data = {"code": 200, "data": racknode, "msg": "success"}
            return JsonResponse(data)
        else:
            return JsonResponse({"code": 400, "msg": form.errors})


class ScanInList(View):
    def post(self, request):
        datas = json.loads(request.body)

        res = {}
        code = 201
        for item in datas:
            item['list'] = 1
            form = ScanInForm(item)
            if form.is_valid():
                cleaned_data = form.cleaned_data
                componentnode_id = cleaned_data["componentnode_id"]
                stage = cleaned_data["stage"]
                rack_stage = cleaned_data["rack_stage"]
                rack_stage_list = cleaned_data["rack_stage_list"]
                operator_id = cleaned_data['operator_id']
                sn = cleaned_data["sn"]
                rack_node_id = cleaned_data['rack_node_id']
                c_status = cleaned_data['teststatus']
                rack_sn = cleaned_data['rack_sn']
                is_new = cleaned_data['is_new']

                componentnode_data = {
                    "sn": sn,
                    'teststatus': c_status,
                    "current_stage": stage,
                    "operator_id": cleaned_data["operator_id"],
                }
                # if is_next_stage:
                try:
                    with transaction.atomic(using='l11_test_primary'):
                        ComponentNode.objects.filter(id=componentnode_id).update(
                            **componentnode_data
                        )
                        # if is_new:
                        componentnode_objs = ComponentNode.objects.filter(
                            rackcomponentnode__rack_node_id=rack_node_id
                        ).values()
                        component_id_l10 = []
                        component_id_notl10 = []
                        for i in componentnode_objs:
                            if Component.objects.get(id=i['component_id_id']).type == 0:
                                component_id_l10.append(i['id'])
                            else:
                                component_id_notl10.append(i['id'])
                        componentnode_l10 = ComponentNode.objects.filter(
                            id__in=component_id_l10
                        ).values()
                        component_not_l10 = ComponentNode.objects.filter(
                            id__in=component_id_notl10
                        ).values()
                        component_type_id = ComponentNode.objects.get(
                            id=componentnode_id
                        ).component_id
                        c_stage_list = []
                        c_status_list = []
                        ComponentObject.objects.update_or_create(
                            component_sn=sn,
                            defaults={
                                'component_type_id': component_type_id,
                                'operatorid': operator_id,
                            },
                        )

                        # 获取非L10的componentnode id
                        if RackNode.objects.get(id=rack_node_id).type == 0:
                            # 跳站准备数据
                            for c_n_item in componentnode_l10:
                                if c_n_item['id'] == componentnode_id:
                                    # 如果是scan in 当前的componentnode id
                                    cur_component_stage = (
                                        -1
                                        if componentnode_data['current_stage'] == 'NA'
                                        else rack_stage_list.index(
                                            componentnode_data['current_stage']
                                        )
                                    )
                                    c_status_list.append(c_status)
                                else:
                                    cur_component_stage = (
                                        -1
                                        if c_n_item['current_stage'] == 'NA'
                                        else rack_stage_list.index(
                                            c_n_item['current_stage']
                                        )
                                    )
                                    c_status_list.append(c_n_item['teststatus'])
                                c_stage_list.append(cur_component_stage)
                            min_stage = min(c_stage_list)
                            # 如果rack只有三个站不会执行下面的if
                            # 如果如果scan in 全部L10都TP pass 且不存在PX站的情况(rack4个站)
                            if (
                                min_stage == 2
                                and len(set(c_status_list)) == 1
                                and ("3" in set(c_status_list))
                                and len(rack_stage_list) != 3
                            ):
                                # 4个站别且TP全pass，到SV站别
                                min_stage += 1
                                # 变换rack的teststatus
                                for c_n_item in component_not_l10:
                                    if c_n_item['id'] == componentnode_id:
                                        # 如果是scan in 当前的componentnode id
                                        c_status_list.append(c_status)
                                    else:
                                        c_status_list.append(c_n_item['teststatus'])
                            # 如果scan in 全部L10都TP pass 且存在PX站的情况，需要回到SV站(5个站别)
                            elif (
                                min_stage == 4
                                and len(set(c_status_list)) == 1
                                and ("2" in set(c_status_list))
                            ):
                                # min_stage -= 1
                                notl10_status = []  # 用于判断是否SVpass跳站
                                for c_n_item in component_not_l10:
                                    if c_n_item['id'] == componentnode_id:
                                        # 如果是scan in 当前的componentnode id
                                        c_status_list.append(c_status)
                                        notl10_status.append(c_status)
                                    else:
                                        c_status_list.append(c_n_item['teststatus'])
                                        notl10_status.append(c_n_item['teststatus'])
                                # SV全pass
                                if len(set(notl10_status)) == 1 and (
                                    "3" in set(notl10_status)
                                ):
                                    pass
                                else:  # SV没有pass
                                    min_stage -= 1

                            cur_rack_stage = rack_stage_list.index(rack_stage)
                            # 修改站别
                            if min_stage > cur_rack_stage:
                                count = min_stage - cur_rack_stage
                                # 上传到SFCS
                                for i in range(count):
                                    sfcs = Complete(
                                        rack_sn,
                                        rack_stage_list[cur_rack_stage + i],
                                        [],
                                        operator_id,
                                        "pass",
                                    )
                                    if sfcs != "OK":
                                        raise ValueError('Upload SFCS error')
                                RackNode.objects.filter(id=rack_node_id).update(
                                    current_stage=rack_stage_list[min_stage]
                                )
                            # 修改状态
                            temp_status = set(c_status_list)
                            if len(temp_status) == 1 and '3' in temp_status:
                                # All Pass
                                sfcs = Complete(
                                    rack_sn,
                                    rack_stage_list[-1],
                                    [],
                                    operator_id,
                                    "pass",
                                )
                                if sfcs != "OK":
                                    raise ValueError('Upload SFCS error')
                                RackNode.objects.filter(id=rack_node_id).update(
                                    teststatus='3', change=0
                                )
                            elif not is_new:
                                RackNode.objects.filter(id=rack_node_id).update(
                                    teststatus='2'
                                )
                            elif '0' in temp_status:
                                # unused
                                temp_status.discard('-1')
                                if len(temp_status) == 1:
                                    RackNode.objects.filter(id=rack_node_id).update(
                                        teststatus='0'
                                    )
                                else:
                                    RackNode.objects.filter(id=rack_node_id).update(
                                        teststatus='2'
                                    )
                            else:
                                # testing
                                RackNode.objects.filter(id=rack_node_id).update(
                                    teststatus='2'
                                )
                    rack_current = RackNode.objects.get(id=rack_node_id)
                    rack_current_step = TestStep.objects.filter(
                        rack=rack_current.rack_id.id,
                        current_stage=rack_current.current_stage,
                    ).values()[0]
                    rack_current_type = rack_current_step['stage_type']
                    try:
                        rack_upper_type = TestStep.objects.filter(
                            rack=rack_current.rack_id.id,
                            next_stage=rack_current.current_stage,
                        ).values()[0]['stage_type']
                        if rack_upper_type != rack_current_type:
                            change = 1
                            componentnode_objs.filter(
                                current_stage=rack_current.current_stage,
                                teststatus__in=["0", "1", "2"],
                            ).update(change=1)
                        else:
                            change = 0
                    except:
                        change = 0
                    RackNode.objects.filter(id=rack_node_id).update(change=change)

                except Exception as e:
                    logger_api.error(e)
                    return JsonResponse({"code": 400, "msg": repr(e)})
            else:
                return JsonResponse({"code": 400, "msg": form.errors})
        return JsonResponse({"code": 201, "msg": "update success"})
