from django.db import models

# Create your models here.
floor_choice = models.IntegerField(-1, 1, 2, 3)
area_choice = models.CharField('A', 'B')


class Area(models.Model):
    id = models.AutoField(primary_key=True)
    area = models.CharField(
        verbose_name='区域', max_length=2, choices=area_choice.choices
    )
    floor = models.IntegerField(verbose_name='楼层', choices=floor_choice.choices)
    current_count = models.IntegerField(
        verbose_name='当前数量', db_column='count', default=0
    )
    isvalid = models.BooleanField(
        verbose_name='是否有效', blank=True, null=True, default=True
    )
    created_time = models.DateTimeField(
        verbose_name='创建时间', auto_now_add=True, db_column='createdtime'
    )
    updated_time = models.DateTimeField(
        verbose_name='更新时间', auto_now=True, blank=True, db_column='updatedtime'
    )

    class Meta:
        db_table = 'area'
        app_label = 'area'
        unique_together = ('area','floor')



