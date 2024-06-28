from django.db import models

# Create your models here.

from area.models import Area

status_choice = models.IntegerField(0, 1, 2, 3, 4, 5)


class Rack(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(
        verbose_name='name', unique=True, max_length=50, db_column='name'
    )
    model_name = models.CharField(
        verbose_name='model_name', unique=True, max_length=50, db_column='modelname'
    )
    # test_plan = models.CharField(verbose_name='测试计划路径',max_length=250,db_column='testplanpath',default="",null=True)
    stage = models.CharField(verbose_name='站别', max_length=20, default="NA")
    operator_id = models.CharField(
        verbose_name='操作员代号', max_length=20, db_column='operatorid'
    )
    rack_row = models.IntegerField(verbose_name='机架行数', db_column='rackrow', default=1)
    rack_col = models.IntegerField(verbose_name='机架列数', db_column='rackcol', default=1)
    created_time = models.DateTimeField(
        verbose_name='创建时间', auto_now_add=True, db_column='createdtime'
    )
    updated_time = models.DateTimeField(
        verbose_name='更新时间', auto_now=True, blank=True, db_column='updatedtime'
    )

    class Meta:
        db_table = 'rack'
        app_label = 'rack'
        ordering = ['id']


class RackNode(models.Model):
    id = models.AutoField(primary_key=True)
    operator_id = models.CharField(
        verbose_name='操作员代号', max_length=20, db_column='operatorid'
    )
    sn = models.CharField(verbose_name="sn", max_length=50, default="NA")
    current_stage = models.CharField(verbose_name='站别', max_length=20, default="NA")
    teststatus = models.CharField(
        max_length=1, default='0'
    )  # (0:unused(default) 1:pending 2:testing 3:pass 4:fail 5:timeout
    created_time = models.DateTimeField(
        verbose_name='创建时间', auto_now_add=True, db_column='createdtime'
    )
    updated_time = models.DateTimeField(
        verbose_name='更新时间', auto_now=True, blank=True, db_column='updatedtime'
    )
    rack_id = models.ForeignKey(Rack, on_delete=models.CASCADE, db_column='rackid')
    errorcode = models.CharField(max_length=150, null=True, blank=True, default="")
    change = models.IntegerField(default=0)  # 0返回前端不闪，1闪
    type = models.IntegerField(default=0)  # 0表示默认，1为备品

    class Meta:
        db_table = 'racknode'


class RackLocation(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(verbose_name='名称', max_length=50, default='')
    coordinateX = models.SmallIntegerField(default=0, db_column='coordinatex')
    coordinateY = models.SmallIntegerField(default=0, db_column='coordinatey')
    index = models.IntegerField(verbose_name='区域一维坐标')
    isvalid = models.BooleanField(verbose_name='是否有效', default=True)
    created_time = models.DateTimeField(
        verbose_name='创建时间', auto_now_add=True, db_column='createdtime'
    )
    updated_time = models.DateTimeField(
        verbose_name='更新时间', auto_now=True, blank=True, db_column='updatedtime'
    )
    rack_node_id = models.ForeignKey(
        RackNode, on_delete=models.SET_NULL, null=True, db_column='racknodeid'
    )
    area_id = models.ForeignKey(Area, on_delete=models.CASCADE, db_column='areaid')

    class Meta:
        unique_together = ('rack_node_id', 'isvalid')
        db_table = 'rack_location'


class TestStep(models.Model):
    id = models.AutoField(primary_key=True)
    current_stage = models.CharField(verbose_name='当前站别', max_length=20, default="NA")
    next_stage = models.CharField(verbose_name='下个站别', max_length=20, default="NA")
    stage_type = models.IntegerField(default=0)  # 0为L10，1为非L10
    rack = models.IntegerField(verbose_name='rack', default=0)

    class Meta:
        db_table = 'teststep'
