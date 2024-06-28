from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q

from rack.models import Rack, RackLocation, RackNode, TestStep
from component.models import (
    Component,
    RackComponent,
    ComponentNode,
    RackComponentNode,
)
from testrecord.models import TestItemRecord
from history.models import TestItemHistoryRecord, RackHistory
from public.sfcs import CheckRoute, GetDynamicData
from component.views import get_sn_pn_mo


class RackInfoForm(forms.Form):
    name = forms.CharField(label="name")
    model_name = forms.CharField(label="model_name")
    operator_id = forms.CharField(label="操作员")
    operator_id = forms.CharField(label="操作员")
    stage = forms.CharField(label="站别")
    rack_row = forms.IntegerField(label="rack行数", min_value=1, max_value=20)
    rack_col = forms.IntegerField(label="rack列数", min_value=1, max_value=10)


class RackComponentForm(forms.Form):
    start_row = forms.IntegerField(label="起始行", min_value=1)
    end_row = forms.IntegerField(label="终止行", min_value=1)
    start_col = forms.IntegerField(label="列", min_value=1)
    end_col = forms.IntegerField(label="列", min_value=1)
    rack_id = forms.IntegerField(label="rack", min_value=0)
    component_id = forms.IntegerField(label="component", min_value=0)

    def clean(self):
        start_row = (
            self.cleaned_data["start_row"] if 'start_row' in self.cleaned_data else None
        )
        end_row = (
            self.cleaned_data["end_row"] if 'end_row' in self.cleaned_data else None
        )
        start_col = (
            self.cleaned_data["start_col"] if 'start_col' in self.cleaned_data else None
        )
        end_col = (
            self.cleaned_data["end_col"] if 'end_col' in self.cleaned_data else None
        )
        rack_id = (
            self.cleaned_data["rack_id"] if 'rack_id' in self.cleaned_data else None
        )
        component_id = (
            self.cleaned_data["component_id"]
            if 'component_id' in self.cleaned_data
            else None
        )
        rack_obj = Rack.objects.filter(id=rack_id)
        component_obj = Component.objects.filter(id=component_id)
        if (
            start_row
            and end_row
            and start_col
            and end_col
            and rack_obj.exists()
            and component_obj.exists()
        ):
            # start 判断rack stage是否和component stage 一致，只有component为L10才需要判断
            c_data = component_obj.values()[0]
            if not c_data["type"]:
                c_stage = c_data["stage"]
                # 获取rackL10的的站别,t_s_l——stage:Rack为L10的站别
                t_s_l_stage = TestStep.objects.filter(
                    rack=rack_id, stage_type=0
                ).values('current_stage')
                for item in t_s_l_stage:
                    if item['current_stage'] not in c_stage:
                        raise ValidationError(
                            "component and rack stage is inconformity"
                        )
            else:
                c_stage = c_data["stage"]
                # 获取rack非L10的的站别,t_s_l——stage:Rack为非L10的站别
                t_s_l_stage = TestStep.objects.filter(
                    rack=rack_id, stage_type=1
                ).values('current_stage')
                if not t_s_l_stage.exists():
                    raise ValidationError(
                        "component can't scanin,rack don't component stage"
                    )
                for item in t_s_l_stage:
                    if item['current_stage'] not in c_stage:
                        raise ValidationError(
                            "component and rack stage is inconformity"
                        )
            # end
            rack_row, rack_col = rack_obj.values('rack_row', 'rack_col')[0].values()
            component_row, component_col = component_obj.values('row', 'col')[
                0
            ].values()
            if (
                start_row + component_row - 1 != end_row
                or start_col + component_col - 1 != end_col
                or end_row > rack_row
                or end_col > rack_col
            ):
                raise ValidationError("this position is not valid")
            postion_verify = RackComponent.objects.filter(
                Q(rack_id=rack_id),
                Q(start_row__range=(start_row, end_row))
                | Q(end_row__range=(start_row, end_row)),
                Q(start_col__range=(start_col, end_col))
                | Q(end_col__range=(start_col, end_col)),
            )
            if postion_verify.exists():
                raise ValidationError("this position is not allow")  # django校验异常
            else:
                self.cleaned_data["rack_id"] = rack_obj[0]
                self.cleaned_data["component_id"] = component_obj[0]
                return self.cleaned_data
        else:
            raise ValidationError(
                "start_row,end_row,start_col,end_col is require or rack,component,sn is not exist "
            )  # django校验异常


class RackLocationForm(forms.Form):
    area_id = forms.IntegerField(label='区域id', required=True)
    coordinateX = forms.IntegerField(label='第几行', required=True)
    coordinateY = forms.IntegerField(label='第几列', required=True)

    def clean(self):
        area_id = (
            self.cleaned_data["area_id"] if 'area_id' in self.cleaned_data else None
        )
        coordinateX = (
            self.cleaned_data["coordinateX"]
            if 'coordinateX' in self.cleaned_data
            else -1
        )
        coordinateY = (
            self.cleaned_data["coordinateY"]
            if 'coordinateY' in self.cleaned_data
            else -1
        )
        if coordinateX < 0 or coordinateY < 0:
            return False
        racklocation_lis = RackLocation.objects.filter(
            coordinateX=coordinateX, coordinateY=coordinateY, area_id=area_id
        )
        if racklocation_lis.exists():
            raise ValidationError("this racklocation is exist")  # django校验异常
        return self.cleaned_data


class RackLocationCheckinForm(forms.Form):
    racklocation_id = forms.IntegerField(label="racklocation id")
    sn = forms.CharField(label="rack_node sn", max_length=50)
    operator_id = forms.CharField(label="rack operator_id", max_length=50)
    rack_id = forms.IntegerField(label="rack id")
    type = forms.IntegerField(label="是否为备品库")

    def clean(self):
        racklocation_id = (
            self.cleaned_data["racklocation_id"]
            if 'racklocation_id' in self.cleaned_data
            else None
        )
        rack_id = (
            self.cleaned_data["rack_id"] if 'rack_id' in self.cleaned_data else None
        )
        type = self.cleaned_data["type"] if 'type' in self.cleaned_data else None
        sn = self.cleaned_data.get('sn')
        rack_node_obj_verify = RackNode.objects.filter(sn=sn)
        rack_history_obj_verify = RackHistory.objects.filter(rack_sn=sn, teststatus='3')
        if rack_node_obj_verify.exists() or rack_history_obj_verify:
            raise ValidationError("sn %s is exist!" % sn)
        racklocation_obj = RackLocation.objects.filter(id=racklocation_id)
        rack_obj = Rack.objects.filter(id=rack_id)
        if racklocation_obj.exists() and rack_obj.exists():
            # start 验证正确stage
            rack_stage = rack_obj.values()[0]['stage']
            rack_stage_list = rack_stage.split(",")
            if type:
                if not len(rack_stage_list) == 3:
                    raise ValidationError("this rack is not allow spare")
            for stage_i in rack_stage.split(","):
                res_sfcs = CheckRoute(sn, stage_i)
                if res_sfcs['state'] == 2:
                    self.cleaned_data["stage"] = stage_i
                    break
                elif res_sfcs['state'] in (-1, 0):
                    raise ValidationError(res_sfcs['msg'])
            else:
                raise ValidationError("stage error")
            # ending
            if racklocation_obj.values()[0]["rack_node_id_id"]:
                raise ValidationError("this racklocation is binded rack")
            self.cleaned_data["rack_obj"] = rack_obj[0]
            return self.cleaned_data
        else:
            raise ValidationError("racklocation or rack is not exist")


class RackLocationDeleaveForm(forms.Form):
    id = forms.IntegerField(label="racklocation id")

    def clean(self):
        '''
        t_r: testrecord
        r_c_n: rack_component_node
        t_i_r:test item record
        '''
        id = self.cleaned_data["id"] if 'id' in self.cleaned_data else None
        racklocation_obj = RackLocation.objects.filter(id=id, isvalid=True).values()
        if racklocation_obj.exists():
            rack_node_id = racklocation_obj.values()[0]["rack_node_id_id"]
            rack_node_obj = RackNode.objects.filter(id=rack_node_id)
            self.error = 0
            r_c_n_objs = RackComponentNode.objects.filter(
                rack_node_id=rack_node_id
            ).values()
            self.cleaned_data["racklocation_obj"] = racklocation_obj
            self.cleaned_data["rack_node_obj"] = rack_node_obj
            self.cleaned_data["r_c_n_objs"] = r_c_n_objs
            return self.cleaned_data
        else:
            raise ValidationError("racklocation is not exist")


class RackLocationDeleaveMoreForm(forms.Form):
    racklocation_id = forms.CharField(label="racklocation_id", required=False)
    is_pass = forms.CharField(label='是否解绑全部pass', required=False)

    def clean_racklocation_id(self):
        r_l_id = self.cleaned_data['racklocation_id']
        return r_l_id if r_l_id else '0'

    def clean_is_pass(self):
        is_pass = self.cleaned_data['is_pass']
        return is_pass if is_pass else '0'

    def clean(self):
        racklocation_id = self.cleaned_data.get('racklocation_id')
        is_pass = self.cleaned_data.get('is_pass')
        if is_pass == '1':
            racknode_objs = RackNode.objects.filter(teststatus='3').values(
                'rack_id_id', 'current_stage', 'rack_id__stage', 'racklocation__id'
            )
            racklocation_id_list = []
            for racknode_item in racknode_objs:
                cur_stage = racknode_item['current_stage']
                stage = racknode_item['rack_id__stage'].split(',')
                if cur_stage == stage[-1]:
                    racklocation_id_list.append(racknode_item['racklocation__id'])
            racklocation_objs = RackLocation.objects.filter(
                id__in=racklocation_id_list
            ).values()
        else:
            if racklocation_id != '0':
                racklocation_id_list = racklocation_id.split(",")
                racklocation_objs = RackLocation.objects.filter(
                    id__in=racklocation_id_list, rack_node_id_id__isnull=False
                ).values()
            else:
                racklocation_objs = RackLocation.objects.filter(
                    rack_node_id_id__isnull=False
                ).values()
        racknode_objs = []
        for r_l_item in racklocation_objs:
            racknode_fields = [
                'id',
                'sn',
                'current_stage',
                'operator_id',
                'teststatus',
                'rack_id_id',
                'rack_id__stage',
                'type',
            ]
            # rackcomponentnode__component_node_id__sn
            racknode_obj = RackNode.objects.filter(
                id=r_l_item['rack_node_id_id']
            ).values(*racknode_fields)[0]
            racknode_objs.append(racknode_obj)
        self.cleaned_data['racklocation_objs'] = racklocation_objs
        self.cleaned_data['racknode_objs'] = racknode_objs
        return self.cleaned_data


class ScanInForm(forms.Form):
    sn = forms.CharField(label="component sn")
    operator_id = forms.CharField(label="操作员")
    rack_component_node_id = forms.IntegerField(label="rackcomponentnode", min_value=1)
    rack_node_id = forms.IntegerField(label="racknode", min_value=1)

    def clean(self):
        rack_component_node_id = (
            self.cleaned_data["rack_component_node_id"]
            if 'rack_component_node_id' in self.cleaned_data
            else None
        )
        rack_node_id = (
            self.cleaned_data["rack_node_id"]
            if 'rack_node_id' in self.cleaned_data
            else None
        )
        sn = self.cleaned_data["sn"] if 'sn' in self.cleaned_data else None
        rackcomponentnode_obj = RackComponentNode.objects.filter(
            id=rack_component_node_id
        )
        try:
            component_type = ComponentNode.objects.get(
                id=rackcomponentnode_obj.values()[0]['component_node_id_id']
            ).component_id.type
        except Exception as e:
            raise ValidationError(e)
        racknode_obj = RackNode.objects.filter(id=rack_node_id)
        if (
            rackcomponentnode_obj.exists()
            and racknode_obj.exists()
            and rackcomponentnode_obj.values()[0]['rack_node_id_id'] == rack_node_id
        ):
            # 准备数据
            racknode_data = racknode_obj.values()[0]
            cur_stage = racknode_data["current_stage"]
            rack_id = racknode_data["rack_id_id"]
            rack_sn = racknode_data["sn"]
            componentnode_id = rackcomponentnode_obj.values("component_node_id")[0][
                "component_node_id"
            ]
            componentnode_obj = ComponentNode.objects.filter(
                id=componentnode_id
            ).values("component_id__model")
            component_model = componentnode_obj[0]["component_id__model"]
            rack_obj = Rack.objects.filter(id=rack_id)
            rack_stage_list = rack_obj.values()[0]['stage'].split(",")

            # 开始校验sfcs中的modelname
            isverify_data = GetDynamicData(sn)
            isverify = False
            if isinstance(isverify_data, dict):
                if isverify_data['model'] == component_model:
                    isverify = True
            else:
                raise ValidationError("%s" % isverify_data)
            if not isverify:
                raise ValidationError("This sn %s doesn't match" % sn)
            # end

            # start校验是否已经scanin
            component_node_verify = ComponentNode.objects.filter(sn=sn)
            if component_node_verify.exists():
                raise ValidationError("this sn %s is exist" % sn)
            # end

            # start校验是否有当前测试记录，排除1
            t_i_r_objs_verify = TestItemRecord.objects.filter(sn=sn).exclude(
                teststatus='3'
            )
            t_i_r_objs = TestItemRecord.objects.filter(sn=sn).order_by('-createtime')
            self.cleaned_data["stage"] = ''
            if t_i_r_objs_verify.exists():
                # if not is_pass:
                raise ValidationError("this sn %s is not all pass" % (sn))

            else:
                self.cleaned_data["teststatus"] = '3'
                t_i_h_r_objs_verify = TestItemRecord.objects.filter(sn=sn)
                if t_i_h_r_objs_verify.exists():  # test item record有且全pass的状态
                    c_stage = t_i_r_objs.values()[0]["stage"]
                    c_type_stage = ComponentNode.objects.get(
                        id=componentnode_id
                    ).component_id.stage.split(',')
                    if c_stage == c_type_stage[-1]:
                        self.cleaned_data["stage"] = c_stage
                        self.cleaned_data["teststatus"] = '3'
                    else:
                        if len(rack_stage_list) == 5:
                            self.cleaned_data["stage"] = c_type_stage[
                                c_type_stage.index(c_stage) + 1
                            ]
                            self.cleaned_data["teststatus"] = '2'
                        else:
                            self.cleaned_data["stage"] = c_stage
                            self.cleaned_data["teststatus"] = '3'
                    self.cleaned_data["is_new"] = False
                else:
                    # 空白SN
                    if RackNode.objects.get(id=rack_node_id).type == 0:
                        try:
                            scanin_list = self.cleaned_data["list"]
                        except:
                            scanin_list = 0
                        if scanin_list == 1:
                            pass
                        elif (
                            RackNode.objects.filter(id=rack_node_id).values()[0][
                                'teststatus'
                            ]
                            == '2'
                        ):
                            raise ValidationError("This rack is not in unused")
                    if component_type == 0:  # L10
                        if cur_stage == rack_stage_list[0]:
                            self.cleaned_data["stage"] = cur_stage
                            self.cleaned_data["teststatus"] = '0'
                    else:  # 非L10
                        component_stage = ComponentNode.objects.get(
                            id=rackcomponentnode_obj.values()[0]['component_node_id_id']
                        ).component_id.stage.split(',')[0]
                        self.cleaned_data['stage'] = component_stage
                        self.cleaned_data["teststatus"] = '0'
                    self.cleaned_data["is_new"] = True
            if not self.cleaned_data["stage"]:
                raise ValidationError("stage error")
            self.cleaned_data["rack_stage"] = cur_stage
            self.cleaned_data["rack_stage_list"] = rack_stage_list
            self.cleaned_data["componentnode_id"] = componentnode_id
            self.cleaned_data["rack_sn"] = rack_sn
            self.cleaned_data["component_type"] = component_type
            return self.cleaned_data
        else:
            raise ValidationError(
                "rackcomponentnode or racknode is not exist or don't match"
            )


class RackSnForm(forms.Form):
    sn = forms.CharField(label="rack sn")

    def clean(self):
        sn = self.cleaned_data["sn"] if 'sn' in self.cleaned_data else None
        racknode_obj = RackNode.objects.filter(sn=sn)
        if racknode_obj.exists():
            fields = [
                'id',
                'sn',
                'current_stage',
                'operator_id',
                'rack_id__name',
                'rack_id__stage',
            ]
            racknode_data = racknode_obj.values(*fields)[0]
            self.cleaned_data["racknode"] = racknode_data
            return self.cleaned_data
        else:
            raise ValidationError("this sn is not racknode")
