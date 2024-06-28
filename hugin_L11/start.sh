
python manage.py makemigrations&&
python manage.py migrate --database=l11_test_primary&&
echo 111&&
uwsgi -d --ini /L11/docker/L11_uwsgi.ini&&
echo 333&&
hypercorn -b 0.0.0.0:8903 hugin_L11.asgi:application&&
echo 222
