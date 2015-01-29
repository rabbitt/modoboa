"""A management command to load Modoboa initial data:

* Create a default super admin if none exists
* Create groups and permissions

"""

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from modoboa.core import PERMISSIONS
from modoboa.core.extensions import exts_pool
from modoboa.core.models import User, ObjectAccess
from modoboa.lib import events
from modoboa.lib.permissions import add_permissions_to_group
from . import CloseConnectionMixin


class Command(BaseCommand, CloseConnectionMixin):

    """Command defintion."""

    help = "Load Modoboa initial data"

    def handle(self, *args, **options):
        """Command entry point."""

        if not User.objects.filter(pk=1, username="admin").exists():
            admin = User(username="admin", is_superuser=True)
            admin.set_password("password")
            admin.save()
            ObjectAccess.objects.create(
                user=admin, content_object=admin, is_owner=True)

        groups = PERMISSIONS.keys() + [
            role[0] for role in events.raiseQueryEvent("GetExtraRoles")
        ]
        for groupname in groups:
            group, created = Group.objects.get_or_create(name=groupname)
            permissions = (
                PERMISSIONS.get(groupname, []) +
                events.raiseQueryEvent("GetExtraRolePermissions", groupname)
            )
            if not permissions:
                continue
            add_permissions_to_group(group, permissions)

        exts_pool.load_all()
        for extname in exts_pool.extensions.keys():
            extension = exts_pool.get_extension(extname)
            extension.load_initial_data()