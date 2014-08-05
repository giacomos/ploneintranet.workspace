from ploneintranet.workspace.config import INTRANET_USERS_GROUP_ID
from ploneintranet.workspace.config import DYNAMIC_GROUPS_PLUGIN_ID
from plone import api

from Products.PluggableAuthService.plugins.DynamicGroupsPlugin \
    import addDynamicGroupsPlugin
from Products.PlonePAS.Extensions.Install import activatePluginInterfaces


def post_install(context):
    """
    - sets an acl user group to hold all intranet users
    - setup the dynamic groups plugin
    - sets the addable types for the ploneintranet policy
    """
    marker = 'ploneintranet-workspace.marker'
    if context.readDataFile(marker) is None:
        return

    portal = api.portal.get()

    # Set up a group to hold all intranet users
    if api.group.get(groupname=INTRANET_USERS_GROUP_ID) is None:
        api.group.create(groupname=INTRANET_USERS_GROUP_ID)
        # All users have Reader role on portal root
        api.group.grant_roles(groupname=INTRANET_USERS_GROUP_ID,
                              roles=['Reader', ],
                              obj=portal)

    # Set up dynamic groups plugin to put all users into the above group
    pas = api.portal.get_tool('acl_users')
    if DYNAMIC_GROUPS_PLUGIN_ID not in pas.objectIds():
        addDynamicGroupsPlugin(
            pas,
            DYNAMIC_GROUPS_PLUGIN_ID,
            "ploneintranet.workspace Dynamic Groups"
        )
        plugin = pas[DYNAMIC_GROUPS_PLUGIN_ID]
        plugin.addGroup(
            group_id=INTRANET_USERS_GROUP_ID,
            predicate='python: True',
            title='All Intranet Users',
            description='',
            active=True,
        )
        # activate the plugin (all interfaces)
        activatePluginInterfaces(portal, DYNAMIC_GROUPS_PLUGIN_ID)

    # deactivate the enumerate groups interface for collective.workspace
    activatePluginInterfaces(portal, 'workspace_groups',
                             disable=['IGroupEnumerationPlugin'])

    # Set up the ploneintranet policy for all addable types
    default_types = []
    types = api.portal.get_tool('portal_types')
    for type_info in types.listTypeInfo():
        if type_info.global_allow:
            default_types.append(type_info.getId())

    if default_types:
        pwftool = api.portal.get_tool('portal_placeful_workflow')
        policy = pwftool['ploneintranet_policy']
        policy.setChainForPortalTypes(default_types, ('(Default)',))
