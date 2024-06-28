from django import forms
from django.core.exceptions import ValidationError

# from component.models import Component


class ComponentForm(forms.Form):
    name = forms.CharField(label='component name')
    test_plan = forms.CharField(label='测试计划')
    stage = forms.CharField(label="站别")
    col = forms.IntegerField(label="占用的列数",min_value=1,max_value=5)
    row = forms.IntegerField(label="占用的行数",min_value=1,max_value=5)


class ComponentAllForm(forms.Form):
    name = forms.CharField(label='name')
    model = forms.CharField(label='model name')
    sn = forms.CharField(label="sn",required=False)
    pn = forms.CharField(label="pn",required=False)
    mo = forms.CharField(label="mo",required=False)
    test_plan = forms.CharField(label='测试计划')
    stage = forms.CharField(label="站别")
    col = forms.IntegerField(label="占用的列数",min_value=1,max_value=5)
    row = forms.IntegerField(label="占用的行数",min_value=1,max_value=5)
    type = forms.ChoiceField(label="component类型",choices=((0,0),(1,1)))
    is_iperf = forms.IntegerField(label="是否需要iperf测试",required=False,initial=0)

    # def clean(self):
    #     sn = self.cleaned_data["sn"] if 'sn' in self.cleaned_data else None
    #     pn = self.cleaned_data["pn"] if 'pn' in self.cleaned_data else None
    #     mo = self.cleaned_data["mo"] if 'mo' in self.cleaned_data else None
    #     if not sn and not pn and not mo:
    #         raise ValidationError("one of the sn,pn,mo is required")
    #     else:
    #         return self.cleaned_data 


class GetComponentForm(forms.Form):
    sn = forms.CharField(label="sn",required=False)
    pn = forms.CharField(label="pn",required=False)
    mo = forms.CharField(label="mo",required=False)

    def clean(self):
        sn = self.cleaned_data["sn"] if 'sn' in self.cleaned_data else None
        pn = self.cleaned_data["pn"] if 'pn' in self.cleaned_data else None
        mo = self.cleaned_data["mo"] if 'mo' in self.cleaned_data else None
        if not sn and not pn and not mo:
            raise ValidationError("input is empty")
        else:
            return self.cleaned_data  


class SnForm(forms.Form):
    sn = forms.CharField(label="sn")


class PnForm(forms.Form):
    pn = forms.CharField(label="pn")


class MoForm(forms.Form):
    mo = forms.CharField(label="mo")


class ModelNameForm(forms.Form):
    model_name = forms.CharField(label="model_name")

