import asyncio
from sqlalchemy import select
from app.db.session import SessionLocal
from app.db.models import User,Tenant
async def main():
 async with SessionLocal() as db:
  u=await db.scalar(select(User).join(Tenant,Tenant.id==User.tenant_id).where(User.email=='developer@kalam.global',Tenant.slug=='kalam'))
  u.failed_login_count=0
  u.locked_until=None
  await db.commit()
  print('UNLOCKED='+str(u.email))
asyncio.run(main())
