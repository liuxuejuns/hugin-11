from django.db import models

from rack.models import RackNode
from component.models import ComponentNode
from public import utils

# Create your models here.


class RackHistory(models.Model):
    id = models.AutoField(primary_key=True)
    rack_id = models.SmallIntegerField(default=0, blank=True)
    rack_sn = models.CharField(verbose_name="rack_sn", max_length=50, default="NA")
    current_stage = models.CharField(verbose_name='站别', max_length=20, default="NA")
    operatorid = models.CharField(max_length=20, null=True, blank=True, default="")
    teststatus = models.CharField(
        max_length=1, default='0'
    )  # (0:unused(default) 1:pending 2:testing 3:pass 4:fail 5:timeout
    isvalid = models.BooleanField(default=True)
    created_time = models.DateTimeField(
        verbose_name='创建时间', auto_now_add=True, db_column='createdtime'
    )
    updated_time = models.DateTimeField(
        verbose_name='更新时间', auto_now=True, blank=True, db_column='updatedtime'
    )

    class Meta:
        db_table = 'rackhistory'
        app_label = 'history'


class TestItemHistoryRecord(models.Model):
    id = models.AutoField(primary_key=True)
    rack_sn = models.CharField(verbose_name="rack_sn", max_length=50, default="NA")
    component_id = models.SmallIntegerField(default=0, blank=True)
    component_sn = models.CharField(
        verbose_name="component_sn", max_length=50, default="NA"
    )
    stage = models.CharField(max_length=20, default="", null=True)
    testitem = models.CharField(max_length=50, null=True)
    waittime = models.SmallIntegerField(
        default=0, null=True, blank=True
    )  # 0:no timeout status
    starttime = models.DateTimeField(null=True)
    endtime = models.DateTimeField(null=True)
    teststatus = models.CharField(
        max_length=1, default='0'
    )  # ((0:unused(default) 1:pending 2:testing 3:pass 4:fail 5:timeout)
    errorcode = models.CharField(max_length=100, null=True, blank=True, default="")
    errordescription = models.CharField(
        max_length=1024, null=True, blank=True, default=""
    )
    operatorid = models.CharField(max_length=20, null=True, blank=True, default="")
    createtime = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    isvalid = models.BooleanField(default=True)  # add
    ismanual = models.BooleanField(
        default=True, null=True, blank=True
    )  # True:manual , False:auto

    class Meta:
        db_table = 'testitemrecordhistory'
        app_label = 'history'
