import random

from django.conf import settings


# DATABASE_MAPPING = settings.DATABASE_APPS_MAPPING


class DatabaseAppsRouter:

    route_app_labels = {'area', 'rack', 'component', 'testrecord', 'history'}

    def db_for_read(self, model, **hints):
        """ "Point all read operations to the specific database."""
        if model._meta.app_label in self.route_app_labels:
            # 读取-从数据库（随机选取）
            # random.choice(['replica1', 'replica2'])
            return 'l11_test_replica'
        return None

    def db_for_write(self, model, **hints):
        """Point all write operations to the specific database."""
        if model._meta.app_label in self.route_app_labels:
            # 写入-主数据库
            return 'l11_test_primary'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """Allow any relation between apps that use the same database."""
        if (
            obj1._meta.app_label in self.route_app_labels
            or obj2._meta.app_label in self.route_app_labels
        ):
            # print(obj1._state.db,obj1._meta.app_label,obj2._state.db,obj2._meta.app_label)
            return True
        return None

    def allow_migrate(self, db, app_label, model=None, **hints):
        """
        Make sure the auth app only appears in the 'auth_db'
        database.
        """
        if app_label in self.route_app_labels:
            # 通过 python manage.py migrate --database=db1 将APP迁移指定数据库
            # 默认迁移主数据库，业务分库需要另外判断
            # return 'l11_test_primary' == db
            return True
        else:
            return False
