import sys

if sys.version_info > (3,):
    collect_ignore = ["test_django_channels.py"]
    if sys.version_info < (3, 6):
        collect_ignore.append('test_gevent.py')
else:
    collect_ignore = ["test_aiohttp.py"]
