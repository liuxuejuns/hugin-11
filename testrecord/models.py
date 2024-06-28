from enum import unique
from django.db import models

# Create your models here.

from rack.models import RackNode
from component.models import ComponentNode, Component

# from area.models import RackLocation


class TestItemRecord(models.Model):
    id = models.AutoField(primary_key=True)
    sn = models.CharField(verbose_name="component sn", max_length=50, default="NA")
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
        db_table = 'testitemrecord'
        app_label = 'testrecord'


class Error(models.Model):
    id = models.AutoField(primary_key=True)
    errorcode = models.CharField(max_length=100, null=True, blank=True, default="")
    errordescription = models.CharField(
        max_length=1024, null=True, blank=True, default=""
    )
    createtime = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = 'error'
        app_label = 'testrecord'


class ComponentObject(models.Model):
    id = models.AutoField(primary_key=True)
    component_sn = models.CharField(
        max_length=100, null=True, blank=True, default="", unique=True
    )
    component_type_id = models.ForeignKey(
        Component, on_delete=models.CASCADE, db_column='componentid'
    )
    createtime = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    log_path = models.CharField(
        verbose_name='日志路径', max_length=250, db_column='logpath', default="", null=True
    )
    operatorid = models.CharField(max_length=20, null=True, blank=True, default="")
    ethernetip = models.GenericIPAddressField(null=True, blank=True, default="")
    bmcip = models.GenericIPAddressField(null=True, blank=True, default="")
    isvalid = models.BooleanField(default=True)
    is_pass = models.BooleanField(default=False)

    class Meta:
        db_table = 'component_obj'
        app_label = 'testrecord'


class ConsumeRecord(models.Model):
    id = models.CharField(max_length=16, primary_key=True)
    rack_sn = models.CharField(max_length=100)
    component_sn = models.CharField(max_length=100)
    role = models.SmallIntegerField(default=0)  # 0=server 1=client
    spare = models.SmallIntegerField(default=0)  # 默认0,不是备品
    server_ip = models.GenericIPAddressField(
        max_length=50, null=True, blank=True, default=""
    )
    client_ip = models.GenericIPAddressField(
        max_length=50, null=True, blank=True, default=""
    )
    state = models.SmallIntegerField(
        default=0
    )  # 默认0，0=已经生成没有消费，1=已经消费等待匹配，2=已经消费已经匹配完成
    createtime = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = 'consume'
        app_label = 'testrecord'
