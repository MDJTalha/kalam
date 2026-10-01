import asyncio
from sqlalchemy import select
from app.db.session import SessionLocal
from app.db.models import User,Tenant
from app.core.security import verify_password
P='RY2OBdHkyCVRTcNO#bTVIRiJ'
async def main():
 async with SessionLocal() as db:
  result=await db.execute(select(User).join(Tenant,Tenant.id==User.tenant_id).where(User.email=='developer@kalam.global').where(Tenant.slug=='kalam').where(Tenant.status=='active'))
  u=result.scalar_one_or_none()
  print('FOUND='+str(u is not None))
  if u:
   print('EMAIL='+repr(u.email)); print('ACTIVE='+str(u.is_active)); print('LOCK='+repr(u.locked_until)); print('FAILED='+str(u.failed_login_count)); print('VERIFY='+str(verify_password(P,u.password_hash)))
   t=await db.scalar(select(Tenant).where(Tenant.id==u.tenant_id)); print('TENANT='+repr((t.slug,t.status)))
asyncio.run(main())
