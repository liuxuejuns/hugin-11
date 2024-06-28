import logging

from django.http import JsonResponse
from django.views import View
from django.http.request import QueryDict
from django.db import transaction

from area.models import Area
from area.form import AreaForm
from rack.models import RackLocation

# Create your views here.
logger_api = logging.getLogger('api')
logger_default = logging.getLogger('default')
logger_debug = logging.getLogger('debug')

class AreaList(View):

    def get(self,request):
        '''
            获取所有area
        '''
        fields = ['id','area','floor','current_count']  # 需要返回的字段
        area_list = Area.objects.all().values(*fields)
        data = {
            "code":200,
            "data":[data for data in area_list],
            "msg":"success"
        }
        return JsonResponse(data,status=200)


class CreateArea(View):

    def post(self,request):
        '''
            添加area
        '''
        form = AreaForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            racklocatin_suffix = ''
            area_data = {
                "area": cleaned_data["area"],
                "floor":cleaned_data["floor"],
                "current_count":cleaned_data["current_count"],
            }
            try:
                with transaction.atomic(using='l11_test_primary'):
                    area = Area.objects.create(**area_data)
                    x = 0
                    y = 0
                    coordinate = {}
                    col = []
                    for count in [x for x in range(0, int(cleaned_data["current_count"]))]:
                        col.append(y)
                        if cleaned_data['is_int'] == "1":
                            racklocatin_suffix = chr(65+count)
                        else:
                            racklocatin_suffix = str(count + 1)
                        rack_location = cleaned_data['racklocation_prefix'] + "-" + racklocatin_suffix
                        # Insert test area to TestArea table
                        index = x*3+y
                        new_rack_location = RackLocation.objects.create(
                                                                    area_id=area,
                                                                    name = rack_location,
                                                                    coordinateX=x,
                                                                    coordinateY=y,
                                                                    index=index,
                                                                    isvalid=True
                                                                )
                        # 列加1
                        y += 1 
                        # 當列達到6時，換行
                        if y > 2:
                            coordinate[x] = col
                            x += 1
                            y = 0
            except Exception as e:
                logger_api.error(e)
                return JsonResponse({"code":400,"msg":repr(e)})
            # rack_location_format = request.POST.get('rack_location_format', 'Rack-')
             # initial rack location table if rack location count > 0
            
            return JsonResponse({"code":201,"msg":"add area success"})
        else:
            # print(form.errors.get_json_data)
            return JsonResponse({"code":400,"msg":form.errors})


class AreaInfo(View):

    def get(self,request,id):
        '''
            获取单个area
        '''
        if id:
            fields = ['id','area','floor','current_count']  # 需要返回的字段
            area_list = Area.objects.filter(id=id).values(*fields)
            data = {
                "code":200,
                "data":[data for data in area_list],
                "msg":"success"
            }
            return JsonResponse(data,status=200)
        else:
            return JsonResponse({"code":400,"msg":"area id is fail"})
    
    def patch(self,request,id):
        '''
            修改area信息
        '''
        if id:
            area_lis = Area.objects.filter(id=id)
            if area_lis.exists():
                patch_data = QueryDict(request.body)
                area = patch_data.get('area',None)
                floor = patch_data.get('floor',None)
                condition = {}
                condition["area"] = area if area else area_lis.values()[0]["area"]
                condition["floor"] = floor if floor else area_lis.values()[0]["floor"]
                area_list = Area.objects.filter(**condition)
                if len(area_list):
                    return JsonResponse({"code":400,"msg":"this area is exist"})  #django校验异常
                else:
                    Area.objects.filter(id=id).update(**condition)
                    return JsonResponse({"code":201,"msg":"update success"})
            else:
                return JsonResponse({"code":404,"msg":"area not exist"})
        else:
            return JsonResponse({"code":400,"msg":"area id is null"})

    def delete(self,request,id):
        '''
            根据ID删除area
        '''
        if id:
            area = Area.objects.filter(id=id)
            rackloc = RackLocation.objects.filter(area_id=id,rack_node_id__isnull=False)
            if area.exists():
                if rackloc.exists():
                    return JsonResponse({"code":400,"msg":"can't delete,this area have racklocation and racklocation isbind rack"})
                else:
                    area.delete()
                    return JsonResponse({"code":204,"msg":"del success"})
            else:
                return JsonResponse({"code":404,"msg":"area not exist"})
        else:
            return JsonResponse({"code":400,"msg":"area id is null"})
        




