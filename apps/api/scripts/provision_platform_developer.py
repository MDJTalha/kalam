import asyncio, secrets, string
from sqlalchemy import select
from app.db.session import SessionLocal
from app.db.models import Tenant, User, Role, UserRole
from app.core.security import hash_password
EMAIL='developer@kalam.global'
ALPHABET=string.ascii_letters+string.digits+'!@#$%^&*'
TEMP=''.join(secrets.choice(ALPHABET) for _ in range(24))
async def main():
    async with SessionLocal() as db:
        tenant=await db.scalar(select(Tenant).where(Tenant.slug=='kalam'))
        role=await db.scalar(select(Role).where(Role.tenant_id==tenant.id,Role.name=='Platform Developer')) if tenant else None
        if not tenant or not role: raise RuntimeError('Required Kalam tenant/Platform Developer role missing')
        user=await db.scalar(select(User).where(User.tenant_id==tenant.id,User.email==EMAIL))
        action='repaired'
        if user is None:
            user=User(tenant_id=tenant.id,email=EMAIL,password_hash=hash_password(TEMP),first_name='Platform',last_name='Developer',job_title='Platform Developer',is_active=True)
            db.add(user); await db.flush(); action='created'
        else:
            user.is_active=True; user.failed_login_count=0; user.locked_until=None; user.password_hash=hash_password(TEMP)
        link=await db.scalar(select(UserRole).where(UserRole.user_id==user.id,UserRole.role_id==role.id))
        if link is None: db.add(UserRole(user_id=user.id,role_id=role.id))
        await db.commit()
        print('ACTION='+action); print('EMAIL='+EMAIL); print('TENANT=kalam'); print('TEMP_PASSWORD='+TEMP); print('USER_ID='+str(user.id))
asyncio.run(main())
