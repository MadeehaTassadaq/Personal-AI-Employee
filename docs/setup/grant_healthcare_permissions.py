#!/usr/bin/env python3
"""Grant admin user Healthcare Manager permissions in Odoo."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def grant_healthcare_permissions():
    """Grant admin user Healthcare Manager permissions."""
    from mcp_services.odoo_mcp.jsonrpc_client import OdooClient

    client = OdooClient(
        url='http://localhost:8069',
        db='odoo19',
        username='admin',
        password='odoo'
    )

    print('=== Granting Healthcare Manager Permissions ===\n')

    # Authenticate
    print('1. Authenticating to Odoo...')
    await client.authenticate()
    print('   Authenticated!\n')

    # Find Healthcare Manager group
    print('2. Finding Healthcare Manager group...')
    groups = await client.search_read(
        model='res.groups',
        domain=[['name', 'ilike', 'healthcare']],
        fields=['id', 'name', 'user_ids'],
        limit=10
    )

    print(f'   Found {len(groups)} healthcare-related groups:')
    healthcare_group_id = None
    for g in groups:
        print(f"     - ID: {g.get('id')}, Name: {g.get('name')}, Users: {g.get('user_ids', [])}")
        if 'Healthcare Manager' in g.get('name', ''):
            healthcare_group_id = g.get('id')

    if not healthcare_group_id:
        print('\n   ERROR: Healthcare Manager group not found!')
        return False

    # Get admin user
    print(f'\n3. Getting admin user info...')
    admin_id = 2  # Default admin ID
    admin_users = await client.search_read(
        model='res.users',
        domain=[['login', '=', 'admin']],
        fields=['id', 'login', 'name'],
        limit=1
    )
    if admin_users:
        admin_id = admin_users[0]['id']
        print(f"   Admin ID: {admin_id}, Login: {admin_users[0].get('login')}")

    # Check if admin already in group
    print(f'\n4. Checking if admin already in Healthcare Manager group...')
    group_details = await client.read(
        model='res.groups',
        ids=[healthcare_group_id],
        fields=['id', 'name', 'user_ids']
    )
    current_users = group_details[0].get('user_ids', [])
    print(f'   Current users in group: {current_users}')

    if admin_id in current_users:
        print(f'   Admin (ID {admin_id}) already in Healthcare Manager group!')
    else:
        print(f'   Adding admin (ID {admin_id}) to Healthcare Manager group...')
        # Try adding from user side instead
        result = await client.write(
            model='res.users',
            ids=[admin_id],
            values={'groups_id': [(4, healthcare_group_id)]}
        )
        print(f'   Done! Result: {result}')

    # Verify the change
    print(f'\n5. Verifying permissions...')
    updated_group = await client.read(
        model='res.groups',
        ids=[healthcare_group_id],
        fields=['id', 'name', 'user_ids']
    )
    print(f'   Users in Healthcare Manager group: {updated_group[0].get("user_ids", [])}')

    if admin_id in updated_group[0].get('user_ids', []):
        print('\n✅ SUCCESS! Admin now has Healthcare Manager permissions.')
        return True
    else:
        print('\n❌ FAILED! Admin not added to group.')
        return False


if __name__ == "__main__":
    success = asyncio.run(grant_healthcare_permissions())
    sys.exit(0 if success else 1)
