-- 데모 시드 (회원 2명 + 투자 성향 + 분석 기록 예시 1건)
-- 비밀번호는 발표용 데모 계정 공용 값 Demo1234!다(shared/contracts/frontend_backend).
-- 해시는 backend/app/core/security.py의 PBKDF2(sha256, 200000회)와 같은 형식이다:
--   "<salt hex>$<derived hex>"
-- 실제 회원가입 시에는 여기 값이 아니라 Backend가 매번 새 salt로 생성한다.

INSERT INTO users (user_id, username, password_hash, display_name) VALUES
    ('demo-001', 'demo001',
     '81d89e604160f526e036414e10451207$1a2df8157004d874d39133836a8d5dad6cff4f2fd982c057b270a01752042c54',
     '데모 사용자 1'),
    ('demo-002', 'demo002',
     '81d89e604160f526e036414e10451207$1a2df8157004d874d39133836a8d5dad6cff4f2fd982c057b270a01752042c54',
     '데모 사용자 2')
ON CONFLICT (user_id) DO NOTHING;

-- backend/app/repositories/user_repository.py의 seed 조합 중 1·2번째와 맞춘다.
INSERT INTO user_profiles (user_id, experience_level, risk_profile, investment_horizon, preferred_evidence) VALUES
    ('demo-001', 'beginner', 'conservative', 'long', 'news'),
    ('demo-002', 'intermediate', 'balanced', 'medium', 'market')
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
