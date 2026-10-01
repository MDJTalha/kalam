import asyncio
from sqlalchemy import select
from app.db.session import SessionLocal
from app.db.models import User,Tenant,Role,UserRole
async def main():
 async with SessionLocal() as db:
  u=await db.scalar(select(User).join(Tenant,Tenant.id==User.tenant_id).where(User.email=='developer@kalam.global',Tenant.slug=='kalam'))
  if not u: print('MISSING'); return
  roles=(await db.execute(select(Role.name).join(UserRole,UserRole.role_id==Role.id).where(UserRole.user_id==u.id))).scalars().all()
  print('ACTIVE='+str(u.is_active)); print('LOCKED='+str(u.locked_until)); print('ROLES='+','.join(roles))
asyncio.run(main())
