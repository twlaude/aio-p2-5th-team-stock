-- 데모 시드 (발표용 회원 10명 + 투자 성향 + 분석 기록 예시 1건)
-- 비밀번호는 발표용 데모 계정 공용 값 Demo1234!다(shared/contracts/frontend_backend).
-- 해시는 backend/app/core/security.py의 PBKDF2(sha256, 200000회)와 같은 형식이다:
--   "<salt hex>$<derived hex>"
-- 실제 회원가입 시에는 여기 값이 아니라 Backend가 매번 새 salt로 생성한다.

INSERT INTO users (user_id, username, password_hash, display_name) VALUES
    ('demo-001', 'demo001', '81d89e604160f526e036414e10451207$1a2df8157004d874d39133836a8d5dad6cff4f2fd982c057b270a01752042c54', '안정형 장기 초보'),
    ('demo-002', 'demo002', '81d89e604160f526e036414e10451207$1a2df8157004d874d39133836a8d5dad6cff4f2fd982c057b270a01752042c54', '균형형 장기 투자자'),
    ('demo-003', 'demo003', '81d89e604160f526e036414e10451207$1a2df8157004d874d39133836a8d5dad6cff4f2fd982c057b270a01752042c54', '공격형 단기 숙련자'),
    ('demo-004', 'demo004', '81d89e604160f526e036414e10451207$1a2df8157004d874d39133836a8d5dad6cff4f2fd982c057b270a01752042c54', '균형형 중기 초보'),
    ('demo-005', 'demo005', '81d89e604160f526e036414e10451207$1a2df8157004d874d39133836a8d5dad6cff4f2fd982c057b270a01752042c54', '안정형 중기 투자자'),
    ('demo-006', 'demo006', '81d89e604160f526e036414e10451207$1a2df8157004d874d39133836a8d5dad6cff4f2fd982c057b270a01752042c54', '균형형 단기 숙련자'),
    ('demo-007', 'demo007', '81d89e604160f526e036414e10451207$1a2df8157004d874d39133836a8d5dad6cff4f2fd982c057b270a01752042c54', '공격형 단기 초보'),
    ('demo-008', 'demo008', '81d89e604160f526e036414e10451207$1a2df8157004d874d39133836a8d5dad6cff4f2fd982c057b270a01752042c54', '공격형 중기 투자자'),
    ('demo-009', 'demo009', '81d89e604160f526e036414e10451207$1a2df8157004d874d39133836a8d5dad6cff4f2fd982c057b270a01752042c54', '안정형 장기 숙련자'),
    ('demo-010', 'demo010', '81d89e604160f526e036414e10451207$1a2df8157004d874d39133836a8d5dad6cff4f2fd982c057b270a01752042c54', '균형형 장기 초보')
ON CONFLICT (user_id) DO NOTHING;

-- 네 값을 순환시켜 다양한 조합을 만든다.
INSERT INTO user_profiles (user_id, experience_level, risk_profile, investment_horizon, preferred_evidence) VALUES
    ('demo-001', 'beginner', 'conservative', 'long', 'financial'),
    ('demo-002', 'intermediate', 'balanced', 'long', 'news'),
    ('demo-003', 'experienced', 'aggressive', 'short', 'risk'),
    ('demo-004', 'beginner', 'balanced', 'medium', 'market'),
    ('demo-005', 'intermediate', 'conservative', 'medium', 'financial'),
    ('demo-006', 'experienced', 'balanced', 'short', 'news'),
    ('demo-007', 'beginner', 'aggressive', 'short', 'risk'),
    ('demo-008', 'intermediate', 'aggressive', 'medium', 'market'),
    ('demo-009', 'experienced', 'conservative', 'long', 'financial'),
    ('demo-010', 'beginner', 'balanced', 'long', 'news')
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO analysis_runs (
    request_id, user_id, company_name, stock_code, access_level, status,
    one_line_summary, sources, partial_failures, personalized_checkpoints,
    requested_at, collected_at
) VALUES (
    'seed-demo-analysis-005930-001',
    'demo-001',
    '삼성전자',
    '005930',
    'member',
    'success',
    '삼성전자의 최근 흐름을 뉴스·공시·커뮤니티 반응과 함께 정리했다(Seed 예시).',
    '[]'::jsonb,
    '[]'::jsonb,
    '{
        "personal_summary": "장기 관점에서 보면: 삼성전자의 최근 흐름을 정리했다(Seed 예시).",
        "priority_checks": ["최근 뉴스부터 확인해보자.", "conservative 성향에 맞는 변동성 수준인지 점검해보자."],
        "caution": "이 확인 포인트는 매수·매도를 추천하지 않으며 참고용 설명이다."
    }'::jsonb,
    now() - interval '1 day',
    now() - interval '1 day'
)
ON CONFLICT (request_id) DO NOTHING;
