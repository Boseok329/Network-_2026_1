[README.md](https://github.com/user-attachments/files/28067575/README.md)
# HFT_problem_and_delay_analysis

# HFT 네트워크 지연 문제 정의 — 큐잉·처리 지연이 핵심인 이유<img width="779" height="440" alt="image" src="https://github.com/user-attachments/assets/18a80197-eb8c-4258-a4ca-add800ffc453" />


> **컴퓨터 네트워크 Module 5 — Group 07Problem Lead: 김보석 (Kim Boseok)**
> 
> 
> 본 문서는 HFT(High-Frequency Trading) 환경에서 네트워크 지연이 어떻게 발생하고,
> 4가지 지연 요소 중 **큐잉 지연(d_queue)과 처리 지연(d_proc)** 이 왜 학부 프로젝트에서
> 다룰 가치가 있는 핵심 영역인지 이론적으로 정의한다.
> 

---

## 목차

---

## 1. HFT란 무엇이고 왜 속도를 중요하게 여기는가

### 1.1 정의

**High-Frequency Trading (HFT, 고빈도 거래)** 은 사람이 아닌 알고리즘이 매수/매도 의사결정을 내리고, 1초당 수천~수만 건의 주문을 매우 빠른 속도인 µs(마이크로초) 단위로 처리하는 자동매매 방식이다. 시스템 설계의 모든 결정이 **지연 최소화**에 중점을 둔다는 점에서 일반 거래와 차이가 있다.

### 1.2 산업 규모

- 미국 주식 시장 거래량의 **약 50%** 가 HFT에 의해 발생
- 약  **1ms 단축이 일일 수익 약 100만~수백만 달러** 증가에 기여 [3]

### 1.3 왜 속도를 높이기 위해 경쟁하는가 — 승자 독식 구조

가격 변동이 발생하는 순간 첫 번째로 도착한 주문만 수익을 독점하는 구조이다. 1µs 늦으면 다른 봇이 그 가격을 이미 가져간다. 핵심은 평균 지연이 아니라 실패할 확률인 Tail Latency (P99, P99.9) 이다. 평균이 100µs라도 한번이라도 200ms가 나오면, 평균이 아무리 좋아도 사실상 사용 불가능한 신호가 된다.

> HFT는 평균이 아니라 꼬리가 시스템을 결정한다. 본 프로젝트가 평균 RTT보다 P99에 주목하는 이유.
> 

---

## 2.  지연문제

### 2.1 가장 돈이 몰리는 시간에 지연이 발생한다.

1. **시장 변동성 폭발** (FOMC 발표, 실적 시즌, 지정학적 이벤트) → 차익거래 기회 폭발
2. **모든 알고리즘 주문 폭증** → 네트워크 트래픽 과도→ 큐잉 지연 폭발 + 패킷 손실 가능성 증가

즉 수익 기회와 시스템 부담이 비례한다. 

### 2.2 실제 사례: Flash Crash (2014)

- 거래 폭주 발새
- 일부 거래소 시스템에서 큐잉 지연 급증 → 호가 정보 지연 도달
- 주문이처리되지 못하고 밀려 있는 상태로 시장이 마비됨
- 미 국채 10년물 금리 **10여 분 만에 33~34bp 급락 후 곧바로 전액 회복** [1]

---

## 3. 왜 d_queue와 d_proc이 핵심인 이유

4가지 중 큐잉·처리 지연에 집중하는 이유

### 3.1 통제가 가능한 변수만 의미 있다.

| 지연 | 통제 수단 | 프로젝트 적합성 |
| --- | --- | --- |
| `d_prop` | 거리 단축 — Co-location, 직선 광케이블, 마이크로웨이브 | 인프라/부동산 영역이기에 상수 취급 |
| `d_trans` | 빠른 인터넷 속도— 10/40/100 GbE | 인터넷 속도만 빠르면 되기에 상수 취급 |
| `d_proc` | 커널 바이패스 (DPDK, OpenOnload), FPGA | 분석 가능하지만 어려움 |
| **`d_queue`** | **프로토콜 선택, QoS, 버퍼 관리** | **코드와 이론이 직접 만나는 지점** |

`d_prop`은 빛의 속도가 절대 상한선이며 코드로는 줄일 수 없다. `d_trans`는 개인이 통제하기 어렵기에 상수취급한다. 반면 `d_proc`과 `d_queue`는 **소프트웨어 계층의 선택이 직접적으로 영향**을 미치는 부분.

### 3.2 d_queue — 비선형 폭발의 영역

큐잉 지연이 핵심인 결정적 이유는 **비선형성**이다. 트래픽 강도 ρ가 1에 가까워질 때 평균 큐잉 지연은 M/M/1 큐 모델 기준 다음과 같이 행동한다:

```
E[W] ≈ ρ / (1 - ρ) × (L / R)
```

![image.png](image.png)

[CN_Module1_Session1_overview]

강의자료의 내용 La/R > 1: more “work” arriving is more than can be serviced - average delay infinite! 처럼 0에 가까울 때에는 지연이 매우 작다가 1에 가까우면 지연이 무한에 가까워진다

> 핵심 통찰: d_queue는 평균이 작아도 분산이 매우 크다. **평균이 µs인 시스템이 지연으로  ms~s까지 느려지는 영역**이 큐잉 지연이며, 해당 부분이  Tail Latency (P99, P99.9) 이다.
> 

---

## 4. 결론

본 문서의 주장을 세 줄로 요약하면:

1. **HFT의 본질적 약점은 “평균 지연”이 아니라 “변동성 시즌의 꼬리 폭발”이다.** 평균이 µs인 시스템이 P99에서 ms로 튀는 순간 시스템 신뢰도가 무너진다.
2. **Tail Latency를 만드는 원인이 d_queue + d_proc이다.** d_prop와 d_trans는 개인이 해결하기 어렵기 때문에 상수 취급하고, . **d_queue + d_proc가**  통제할 수 있는 영역이기 때문에  RTT의 ~95% 이상을 차지한다.
3. **그러므로 프로토콜 선택(TCP vs UDP)이 HFT 시스템의 운명을 결정한다.** 두 프로토콜의 본질적 차이는 손실이 없을 때는 미미하지만, ρ→1에서 손실이 발생하는 순간 비대칭적으로 벌어진다. 이 비대칭이 실제 거래소가 시세 데이터에 UDP 멀티캐스트를 채택하는 이유이다.

---

## 첨부 자료

- **코드**: `delay_simulator.py` — 4가지 지연 계산기 + ρ에 따른 d_queue 폭발 시각화
- **그래프**: 코드 실행 시 자동 생성 (`delay_analysis.png`)
- **개인 학업 연구**: [`UDP_security_tradeoff.md`](./UDP_security_tradeoff.md) — UDP 채택으로 발생하는 보안 위협 (개인정보보호 진로 연결)

---

## References

[1] M. Aquilina, E. Budish, P. O’Neill, “*“Quantifying the High-Frequency Trading ‘Arms Race’,”* The Quarterly Journal of Economics, Vol. 137, No. 1, 2022.

---

## 팀 작업 흐름

```
[김보석 — Problem Lead]  본 문서: HFT 도메인 + 4대 지연 + d_queue·d_proc 핵심 이유
         │
         ▼
[손한주 — Simulation Lead]  Docker + tc netem 실측 (TCP/UDP 비교)
         │
         ▼
[김정하 — Protocol Lead]  d_proc 절감 기법 (DPDK, OpenOnload, RDMA) 심층 분석
         │
         ▼
[이준서 — Industry Lead]  실제 산업 사례 (NYSE, CME, Cisco, AWS) 매핑
```

---

> **김보석 (Problem Lead)** | DCCS307 Computer Networks | Module 5 Group 07 | 2026
>
