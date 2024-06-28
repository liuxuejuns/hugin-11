import re

from errno import errorcode
from telnetlib import STATUS
from django import forms
from django.core.exceptions import ValidationError

from rack.models import RackNode, TestStep, Rack
from component.models import ComponentNode, RackComponentNode, Component
from testrecord.models import TestItemRecord, ComponentObject


class BuildTestForm(forms.Form):
    sn = forms.CharField(label="sn", max_length=50, required=False)
    log_path = forms.CharField(label="log_path", max_length=250, required=False)
    bmcip = forms.GenericIPAddressField(label="bmcip", required=False)
    ethernetip = forms.GenericIPAddressField(label="ethernetip", required=False)

    def clean_log_path(self):
        log_path = self.cleaned_data['log_path']
        if not log_path:
            raise ValidationError('Please input log_path')
        return self.cleaned_data['log_path']

    def clean(self):
        sn = self.cleaned_data['sn']
        if not sn:
            raise ValidationError('please input sn')
        try:
            component_node_obj = ComponentNode.objects.get(sn=sn)
        except:
            raise ValidationError('Can not found this sn in componentnode')
        racknode_id = RackComponentNode.objects.filter(
            component_node_id=component_node_obj.id
        ).values()[0]['rack_node_id_id']
        current_stage = component_node_obj.current_stage
        try:
            component_type = ComponentNode.objects.get(id=component_node_obj.id)
        except Exception as e:
            raise ValidationError(e)
        if len(TestItemRecord.objects.filter(sn=sn, stage=current_stage)) >= 1:
            raise ValidationError('This sn already build')
        if not racknode_id:
            raise ValidationError('Can not found this sn')
        if (
            component_node_obj.current_stage
            != RackNode.objects.get(id=racknode_id).current_stage
        ):
            raise ValidationError('This rack stage not in current stage')
        self.cleaned_data['racknode_id'] = racknode_id
        self.cleaned_data['current_stage'] = current_stage
        self.cleaned_data['component_type_id'] = component_type.component_id
        self.cleaned_data['operatorid'] = component_node_obj.operator_id
        return self.cleaned_data


class NextStageForm(forms.Form):
    sn = forms.CharField(label="rack_sn", max_length=50, required=False)

    def clean(self):
        component_sn = self.cleaned_data['sn']
        if not component_sn:
            raise ValidationError('please input sn')
        try:
            componentnode_obj = ComponentNode.objects.get(sn=component_sn)
        except:
            raise ValidationError('Can not found this sn in componentnode')
        component_id = componentnode_obj.component_id
        if (
            len(
                TestItemRecord.objects.filter(
                    sn=component_sn,
                    stage=componentnode_obj.current_stage,
                    teststatus__in=['2', '4', '5'],
                )
            )
            >= 1
        ):
            raise ValidationError('This stage has no finish test item record')
        if (
            len(
                TestItemRecord.objects.filter(
                    sn=component_sn,
                    stage=componentnode_obj.current_stage,
                    teststatus='3',
                )
            )
            < 1
        ):
            raise ValidationError('This stage has no pass test item record')
        racknode_id = RackComponentNode.objects.filter(
            component_node_id=componentnode_obj.id
        ).values()[0]['rack_node_id_id']
        rack_id = RackNode.objects.get(id=racknode_id).rack_id.id
        component_type = componentnode_obj.component_id.type
        component_stage = componentnode_obj.component_id.stage.split(',')
        component_stage.append('-1')
        rack_stage = RackNode.objects.get(id=racknode_id).rack_id.stage.split(',')
        rack_stage.append('-1')
        # 非L10站别
        if component_type == 1:
            if len(rack_stage) != 4:
                next_index = component_stage.index(componentnode_obj.current_stage) + 1
                next_stage = component_stage[next_index]
            else:
                next_stage = "-1"
        # L10
        else:
            if RackNode.objects.get(id=racknode_id).type == 0:
                if len(component_stage) < len(rack_stage):
                    next_index = (
                        component_stage.index(componentnode_obj.current_stage) + 1
                    )
                    next_stage = component_stage[next_index]
                else:
                    next_index = rack_stage.index(componentnode_obj.current_stage) + 1
                    try:
                        step_obj = TestStep.objects.get(
                            current_stage=rack_stage[next_index], rack=rack_id
                        )
                        if step_obj.stage_type == 1:
                            next_stage = step_obj.next_stage
                        else:
                            next_stage = rack_stage[next_index]
                    except:
                        next_stage = rack_stage[next_index]
            else:
                next_index = rack_stage.index(componentnode_obj.current_stage) + 1
                next_stage = rack_stage[next_index]
        stage = Rack.objects.filter(id=rack_id).values()[0]['stage']
        all_stage = stage.split(',')
        all_stage.insert(0, "NA")
        component_node_id = []
        component_node_mb = []
        racknode_list = RackComponentNode.objects.filter(
            rack_node_id=racknode_id
        ).values('component_node_id_id')
        for i in racknode_list:
            component_node_id.append(i['component_node_id_id'])
        for k in component_node_id:
            if ComponentNode.objects.get(id=k).component_id.type == 1:
                component_node_id.remove(k)
                component_node_mb.append(k)

        # 变更racknode的change
        current_step = TestStep.objects.get(
            current_stage=RackNode.objects.get(id=racknode_id).current_stage,
            rack=rack_id,
        )
        try:
            next_step_type = TestStep.objects.get(
                current_stage=current_step.next_stage, rack=rack_id
            ).stage_type
        except:
            next_step_type = -1
        if RackNode.objects.get(id=racknode_id).type == 0:
            if RackNode.objects.get(id=racknode_id).current_stage == all_stage[-1]:
                self.cleaned_data['change'] = 0
            elif next_step_type != -1:
                if current_step.stage_type != next_step_type:
                    self.cleaned_data['change'] = 1
                else:
                    self.cleaned_data['change'] = 0
            else:
                self.cleaned_data['change'] = 0
        else:
            self.cleaned_data['change'] = 0

        self.cleaned_data['next_stage'] = next_stage
        self.cleaned_data['racknode_id'] = racknode_id
        self.cleaned_data['component_node_id'] = component_node_id
        self.cleaned_data['component_node_mb'] = component_node_mb
        self.cleaned_data['all_stage'] = all_stage
        self.cleaned_data['component_id'] = component_id
        self.cleaned_data['component_type'] = componentnode_obj.component_id.type
        return self.cleaned_data


class StartTestItemRecord(forms.Form):
    sn = forms.CharField(label="component_sn", max_length=50, required=False)
    testitem = forms.CharField(label="testitem", max_length=50, required=False)
    is_manual = forms.CharField(label="is_manual", max_length=20, required=False)
    stage = forms.CharField(label="stage", max_length=50, required=False)
    machine_name = forms.CharField(label="machine_name", max_length=100, required=False)

    def clean_is_manual(self):
        is_manual = self.cleaned_data['is_manual']
        if (not is_manual) or (is_manual == "1") or (is_manual.upper() == 'TRUE'):
            manual = True
        else:
            manual = False
        self.cleaned_data['is_manual'] = manual
        return self.cleaned_data['is_manual']

    def clean(self):
        component_sn = self.cleaned_data['sn']
        testitem = self.cleaned_data['testitem']
        stage = self.cleaned_data['stage']
        machine_name = self.cleaned_data['machine_name']
        if not component_sn:
            raise ValidationError('Please input sn')
        if not testitem:
            raise ValidationError('Please input testitem')
        else:
            if re.match('Cross.+', testitem):
                if not machine_name:
                    raise ValidationError('Cross test item need machine_name')
        if (
            len(
                ComponentNode.objects.filter(
                    sn=component_sn, is_valid=True, teststatus__in=['4', '5']
                )
            )
            >= 1
        ):
            raise ValidationError(
                'Please check sn or component status,it may be have fail or timeout'
            )
        try:
            componentnode_obj = ComponentNode.objects.get(
                sn=component_sn, is_valid=True
            )
        except:
            raise ValidationError(
                'Can not start this sn, please check sn or component status'
            )
        component_stage = componentnode_obj.current_stage
        try:
            TestItemRecord.objects.filter(sn=component_sn,).values()[
                0
            ]['stage']
        except:
            raise ValidationError('No Test item record about this sn')
        if component_stage != stage:
            raise ValidationError(
                'Testitemrecord stage is not in component current stage'
            )
        racknode_id = RackComponentNode.objects.filter(
            component_node_id=componentnode_obj.id,
        ).values()[0]['rack_node_id_id']
        if not racknode_id:
            raise ValidationError('Can not found the rack to this component')
        if RackNode.objects.get(id=racknode_id).change == 1:
            if RackNode.objects.get(id=racknode_id).current_stage != stage:
                raise ValidationError('This stage not in rack current stage')
        try:
            rack_stage_list = RackNode.objects.get(id=racknode_id).rack_id.stage.split(
                ','
            )
        except:
            rack_stage_list = []
        if len(rack_stage_list) == 5 and component_stage == rack_stage_list[-1]:
            if component_stage != RackNode.objects.get(id=racknode_id).current_stage:
                raise ValidationError(
                    'This component stage needs to wait for rack stage in the same '
                )

        testitemrecord_obj = TestItemRecord.objects.filter(
            sn=component_sn, isvalid=True
        ).latest('createtime')
        if (
            len(
                TestItemRecord.objects.filter(
                    sn=component_sn,
                    testitem=testitem,
                )
            )
            >= 1
        ):
            raise ValidationError('This SN and testitem combination already existed')
        if not testitemrecord_obj:
            raise ValidationError('Can not found test item record for this sn')
        if testitemrecord_obj.teststatus != "1":
            raise ValidationError('This test item record is not in pending status')

        self.cleaned_data['current_stage'] = component_stage
        self.cleaned_data['racknode_id'] = racknode_id
        self.cleaned_data['operatorid'] = componentnode_obj.operator_id
        self.cleaned_data['testitemrecord_id'] = testitemrecord_obj.id

        return self.cleaned_data


class EndTestItemRecord(forms.Form):
    sn = forms.CharField(label="component_sn", max_length=50, required=False)
    errorcode = forms.CharField(label="stage", max_length=100, required=False)
    errordescription = forms.CharField(
        label="errordescription", max_length=1024, required=False
    )
    teststatus = forms.CharField(label="teststatus", max_length=10, required=False)
    testitem = forms.CharField(label="testitem", max_length=50, required=False)
    machine_name = forms.CharField(label="machine_name", max_length=100, required=False)

    def clean_testitem(self):
        testitem = self.cleaned_data['testitem']
        if not testitem:
            raise ValidationError('Please input testitem')
        return self.cleaned_data['testitem']

    def clean_teststatus(self):
        teststatus = self.cleaned_data['teststatus']
        if not teststatus:
            raise ValidationError('Please input teststatus')
        if teststatus.upper() == 'PASS':
            teststatus = "3"
        elif teststatus.upper() == 'FAIL':
            teststatus = "4"
        elif teststatus.upper() == 'TIMEOUT':
            teststatus = "5"
        if teststatus == "4" or teststatus == "5":
            errorcode = self.cleaned_data['errorcode']
            if not errorcode:
                raise ValidationError('Please input errorcode')
        self.cleaned_data['teststatus'] = teststatus
        return self.cleaned_data['teststatus']

    def clean(self):
        testitem = self.cleaned_data['testitem']
        machine_name = self.cleaned_data['machine_name']
        if self.errors:
            raise ValidationError(self.errors)
        self.has_error('teststatus'),
        self.has_error('testitem'),
        if re.match('Cross.+', testitem):
            if not machine_name:
                raise ValidationError('Cross test item need machine_name')
        component_sn = self.cleaned_data['sn']
        teststatus = self.cleaned_data['teststatus']
        testitem = self.cleaned_data['testitem']
        if not component_sn:
            raise ValidationError('Please input sn')
        if not testitem:
            raise ValidationError('Please input testitem')
        if not teststatus:
            raise ValidationError('Please input teststatus')
        try:
            componentnode_obj = ComponentNode.objects.get(
                sn=component_sn, is_valid=True
            )
        except Exception:
            raise ValidationError('Can not found component for this sn')
        try:
            testitemrecord_obj = TestItemRecord.objects.get(
                sn=component_sn,
                testitem=testitem,
                stage=componentnode_obj.current_stage,
            )
        except:
            raise ValidationError('Can not found this sn and testitem data')
        # racknode_id = RackComponentNode.objects.filter(
        #     component_node_id=componentnode_obj.id
        # ).values()[0]['rack_node_id_id']
        # rack_id = RackNode.objects.get(id=racknode_id).rack_id.id
        # next_stage = TestStep.objects.filter(
        #     current_stage=componentnode_obj.current_stage, rack=rack_id
        # ).values()[0]['next_stage']
        if not testitemrecord_obj.teststatus == "2":
            raise ValidationError('This test item is not in testing status')
        if teststatus not in ["3", "4", "5"]:
            raise ValidationError('Please input teststatus in pass/fail/timeout')
        self.cleaned_data['componentnode_obj'] = componentnode_obj
        # self.cleaned_data['next_stage'] = next_stage
        return self.cleaned_data


class ModifyForm(forms.Form):
    sn = forms.CharField(label="sn", max_length=50, required=False)
    bmcip = forms.GenericIPAddressField(label="bmcip", required=False)
    ethernetip = forms.GenericIPAddressField(label="ethernetip", required=False)

    def clean_sn(self):
        sn = self.cleaned_data['sn']
        if not sn:
            raise ValidationError('Please input sn')
        return self.cleaned_data['sn']

    def clean(self):
        sn = self.cleaned_data['sn']
        if self.errors:
            raise ValidationError(self.errors)
        self.has_error('sn'),
        try:
            component_obj = ComponentObject.objects.get(component_sn=sn)
        except:
            raise ValidationError('Can not found this sn data')
        bmcip = component_obj.bmcip
        ethernetip = component_obj.ethernetip
        if self.cleaned_data['bmcip'] == '':
            self.cleaned_data['bmcip'] = bmcip
        if self.cleaned_data['ethernetip'] == '':
            self.cleaned_data['ethernetip'] = ethernetip
        return self.cleaned_data
