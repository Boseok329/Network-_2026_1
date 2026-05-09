# HFT 산업 개요 (HFT Industry Overview)

> 📌 **이 문서의 목적**: HFT(High-Frequency Trading)가 어떻게 등장했고, 현재 어느 정도 규모이며, 왜 µs 단위 속도가 그렇게 중요한지 설명한다.

---

## 1. HFT의 정의와 역사

### 정의

**High-Frequency Trading (HFT, 고빈도 거래)** 는 다음 세 가지 특성을 모두 만족하는 자동매매 방식이다:

1. **Algorithm-driven**: 사람이 아닌 알고리즘이 매수/매도 의사결정을 한다
2. **High order-to-trade ratio**: 1초당 수천~수만 건 주문을 발생시키되, 대부분은 즉시 취소(cancel) 된다
3. **Ultra-low latency**: µs(마이크로초) 단위로 작동하며, 모든 시스템 설계 결정이 지연 최소화에 종속된다

### 역사적 흐름

| 시기 | 이벤트 | 영향 |
|------|--------|------|
| 1970s | NASDAQ 전자 거래 시작 | 사람의 손을 떠나기 시작 |
| 1998 | SEC Regulation ATS | 대안 거래 시스템(ATS) 합법화 → 다중 거래소 시대 |
| 2005 | SEC Regulation NMS | 모든 거래소 가격 통합 → 차익거래 기회 폭발 |
| 2007 | Decimalization 완료 | 호가 단위 1¢로 → 빠른 자가 우위 |
| 2010 | Flash Crash | HFT의 위험성이 대중에 알려짐 (1조 달러 시장 가치 일시 증발) |
| 2010 | Spread Networks 시카고-뉴욕 광케이블 개통 | 인프라 군비경쟁의 시작 |
| 2012~ | Microwave network 등장 | 광속의 99% 도달 |
| 2020s | FPGA, ASIC, kernel bypass 보편화 | µs → ns 단위 경쟁 |

---

## 2. 산업 규모

- **거래량 비중**: 미국 주식 시장 거래량의 약 50% 가 HFT
- **연간 매출**: 글로벌 HFT 회사 합산 약 70억~150억 달러 추정 (Tabb Group)
- **인프라 투자**: 단일 거래소-거래소 간 마이크로웨이브 라인 1개에 수천만 달러
- **인력 시장**: 시니어 HFT 엔지니어 연봉 50만~수백만 달러 수준

---

## 3. 주요 플레이어

### 미국 기반

| 회사 | 특징 |
|------|------|
| Citadel Securities | 미국 주식 거래의 ~25%를 처리하는 최대 마켓 메이커 |
| Virtu Financial | 5,000+ 종목에서 시장 조성, 상장사로 재무 정보 공개 |
| Jump Trading | 학계와 활발한 연구 협력, 양자 컴퓨팅 투자 |
| Hudson River Trading | 학술/수학 인재 채용 중심 |
| Two Sigma, DE Shaw | 통계적 차익거래 + HFT 혼합 |

### 한국 시장

- 외국계 IB(Goldman Sachs, Morgan Stanley 등)의 prop trading 부서
- 일부 국내 증권사의 알고리즘 트레이딩 데스크

---

## 4. HFT의 주요 전략

### 4.1 Market Making (시장 조성)

- 매수 호가(bid)와 매도 호가(ask)를 동시에 걸어 **스프레드(spread) 수익** 확보
- 거래소가 마켓 메이커에게 리베이트(rebate) 지급
- 위험: 시장 급변 시 인벤토리 손실
- **속도가 중요한 이유**: 가격이 바뀌는 순간 호가를 즉시 갱신해야 손실 방지

### 4.2 Statistical Arbitrage (통계적 차익거래)

- 자산 간 통계적 관계가 일시적으로 무너지는 순간 포착
- 예: 코카콜라/펩시 가격 비율이 평균에서 일시 이탈 → 평균 회귀 베팅
- **속도가 중요한 이유**: 다른 봇이 같은 신호를 보기 전에 진입

### 4.3 Latency Arbitrage (지연 차익거래)

- 거래소 A가 B보다 1ms 빠르게 가격 정보를 받는 경우
- A의 가격을 보고 B에 거래 → 무위험 차익
- **속도가 거래의 본질** — 1µs 늦으면 수익 0
- 본 프로젝트의 분석 대상에 가장 가까운 전략

### 4.4 Event-driven Trading

- 뉴스, 실적 발표, FOMC 발표 등 이벤트에 µs 단위로 반응
- AI/NLP로 뉴스를 자동 파싱 후 즉시 거래
- **속도와 정확도의 트레이드오프**

---

## 5. 왜 µs를 다투는가 — 정량적 근거

### 5.1 수익 vs 지연 관계

학계 추정에 따르면, HFT 회사가 1ms 빨라질 때 일일 수익은 약 **100만~수백만 달러** 증가 (Aquilina et al., QJE 2022 추정).

**1µs 단축의 가치 ≈ 1ms 단축의 1/1000 ≈ 일 1,000~수천 달러 (단순 비례 가정)**

### 5.2 "Loser's Market" 구조

- 가격 변동 발생 → 첫 번째 도착자만 수익
- 1등이 아니면 거의 모든 경우에 수익 0 또는 음수
- → 평균이 아닌 **확률적으로 1등 가능성**이 핵심
- → **Tail Latency (P99, P99.9) 가 평균보다 중요**

### 5.3 군비경쟁(Arms Race) 효과

- 한 회사가 1µs 빨라지면 경쟁사들도 따라옴
- 결국 모든 회사의 절대 지연은 줄어들지만 **상대적 우위는 일시적**
- 이 끊임없는 경쟁이 µs → ns 단위까지 내려가게 만든 원동력

---

## 6. HFT의 사회적 가치 논쟁

본 프로젝트의 직접 주제는 아니지만 맥락상 알아둘 가치:

| 옹호 측 | 비판 측 |
|---------|---------|
| 시장 유동성 공급 | 변동성 증폭 (Flash Crash 사례) |
| 매수/매도 스프레드 축소 | 일반 투자자 대비 비대칭 정보 우위 |
| 시장 효율성 향상 | 사회적 자원의 비생산적 사용 (Aquilina 논문 주장) |

---

## 📌 다음 문서로

본 문서는 HFT 산업의 **개요**를 다뤘다.
구체적인 인프라 사례 (광케이블, 마이크로웨이브, Co-location) 는 [`case_studies.md`](./case_studies.md) 참조.

---

## References

- Aquilina, Budish, O'Neill, *"Quantifying the High-Frequency Trading 'Arms Race',"* QJE, 2022.
- Bhattacherjee et al., *"A Bird's Eye View of the World's Fastest Networks,"* ACM IMC, 2020.
- Lewis, Michael, *Flash Boys: A Wall Street Revolt*, W. W. Norton, 2014.
- SEC, *Concept Release on Equity Market Structure*, 2010.
