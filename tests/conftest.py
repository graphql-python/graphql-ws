import sys

if sys.version_info > (3,):
    collect_ignore = ["test_django_channels.py"]
else:
    collect_ignore = ["test_aiohttp.py", "test_base_async.py"]
