from django import forms
from django.core.exceptions import ValidationError

from area.models import Area

class AreaForm(forms.Form):
    area = forms.ChoiceField(label='区域',choices=(('A','A'),('B','B')),required=True)
    floor = forms.ChoiceField(label='楼层',choices=((-1,-1),(1,1),(2,2),(3,3)),required=True)
    current_count = forms.IntegerField(label='数量',min_value=1,max_value=26,error_messages={'invalid':'数量在1-26'})
    racklocation_prefix = forms.CharField(label='racklocation名称前缀')
    is_int = forms.ChoiceField(label='后缀是数字还是字母',choices=((0,0),(1,1))) # 0:数字；1:字母

    def clean_current_count(self):
        return self.cleaned_data["current_count"] if self.cleaned_data["current_count"] else 0

    def clean(self):
        area = self.cleaned_data["area"] if 'area' in self.cleaned_data else None
        floor = self.cleaned_data["floor"] if 'floor' in self.cleaned_data else None
        arealis = Area.objects.filter(area=area,floor=floor).values()
        if arealis.exists():
            raise ValidationError("this area is exist")  #django校验异常
        return self.cleaned_data


