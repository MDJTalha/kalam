DO $$
DECLARE
  demo_tenant uuid;
  admin_user uuid;
  demo_role uuid;
  ops_tenant uuid;
  ops_role uuid;
BEGIN
  SELECT id INTO demo_tenant FROM tenants WHERE slug='demo-corporation';
  SELECT id INTO admin_user FROM users WHERE tenant_id=demo_tenant AND email='admin@demo.corp';
  IF demo_tenant IS NOT NULL AND admin_user IS NOT NULL THEN
    INSERT INTO roles(id,tenant_id,name,description,role_kind)
      VALUES(gen_random_uuid(),demo_tenant,'SaaS Demo Administrator','Demo-only full governance role for release QA','predefined') ON CONFLICT DO NOTHING;
    SELECT id INTO demo_role FROM roles WHERE tenant_id=demo_tenant AND name='SaaS Demo Administrator';
    INSERT INTO role_permissions(role_id,permission_id) SELECT demo_role,p.id FROM permissions p ON CONFLICT DO NOTHING;
    INSERT INTO user_roles(user_id,role_id) VALUES(admin_user,demo_role) ON CONFLICT DO NOTHING;
  END IF;
  INSERT INTO tenants(id,name,slug,status,settings) VALUES(gen_random_uuid(),'Kalam Platform Operations','kalam','active','{}'::jsonb) ON CONFLICT (slug) DO NOTHING;
  SELECT id INTO ops_tenant FROM tenants WHERE slug='kalam';
  INSERT INTO roles(id,tenant_id,name,description,role_kind)
    VALUES(gen_random_uuid(),ops_tenant,'SaaS Administrator','Platform operations and commercial administration','predefined') ON CONFLICT DO NOTHING;
  SELECT id INTO ops_role FROM roles WHERE tenant_id=ops_tenant AND name='SaaS Administrator';
  INSERT INTO role_permissions(role_id,permission_id)
    SELECT ops_role,p.id FROM permissions p WHERE p.key LIKE 'saas.%' ON CONFLICT DO NOTHING;
END $$;