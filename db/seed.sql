-- 데모용 시드 (사용자 1명 + 보유 1종목 + 투자 메모 샘플)
-- 메모 embedding은 NULL로 두고 backend/scripts/embed_chunks.py 가 채운다.

INSERT INTO users (username) VALUES ('demo')
ON CONFLICT (username) DO NOTHING;

INSERT INTO positions (user_id, stock_code, stock_name, quantity, avg_price)
SELECT id, '005930', '삼성전자', 10, 71000 FROM users WHERE username = 'demo'
ON CONFLICT (user_id, stock_code) DO NOTHING;

INSERT INTO rag_chunks (user_id, stock_code, doc_type, title, content, content_hash, published_at)
SELECT u.id, v.stock_code, 'user_note', v.title, v.content, md5(v.content), v.published_at
FROM users u,
     (VALUES
        ('005930', '매수 근거', 'HBM 수요 확대로 메모리 업황 턴어라운드를 기대하고 매수. 경쟁사 대비 밸류에이션 매력 있다고 판단.', now() - interval '60 days'),
        ('005930', '우려',      '파운드리 적자 지속이 부담. 대형 고객 수주 소식 없으면 비중 확대는 보류.', now() - interval '45 days'),
        ('005930', '매도 조건', 'HBM 공급 과잉 신호가 나오거나 분기 영업이익이 시장 기대를 크게 하회하면 절반 정리.', now() - interval '45 days')
     ) AS v(stock_code, title, content, published_at)
WHERE u.username = 'demo'
ON CONFLICT (doc_type, content_hash) DO NOTHING;
