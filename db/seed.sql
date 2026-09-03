-- 발표용 Mock 사용자 10명과 2026-09-01 지원 기업 Snapshot
-- Mock 로그인 공통 비밀번호 Demo1234!는 DB에 저장하지 않고 Backend DEMO_PASSWORD를 사용한다.

INSERT INTO users (user_id, username, display_name, is_demo) VALUES
('demo-001', 'demo001', '안정형 장기 초보', TRUE),
('demo-002', 'demo002', '균형형 장기 투자자', TRUE),
('demo-003', 'demo003', '공격형 단기 숙련자', TRUE),
('demo-004', 'demo004', '균형형 중기 초보', TRUE),
('demo-005', 'demo005', '안정형 중기 투자자', TRUE),
('demo-006', 'demo006', '균형형 단기 숙련자', TRUE),
('demo-007', 'demo007', '공격형 단기 초보', TRUE),
('demo-008', 'demo008', '공격형 중기 투자자', TRUE),
('demo-009', 'demo009', '안정형 장기 숙련자', TRUE),
('demo-010', 'demo010', '균형형 장기 초보', TRUE)
ON CONFLICT (user_id) DO UPDATE SET
    username = EXCLUDED.username,
    display_name = EXCLUDED.display_name;

INSERT INTO investment_profiles
    (user_id, experience_level, risk_profile, investment_horizon, preferred_evidence) VALUES
('demo-001', 'beginner',     'conservative', 'long',   'financial'),
('demo-002', 'intermediate', 'balanced',     'long',   'news'),
('demo-003', 'experienced',  'aggressive',   'short',  'risk'),
('demo-004', 'beginner',     'balanced',     'medium', 'market'),
('demo-005', 'intermediate', 'conservative', 'medium', 'financial'),
('demo-006', 'experienced',  'balanced',     'short',  'news'),
('demo-007', 'beginner',     'aggressive',   'short',  'risk'),
('demo-008', 'intermediate', 'aggressive',   'medium', 'market'),
('demo-009', 'experienced',  'conservative', 'long',   'financial'),
('demo-010', 'beginner',     'balanced',     'long',   'news')
ON CONFLICT (user_id) DO UPDATE SET
    experience_level = EXCLUDED.experience_level,
    risk_profile = EXCLUDED.risk_profile,
    investment_horizon = EXCLUDED.investment_horizon,
    preferred_evidence = EXCLUDED.preferred_evidence,
    updated_at = now();

INSERT INTO supported_companies
    (rank, company_name, stock_code, market, snapshot_date, market_cap_trillion_krw) VALUES
(1,  '삼성전자',         '005930', 'KOSPI', '2026-09-01', 1525.9),
(2,  'SK하이닉스',       '000660', 'KOSPI', '2026-09-01', 1236.7),
(3,  'SK스퀘어',         '402340', 'KOSPI', '2026-09-01', 140.8),
(4,  '삼성전기',         '009150', 'KOSPI', '2026-09-01', 106.8),
(5,  'LG에너지솔루션',   '373220', 'KOSPI', '2026-09-01', 85.9),
(6,  '현대차',           '005380', 'KOSPI', '2026-09-01', 82.0),
(7,  '삼성바이오로직스', '207940', 'KOSPI', '2026-09-01', 70.4),
(8,  '삼성물산',         '028260', 'KOSPI', '2026-09-01', 63.3),
(9,  '삼성생명',         '032830', 'KOSPI', '2026-09-01', 61.9),
(10, 'KB금융',           '105560', 'KOSPI', '2026-09-01', 60.7),
(11, '한화에어로스페이스','012450', 'KOSPI', '2026-09-01', 54.6),
(12, '신한지주',         '055550', 'KOSPI', '2026-09-01', 52.2),
(13, '두산에너빌리티',   '034020', 'KOSPI', '2026-09-01', 52.1),
(14, '기아',             '000270', 'KOSPI', '2026-09-01', 51.2),
(15, 'HD현대중공업',     '329180', 'KOSPI', '2026-09-01', 47.5),
(16, '삼성SDI',          '006400', 'KOSPI', '2026-09-01', 45.9),
(17, '셀트리온',         '068270', 'KOSPI', '2026-09-01', 43.7),
(18, 'SK',               '034730', 'KOSPI', '2026-09-01', 42.5),
(19, '현대모비스',       '012330', 'KOSPI', '2026-09-01', 39.8),
(20, '하나금융지주',     '086790', 'KOSPI', '2026-09-01', 37.7)
ON CONFLICT (stock_code) DO UPDATE SET
    rank = EXCLUDED.rank,
    company_name = EXCLUDED.company_name,
    snapshot_date = EXCLUDED.snapshot_date,
    market_cap_trillion_krw = EXCLUDED.market_cap_trillion_krw;
