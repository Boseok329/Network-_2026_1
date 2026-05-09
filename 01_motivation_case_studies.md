# HFT 인프라 사례 연구 (Case Studies)

>  **이 문서의 목적**: HFT 회사들이 실제로 어떻게 µs 단위 지연을 줄여왔는지를 구체적 사례로 보여준다. 각 사례는 [`four_delays_theory.md`](../02_problem_definition/four_delays_theory.md) 의 4대 지연 중 어느 것을 줄였는지 매핑한다.

---

## Case 1: Spread Networks — 시카고 ↔ 뉴욕 직선 광케이블 (2010)

### 배경

- **거래 동기**: 시카고 상품거래소(CME) 의 선물 가격과 뉴욕 NYSE의 주식 가격 사이 차익거래
- 기존 광케이블은 도로/철도를 따라 우회(약 1,330km) → 13.1ms RTT

### 인프라 투자

- 시카고 ↔ 뉴저지 **직선 약 1,300km** 광케이블 신규 건설
- 산, 강, 도시를 관통하는 직선 경로 → 토지 수용 + 굴착 비용 약 **3억 달러**
- 결과: RTT **13.1ms → 13.0ms** (단 100µs 단축)

### 줄인 지연 요소

- ✅ **d_prop (전파 지연)**: 거리 d 자체를 단축
- 다른 요소(d_proc, d_queue, d_trans)는 변화 없음

### 비즈니스 모델

- HFT 회사들에 회선 임대 (한 회사당 연 수천만 달러)
- 고객사들은 임대료를 부담하더라도 100µs 우위로 충분히 회수

### 시사점

- µs 단위 단축에 수억 달러를 투자하는 HFT 산업의 본질을 보여줌
- 그러나 곧 **마이크로웨이브 네트워크에 의해 도태됨** (다음 사례)

---

## Case 2: Microwave Networks — 광속의 99% (2012~)

### 배경

- 빛은 진공에서 약 **3 × 10⁸ m/s** 로 이동
- 광케이블 안에서는 굴절률 때문에 **약 2 × 10⁸ m/s** 로 감소 (광속의 67%)
- 무선 마이크로웨이브는 공기 중에서 거의 **광속 그대로** 이동

### 인프라

- 시카고 ↔ 뉴욕 사이에 **약 30~40개의 마이크로웨이브 송수신탑** 건설
- 각 탑은 시야선(Line-of-Sight) 으로 직접 통신
- 결과: RTT 광케이블 6.65ms → **마이크로웨이브 4.13ms** (약 38% 단축)

### 줄인 지연 요소

- ✅ **d_prop (전파 지연)**: 매체의 전파 속도 s 향상

### 한계와 트레이드오프

| 측면 | 광케이블 | 마이크로웨이브 |
|------|---------|--------------|
| 속도 | 광속의 67% | 광속의 99% |
| 대역폭 | 매우 높음 (Tbps) | 낮음 (Mbps~수 Gbps) |
| 안정성 | 매우 안정 | 비/안개에 약함 |
| 거리 한계 | 무제한 | 시야선 한계 (탑 간 ~70km) |
| 용도 | 대용량 데이터 | **HFT 거래 신호만** (작은 패킷) |

> 💡 **HFT 거래 메시지가 작기 때문에** (수십 byte) 마이크로웨이브의 낮은 대역폭이 문제 안 됨

### 시사점

- d_prop의 본질적 한계(광속) 안에서도 **매체 선택** 으로 추가 단축 가능
- 다만 비/날씨에 약하므로 광케이블을 백업으로 함께 운영

---

## Case 3: Co-location — d_prop을 ~0으로

### 배경

- 거래소(NYSE, NASDAQ, CME) 가 자기 데이터센터에 **HFT 회사의 서버를 임대 입주** 시키는 서비스
- 거래소 매칭 엔진과 HFT 서버가 **같은 건물, 같은 층** 에 있음

### 주요 거래소 Co-lo 시설

| 거래소 | 위치 | 임대료 (캐비닛 1개) |
|--------|------|------------------|
| NYSE Mahwah | New Jersey, USA | 월 ~$10,000~ |
| NASDAQ Carteret | New Jersey, USA | 월 ~$10,000~ |
| CME Aurora | Illinois, USA | 월 ~$10,000~ |
| LSE Slough | London, UK | 월 ~£10,000~ |

### 줄인 지연 요소

- ✅ **d_prop (전파 지연)**: 거리 d를 **수백 m → 수 m로 축소**
  - 일반 백오피스 ↔ 거래소: ~수 ms
  - Co-lo: ~수십 µs
- ✅ **공정성 보장**: 같은 거래소 내 모든 Co-lo 입주사는 매칭 엔진까지 **같은 길이 케이블** (cross-connect 길이 통제)

### 시사점

- **모든 회사가 Co-lo를 쓰면 → 다시 동등한 시작점** → 다른 차원의 경쟁 시작 (FPGA, 알고리즘 등)
- 본 프로젝트의 Docker 격리 환경은 이 Co-lo 환경을 **단순화하여 모방** 한 것

---

## Case 4: Hibernia Express — 대서양 횡단 케이블 (2015)

### 배경

- 뉴욕 ↔ 런던 거래 (NYSE ↔ LSE)
- 기존 케이블은 우회 경로 → ~65ms RTT

### 인프라 투자

- 대서양 해저 직선 광케이블 약 **5,000km**
- 투자액 **약 3억 달러**
- 결과: RTT **65ms → 59ms** (약 6ms 단축)

### 줄인 지연 요소

- ✅ **d_prop (전파 지연)**: 거리 d 단축

### 시사점

- 대륙 간에서도 µs 단축이 사업화 가능한 시장임을 보여줌
- 6ms 단축에 3억 달러 → ms당 **5,000만 달러의 가치**

---

## Case 5: FPGA / Kernel Bypass — 호스트 내부 µs 절감 (2010s~)

### 배경

- 위 사례들은 모두 d_prop을 줄였지만, **호스트 내부 처리 시간(d_proc)** 도 µs 단위 영향
- 일반 Linux 서버에서 패킷이 NIC → 커널 → 사용자 공간 도달까지 **수십 µs** 소요

### 기술 스택

| 기술 | 작동 원리 | 절감 효과 |
|------|---------|---------|
| **DPDK** | 사용자 공간이 NIC를 직접 polling, 커널 우회 | ~10µs → ~1µs |
| **Solarflare OpenOnload** | TCP 스택을 사용자 공간에 구현 | 커널 TCP 대비 ~5x 빠름 |
| **RDMA (RoCE)** | NIC가 원격 메모리에 직접 접근, CPU 거의 미사용 | 1µs 미만 도달 가능 |
| **FPGA NIC** | TCP/UDP 처리 자체를 하드웨어에 구현 | 100ns 미만 도달 가능 |

### 줄인 지연 요소

- ✅ **d_proc (처리 지연)**: 커널, 컨텍스트 스위치, 인터럽트 비용 제거
- 일부는 **d_queue도 회피** (busy-polling으로 큐 자체를 안 씀)

### 시사점

- 김정하 (Protocol Lead) 가 [`../protocol/`](../../protocol/) 에서 깊이 분석할 영역
- d_prop 단축이 한계에 도달한 이후 HFT 군비경쟁의 새 전선

---

## Case 6: Flash Crash (2010.05.06) — 지연/부하의 위험성

### 사건 개요

- 2010년 5월 6일 14:42, **불과 36분 만에 미국 주식 시장 시가총액 약 1조 달러 증발 후 회복**
- 다우존스 -9% 폭락 후 빠르게 회복
- HFT 봇 간 연쇄 매도가 주된 원인 중 하나

### 네트워크 측면 분석

- 이벤트 시점 거래량 평소의 약 5배 → **트래픽 강도 La/R 폭발**
- 일부 거래소 시스템에서 큐잉 지연 폭증 → **호가 정보 지연 도달**
- HFT 봇들이 정확한 가격을 보지 못한 채 매도 → 연쇄 효과

### 시사점

- HFT의 **fatal weakness가 실제로 발현된 사례**
- "정상 환경에서는 빠르지만 위기 상황에서 가장 느려진다" → 본 프로젝트의 핵심 문제 제기
- 본 프로젝트의 시나리오 D (손실 1%) 가 모방하는 환경

---

##  사례별 지연 요소 매핑 요약

| 사례 | d_proc | d_queue | d_trans | d_prop |
|------|:------:|:-------:|:-------:|:------:|
| Spread Networks (직선 광케이블) | | | | ✅ |
| Microwave Network | | | | ✅✅ |
| Co-location | | | | ✅✅✅ |
| Hibernia Express | | | | ✅ |
| DPDK / RDMA / FPGA | ✅✅✅ | ✅ | | |
| **본 프로젝트의 분석 대상** | | **✅** | | |

>  본 프로젝트는 **d_queue + 손실 발생 시 프로토콜의 복구 메커니즘** 에 집중. 위 사례 어디에도 단독으로 다뤄지지 않은 영역.

---

## References

- Bhattacherjee et al., *"A Bird's Eye View of the World's Fastest Networks,"* ACM IMC, 2020.
- Laughlin, Aguirre, Grundfest, *"Information Transmission Between Financial Markets in Chicago and New York,"* Financial Review, 2014.
- Lewis, Michael, *Flash Boys: A Wall Street Revolt*, W. W. Norton, 2014.
- CFTC-SEC, *Findings Regarding the Market Events of May 6, 2010* (Flash Crash 보고서)
- Lockwood et al., *"A Low-Latency Library in FPGA Hardware for High-Frequency Trading,"* IEEE, 2012.
