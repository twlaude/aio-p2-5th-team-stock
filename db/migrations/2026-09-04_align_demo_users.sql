BEGIN;

UPDATE users SET display_name = '안정형 장기 초보' WHERE user_id = 'demo-001';
UPDATE users SET display_name = '균형형 장기 투자자' WHERE user_id = 'demo-002';
UPDATE users SET display_name = '공격형 단기 숙련자' WHERE user_id = 'demo-003';
UPDATE users SET display_name = '균형형 중기 초보' WHERE user_id = 'demo-004';
UPDATE users SET display_name = '안정형 중기 투자자' WHERE user_id = 'demo-005';
UPDATE users SET display_name = '균형형 단기 숙련자' WHERE user_id = 'demo-006';
UPDATE users SET display_name = '공격형 단기 초보' WHERE user_id = 'demo-007';
UPDATE users SET display_name = '공격형 중기 투자자' WHERE user_id = 'demo-008';
UPDATE users SET display_name = '안정형 장기 숙련자' WHERE user_id = 'demo-009';
UPDATE users SET display_name = '균형형 장기 초보' WHERE user_id = 'demo-010';

UPDATE user_profiles SET experience_level = 'beginner', risk_profile = 'conservative', investment_horizon = 'long', preferred_evidence = 'financial', updated_at = now() WHERE user_id = 'demo-001';
UPDATE user_profiles SET experience_level = 'intermediate', risk_profile = 'balanced', investment_horizon = 'long', preferred_evidence = 'news', updated_at = now() WHERE user_id = 'demo-002';
UPDATE user_profiles SET experience_level = 'experienced', risk_profile = 'aggressive', investment_horizon = 'short', preferred_evidence = 'risk', updated_at = now() WHERE user_id = 'demo-003';
UPDATE user_profiles SET experience_level = 'beginner', risk_profile = 'balanced', investment_horizon = 'medium', preferred_evidence = 'market', updated_at = now() WHERE user_id = 'demo-004';
UPDATE user_profiles SET experience_level = 'intermediate', risk_profile = 'conservative', investment_horizon = 'medium', preferred_evidence = 'financial', updated_at = now() WHERE user_id = 'demo-005';
UPDATE user_profiles SET experience_level = 'experienced', risk_profile = 'balanced', investment_horizon = 'short', preferred_evidence = 'news', updated_at = now() WHERE user_id = 'demo-006';
UPDATE user_profiles SET experience_level = 'beginner', risk_profile = 'aggressive', investment_horizon = 'short', preferred_evidence = 'risk', updated_at = now() WHERE user_id = 'demo-007';
UPDATE user_profiles SET experience_level = 'intermediate', risk_profile = 'aggressive', investment_horizon = 'medium', preferred_evidence = 'market', updated_at = now() WHERE user_id = 'demo-008';
UPDATE user_profiles SET experience_level = 'experienced', risk_profile = 'conservative', investment_horizon = 'long', preferred_evidence = 'financial', updated_at = now() WHERE user_id = 'demo-009';
UPDATE user_profiles SET experience_level = 'beginner', risk_profile = 'balanced', investment_horizon = 'long', preferred_evidence = 'news', updated_at = now() WHERE user_id = 'demo-010';

COMMIT;
