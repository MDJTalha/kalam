UPDATE saas_plans
SET limits = jsonb_set(
  COALESCE(limits,'{}'::jsonb),
  '{public_merchandising}',
  '{"featured":true,"badge_label":"Most popular","cta_type":"evaluation","cta_label":"Evaluate Scale","comparison_label":"Best for multi-team organizations"}'::jsonb,
  true
)
WHERE code='scale' AND currency='USD';
