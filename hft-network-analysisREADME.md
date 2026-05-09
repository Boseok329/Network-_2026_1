# 🚀 HFT 네트워크 지연 문제 정의 (Problem Definition)

> **컴퓨터 네트워크 Module 5 — Group 07**
> Problem Lead: 김보석 (Kim Boseok)
> 본 문서는 HFT(High-Frequency Trading) 도메인에서 네트워크 지연이 왜 치명적인지,
> 그리고 그 지연이 어디서 발생하는지를 **이론적으로 정의**하는 문서입니다.
> 시뮬레이션 결과는 [팀원 손한주의 벤치마크 결과](../simulation/) 참고.

---

## 📌 목차

1. [HFT란 무엇이고 왜 µs를 다투는가](#1-hft란-무엇이고-왜-µs를-다투는가)
2. [HFT의 Fatal Weakness — 지연(Latency)](#2-hft의-fatal-weakness--지연latency)
3. [네트워크 지연의 4가지 원인](#3-네트워크-지연의-4가지-원인)
4. [HFT 환경에서 각 지연이 갖는 의미](#4-hft-환경에서-각-지연이-갖는-의미)
5. [왜 전송 계층 프로토콜 선택이 핵심인가](#5-왜-전송-계층-프로토콜-선택이-핵심인가)
6. [우리 팀의 가설과 검증 흐름](#6-우리-팀의-가설과-검증-흐름)

---

## 1. HFT란 무엇이고 왜 µs를 다투는가

### 정의

**High-Frequency Trading (HFT, 고빈도 거래)** 는 알고리즘이 자동으로 µs(마이크로초) ~ ms(밀리초) 단위로 수천~수만 건의 거래를 체결하는 자동매매 방식이다. 사람이 개입하지 않으며, 거래의 핵심 자원은 **속도(Speed)** 이다.

### 주요 전략

- **Arbitrage (차익거래)**: 거래소 A와 B의 동일 자산 가격 차이를 즉시 포착해 차익 실현
- **Market Making (시장 조성)**: 매수/매도 호가를 동시에 걸어 스프레드 수익 확보
- **Statistical Arbitrage**: 통계 모델 기반 단기 가격 예측

### 산업 영향

- 미국 주식 시장 거래량의 약 50% 가 HFT에 의해 발생
- 단 1ms 의 우위 확보를 위해 글로벌 금융사들이 **수억 달러 규모의 인프라 투자** 진행

### 대표 사례

| 사례 | 내용 | 지연 단축 효과 |
|------|------|---------------|
| Spread Networks (2010) | 시카고 ↔ 뉴욕 간 직선 광케이블 | 13.1ms → 13.0ms (~$300M 투자) |
| 마이크로웨이브 네트워크 (2012~) | 동일 구간 무선 직선 전송 | ~6.65ms → ~4.13ms (광속의 99%) |
| Co-location | 거래소 서버 바로 옆에 자기 서버 배치 | propagation 지연을 ~0에 근접 |

> 💡 **Key Insight**: HFT 인프라 투자의 본질은 "지연을 1µs라도 더 줄이는 것"이며, 이는 곧 수익으로 직결된다.

---

## 2. HFT의 Fatal Weakness — 지연(Latency)

### Speed → Money

시장 가격 변동이 발생하는 순간, **첫 번째로 도착한 주문이 수익을 독점**한다.
1µs 늦으면 다른 봇이 이미 그 가격을 가져갔다 — "Loser's Market" 구조.

### Tail Latency가 진짜 적

평균 지연(Mean)이 좋아도 **P99/P99.9 (상위 1% 꼬리 지연)** 가 나쁘면 시스템 신뢰도가 파괴된다.

- 100만 건 거래 중 1%인 **1만 건이 200ms 지연** → 1만 건의 거래 기회 상실
- 평균이 100µs라도 P99가 200ms면 → 시스템은 사실상 못 쓰는 수준

> 📊 손한주의 실측에서 **TCP P99가 손실 1% 환경에서 375µs → 205ms (545배 폭등)** 한 것이 정확히 이 현상이다.

### 변동성 높을 때 가장 위험

- FOMC 발표, 실적 시즌 등 → 시장 변동성 폭발 → 트래픽 폭발 → 큐잉 지연 폭발
- **정작 가장 돈이 되는 순간에 시스템이 가장 느려진다** = HFT의 본질적 딜레마

---

## 3. 네트워크 지연의 4가지 원인

> 📚 [Kurose & Ross 8th ed., Module 1] 강의에서 배운 4대 지연 요소를 HFT 관점에서 재해석.

### 전체 지연 공식

```
d_total = d_proc + d_queue + d_trans + d_prop
```

| 지연 | 정의 | 공식 | 일반 환경 |
|------|------|------|---------|
| **Processing** (d_proc) | 비트 에러 체크 + 출력 링크 결정 | < 1µs | 무시 가능 |
| **Queueing** (d_queue) | 출력 버퍼에서 전송 대기 | f(La/R) | 가장 가변적 |
| **Transmission** (d_trans) | 패킷을 링크에 밀어넣는 시간 | L / R | 링크/패킷 의존 |
| **Propagation** (d_prop) | 신호가 매체를 이동하는 시간 | d / s | 거리에 비례 |

- L: 패킷 길이 (bits)
- R: 링크 대역폭 (bps)
- d: 물리적 거리 (m)
- s: 전파 속도 (≈ 2 × 10⁸ m/s)

### 트래픽 강도와 패킷 손실

```
Traffic Intensity = L · a / R
```
- a: 평균 패킷 도착률 (packets/sec)

- **La/R ≈ 0**: 큐잉 지연 거의 없음
- **La/R → 1**: 큐잉 지연 **폭발적 증가**
- **La/R > 1**: 큐가 무한대로 커짐 → **패킷 드롭(Loss) 발생**

> ⚠️ HFT에서 시장 변동성이 폭발할 때 정확히 La/R > 1 상태에 진입한다. 즉 **HFT는 "필요한 순간에 가장 손실이 잘 나는" 환경**.

---

## 4. HFT 환경에서 각 지연이 갖는 의미

각 지연 요소가 HFT에서 어떤 의미를 갖고, 어떻게 줄일 수 있는지 정리한다.

### 4.1 d_prop (전파 지연) — 물리 법칙의 한계

- 광속(c) 자체가 상한선 → **코드로는 절대 줄일 수 없음**
- NY ↔ Chicago: 광케이블 ~6.65ms / 마이크로웨이브 직선 ~4.13ms
- **해결책**: Co-location (거리 d 자체를 줄임), Microwave (전파 속도 s를 광케이블 대비 ~50% 향상)

> 🚫 본 프로젝트의 코드 영역 밖 — 인프라/부동산 문제

### 4.2 d_proc (처리 지연) — 커널 오버헤드

- OS 커널의 TCP 스택, 인터럽트 처리, 컨텍스트 스위치에서 µs 단위 누적
- 일반 환경에선 무시되지만, HFT에선 누적되면 결정적 차이
- **해결책**: Kernel Bypass (DPDK, Solarflare OpenOnload, RDMA)
  - 패킷이 OS 커널을 거치지 않고 NIC ↔ 사용자 공간 직접 전달

> 🔬 김정하 (Protocol Lead) 분량으로 분석 예정

### 4.3 d_trans (전송 지연) — 대역폭 문제

- HFT 거래 메시지는 매우 작음 (수십~수백 byte)
- 10/40/100 GbE NIC 사용 시 d_trans는 거의 무시 가능
- **해결책**: 빠른 NIC 사용 (이미 해결된 영역)

> ✅ 본 프로젝트에서 큰 변수 아님

### 4.4 d_queue (큐잉 지연) — 가장 변동성 큰 적

- 트래픽 폭발 시 라우터/NIC 큐가 차오름 → 지연 폭발
- 큐가 가득 차면 → **패킷 드롭** → **프로토콜 복구 메커니즘 발동**
- **TCP**: 자동 재전송 (RTO 타이머, Linux 기본 200ms 최소)
- **UDP**: 복구 없음, 손실된 패킷은 그대로 폐기

> ⭐ **여기가 본 프로젝트의 진짜 타겟**

---

## 5. 왜 전송 계층 프로토콜 선택이 핵심인가

### 5.1 우리가 통제할 수 있는 영역 정리

| 지연 요소 | 통제 가능성 | 이유 |
|----------|-----------|------|
| d_prop | ❌ | 빛의 속도 한계 |
| d_proc | △ | 부분적 (커널 바이패스) |
| d_trans | ✅ (이미 해결) | 빠른 NIC |
| **d_queue + 손실 복구** | ✅ **핵심 통제 지점** | **프로토콜 계층 결정** |

### 5.2 TCP vs UDP — Module 2에서 배운 본질적 차이

| 측면 | TCP | UDP |
|------|-----|-----|
| 연결 방식 | Connection-oriented (3-way handshake) | Connectionless |
| 손실 시 복구 | 자동 재전송 (RTO 타이머) | 없음 (애플리케이션 책임) |
| 순서 보장 | O | X |
| 흐름 제어 | rwnd | 없음 |
| 혼잡 제어 | CWND | 없음 |
| 헤더 크기 | 20+ bytes | 8 bytes |

### 5.3 HFT 관점의 결정적 차이

- **TCP RTO**: 손실 발생 시 ACK 대기 후 재전송. **Linux 커널 RTO 최소값 = 200ms**
  → 손실 1건이 곧 200ms+ 지연
- **UDP**: 손실 발생 시 그냥 포기. 다음 거래 신호로 즉시 진행
  → 정상 패킷의 지연은 일정하게 유지됨

> 💡 **HFT 도메인 특성**: 200ms 늦게 도착한 거래 신호는 **이미 가치가 0** (시장이 움직였음)
> 차라리 **그 신호를 포기하고 새 신호를 보내는 게 합리적** → UDP 선호의 근본 이유

---

## 6. 우리 팀의 가설과 검증 흐름

### 6.1 핵심 가설

> **H1**: 패킷 손실이 없는 환경에서는 TCP와 UDP의 지연 차이가 미미할 것이다 (헤더 오버헤드 차이만 반영).
>
> **H2**: 패킷 손실이 발생하는 환경에서는 TCP가 RTO 메커니즘으로 인해 P99 지연이 200ms+ 단위로 폭등하지만, UDP는 정상 패킷의 지연을 유지할 것이다.
>
> **H3**: 따라서 HFT 환경에서는 **신뢰성(TCP) vs 예측 가능한 지연시간(UDP)** 의 트레이드오프가 발생하며, 도메인 특성상 UDP가 합리적 선택이 된다.

### 6.2 검증 흐름

```
[보석] 이론적 문제 정의 (이 문서)
         │
         ▼
[한주] Docker 격리 환경에서 tc netem 으로 손실 주입 후 TCP/UDP 실측
         │
         ▼
[정하] 결과의 프로토콜 레벨 원인 분석 (RTO, CWND, kernel bypass 대안)
         │
         ▼
[준서] 실제 산업 사례와 매핑 (NYSE, CME, FPGA, RDMA 도입 사례)
```

### 6.3 가설 검증 결과 (손한주 실측 결과 요약)

| 시나리오 | TCP P99 | UDP P99 | 차이 | 가설 일치 |
|---------|---------|---------|------|---------|
| Baseline (무손실) | 375.7 µs | 386.1 µs | +10 µs | ✅ H1 입증 |
| Loss 1% | **204,812 µs** | **374.5 µs** | **545×** | ✅ H2 입증 |
| Loss 5% | > 400 ms | ~395 µs | 1000×+ | ✅ H2 강화 |

→ **이론 예측이 정량적으로 검증됨**: TCP의 200ms RTO 메커니즘이 HFT의 fatal weakness가 됨을 실측으로 확인

---

## 📚 References

[1] Lockwood et al., *"A Low-Latency Library in FPGA Hardware for High-Frequency Trading,"* IEEE Symposium on High-Performance Interconnects, 2012.
[2] Bhattacherjee et al., *"A Bird's Eye View of the World's Fastest Networks,"* ACM Internet Measurement Conference (IMC), 2020.
[3] Aquilina, Budish, O'Neill, *"Quantifying the High-Frequency Trading 'Arms Race',"* The Quarterly Journal of Economics, 2022.
[4] Laughlin, Aguirre, Grundfest, *"Information Transmission Between Financial Markets in Chicago and New York,"* Financial Review, 2014.
[5] Kurose & Ross, *"Computer Networking: A Top-Down Approach,"* 8th ed.
[6] J. Postel, *"Transmission Control Protocol,"* IETF RFC 793, 1981.

---

## 🔗 팀 분석 링크

- **[Simulation 분석](../simulation/)** — 손한주 (Docker 환경 + tc netem 실측)
- **[Protocol 분석](../protocol/)** — 김정하 (DPDK / OpenOnload / RDMA 심층 분석)
- **[Industry 사례](../industry/)** — 이준서 (NYSE / CME / Cisco / AWS 사례)

---

> **김보석 (Problem Lead)** | 컴퓨터 네트워크 DCCS307 | 2026
