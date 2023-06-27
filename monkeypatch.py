# this module is imported as pytest plugin with -p parameter to make sure
# it will be first plugin imported
import gevent.monkey

gevent.monkey.patch_all()  # noqa # noreorder
