from email.policy import default
from django.db import models

from rack.models import RackLocation, Rack, RackNode

# Create your models here.


class Component(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(
        verbose_name='name', unique=True, max_length=50, db_column='name'
    )
    model = models.CharField(verbose_name='model name', unique=True, max_length=50)
    is_iperf = models.BooleanField(verbose_name="是否需要iperf测试", default=False)
    test_plan = models.CharField(
        verbose_name='测试计划路径', max_length=250, db_column='testplanpath'
    )
    stage = models.CharField(verbose_name='站别', max_length=20)
    col = models.IntegerField(verbose_name='component占用列数', default=1)
    row = models.IntegerField(verbose_name='component占用行数', default=1)
    type = models.IntegerField(
        verbose_name="类型,L10,非L10", default=0
    )  # 22/11/01, 0:L10;1:非L10(switch,PDU)
    created_time = models.DateTimeField(
        verbose_name='创建时间', auto_now_add=True, db_column='createdtime'
    )
    updated_time = models.DateTimeField(
        verbose_name='更新时间', auto_now=True, blank=True, db_column='updatedtime'
    )

    class Meta:
        db_table = 'component'
        app_label = 'component'
        ordering = ['id']


class RackComponent(models.Model):
    id = models.AutoField(primary_key=True)
    start_row = models.IntegerField(verbose_name='起始行', db_column='startrow')
    end_row = models.IntegerField(verbose_name='终止行', db_column='endrow')
    start_col = models.IntegerField(verbose_name='起始列', db_column='startcol', default=0)
    end_col = models.IntegerField(verbose_name='终止列', db_column='endcol', default=0)
    rack_id = models.ForeignKey(Rack, on_delete=models.CASCADE, db_column='rackid')
    component_id = models.ForeignKey(
        Component, on_delete=models.CASCADE, db_column='componentid'
    )

    class Meta:
        db_table = 'rackcomponent'


class ComponentNode(models.Model):
    id = models.AutoField(primary_key=True)
    operator_id = models.CharField(
        verbose_name='操作员代号',
        max_length=20,
        db_column='operatorid',
        null=True,
        blank=True,
        default="",
    )
    sn = models.CharField(verbose_name="sn", max_length=50, default="NA")
    # stage = models.CharField(verbose_name="stage",max_length=20,null=True,blank=True,default="")
    is_valid = models.BooleanField(verbose_name="是否有效", default=True)
    created_time = models.DateTimeField(
        verbose_name='创建时间', auto_now_add=True, db_column='createdtime'
    )
    updated_time = models.DateTimeField(
        verbose_name='更新时间', auto_now=True, db_column='updatedtime'
    )
    change = models.IntegerField(default=0)  # 0返回前端不闪，1闪
    teststatus = models.CharField(
        max_length=2, default='-1'
    )  # (-1:null(default)(0:unused 1:pending 2:testing 3:pass 4:fail 5:timeout)
    current_stage = models.CharField(verbose_name='站别', max_length=20, default="NA")
    # rack_location_id = models.ForeignKey(RackLocation,on_delete=models.CASCADE,db_column='racklocationid')
    # rack_component_id = models.ForeignKey(RackComponent,on_delete=models.CASCADE,db_column='rackcomponentid')
    component_id = models.ForeignKey(
        Component, on_delete=models.CASCADE, db_column='componentid'
    )

    class Meta:
        db_table = 'componentnode'


class RackComponentNode(models.Model):
    id = models.AutoField(primary_key=True)
    start_row = models.IntegerField(verbose_name='起始行', db_column='startrow')
    end_row = models.IntegerField(verbose_name='终止行', db_column='endrow')
    start_col = models.IntegerField(verbose_name='起始列', db_column='startcol', default=0)
    end_col = models.IntegerField(verbose_name='终止列', db_column='endcol', default=0)
    rack_node_id = models.ForeignKey(
        RackNode, on_delete=models.CASCADE, db_column='racknodeid'
    )
    component_node_id = models.ForeignKey(
        ComponentNode, on_delete=models.CASCADE, db_column='componentnodeid'
    )

    class Meta:
        db_table = 'rackcomponentnode'


class SN(models.Model):
    id = models.AutoField(primary_key=True)
    sn = models.CharField(max_length=100)
    created_time = models.DateTimeField(
        verbose_name='创建时间', auto_now_add=True, db_column='createdtime'
    )
    component_id = models.ForeignKey(
        Component, on_delete=models.CASCADE, db_column='componentid'
    )

    class Meta:
        db_table = 'sn'
        app_label = 'component'
        unique_together = ('sn', 'component_id')


class PN(models.Model):
    id = models.AutoField(primary_key=True)
    pn = models.CharField(max_length=100)
    created_time = models.DateTimeField(
        verbose_name='创建时间', auto_now_add=True, db_column='createdtime'
    )
    component_id = models.ForeignKey(
        Component, on_delete=models.CASCADE, db_column='componentid'
    )

    class Meta:
        db_table = 'pn'
        app_label = 'component'
        unique_together = ('pn', 'component_id')


class MO(models.Model):
    id = models.AutoField(primary_key=True)
    mo = models.CharField(max_length=100)
    created_time = models.DateTimeField(
        verbose_name='创建时间', auto_now_add=True, db_column='createdtime'
    )
    component_id = models.ForeignKey(
        Component, on_delete=models.CASCADE, db_column='componentid'
    )

    class Meta:
        db_table = 'mo'
        app_label = 'component'
        unique_together = ('mo', 'component_id')


# class ModelName(models.Model):
#     id = models.AutoField(primary_key=True)
#     model_name = models.CharField(max_length=100)
#     created_time = models.DateTimeField(
#         verbose_name='创建时间', auto_now_add=True, db_column='createdtime'
#     )
#     component_id = models.ForeignKey(
#         Component, on_delete=models.CASCADE, db_column='componentid'
#     )

#     class Meta:
#         db_table = 'modelname'
#         app_label = 'component'
#         unique_together = ('model_name', 'component_id')
