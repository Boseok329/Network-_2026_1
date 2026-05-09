# TCP vs UDP 트레이드오프 분석

> 📌 **이 문서의 목적**: TCP와 UDP의 본질적 차이를 Module 2 강의 내용 기반으로 정리하고, HFT 환경에서 각 프로토콜이 어떤 결과를 만드는지 분석한다.
>
> 📚 **출처**: Kurose & Ross 8th ed., Chap. 3 / 강의자료 `CN_Module2_*.pdf`

---

## 1. 두 프로토콜의 핵심 비교

| 측면 | TCP | UDP |
|------|-----|-----|
| 연결 방식 | Connection-oriented | Connectionless |
| 연결 설정 | 3-way handshake (1 RTT) | 없음 |
| 신뢰성 | 보장 (자동 재전송) | 없음 (Best-effort) |
| 순서 보장 | O (Seq # 기반) | X |
| 흐름 제어 | rwnd | 없음 |
| 혼잡 제어 | CWND (감속 가능) | 없음 (풀 속도) |
| 헤더 크기 | **20+ bytes** | **8 bytes** |
| 식별 (Demux) | 4-tuple | 2-tuple |
| 적합 용도 | 파일 전송, 웹 | 실시간, DNS, 게임 |

---

## 2. UDP — 단순함의 미학

### 2.1 헤더 구조 (8 bytes)

| 필드 | 크기 | 의미 |
|------|------|------|
| Source Port | 16 bits | 송신 측 포트 |
| Destination Port | 16 bits | 수신 측 포트 |
| Length | 16 bits | UDP 세그먼트 전체 길이 |
| Checksum | 16 bits | 비트 에러 감지 |

### 2.2 동작 방식

1. 송신자: 데이터에 8 byte 헤더 붙여 IP 계층으로 전달
2. 수신자: 도착하면 `(dst IP, dst port)` 2-tuple로 소켓 매칭, 응용에 전달
3. **손실/중복/순서 어긋남 → 응용 계층 책임**

### 2.3 Demultiplexing (강의 내용)

```
mySocket = socket(AF_INET, SOCK_DGRAM)
mySocket.bind(myaddr, 6428)
# 6428번 포트로 오는 모든 UDP는 이 소켓으로
# 송신자가 누구든 (srcIP, srcPort) 무관
```

→ **2-tuple 매칭** (dstIP, dstPort)

### 2.4 장점

- ✅ **극도로 빠름** (헤더 8B, 핸드셰이크 없음)
- ✅ **예측 가능한 지연** (재전송 메커니즘 없음 → 정상 패킷은 항상 일정)
- ✅ 혼잡 제어 없음 → 원하는 만큼 빠르게 전송 (HFT에 적합)
- ✅ 멀티캐스트 가능 → 시세 데이터 배포에 이상적

### 2.5 단점

- ❌ 손실 시 복구 메커니즘 없음
- ❌ 순서 보장 없음
- ❌ 신뢰성을 응용 계층에서 직접 구현 필요 (잘못 짜면 TCP보다 느림)

---

## 3. TCP — 신뢰성의 대가

### 3.1 헤더 구조 (20+ bytes)

| 필드 | 크기 | 의미 |
|------|------|------|
| Source Port | 16 bits | 송신 포트 |
| Destination Port | 16 bits | 수신 포트 |
| **Sequence Number** | 32 bits | **바이트 단위 시퀀스** |
| **Acknowledgment Number** | 32 bits | **다음 기대 바이트** |
| Header Length | 4 bits | TCP 헤더 길이 |
| Flags (SYN, ACK, FIN, RST...) | 9 bits | 제어 플래그 |
| **Receive Window (rwnd)** | 16 bits | **흐름 제어용 윈도우** |
| Checksum | 16 bits | 에러 감지 |
| Urgent Pointer | 16 bits | 긴급 데이터 |
| Options | 가변 | 추가 기능 |

### 3.2 3-Way Handshake (연결 설정)

```
Client                     Server
  │                           │
  │──────── SYN(x) ─────────→│   ① 연결 요청
  │                           │
  │←─── SYN(y), ACK(x+1) ─────│   ② 응답
  │                           │
  │──── ACK(y+1) [+ data] ───→│   ③ 확인
  │                           │
  │═══════ ESTABLISHED ═══════│
```

> ⚠️ **HFT 영향**: 첫 메시지 전송 전에 **1 RTT 추가 오버헤드** 발생

### 3.3 재전송 메커니즘 (RTO)

#### RTT 추정 (강의 공식)

```
EstimatedRTT = (1 - α) · EstimatedRTT + α · SampleRTT     [α = 0.125]
DevRTT = (1 - β) · DevRTT + β · |SampleRTT - EstimatedRTT|  [β = 0.25]
TimeoutInterval = EstimatedRTT + 4 · DevRTT
```

#### Linux 커널 RTO 최소값

- **RFC 6298** + Linux 구현: `TCP_RTO_MIN = 200ms`
- 위 공식 결과가 200ms 미만이어도 **하한선 200ms**

> ⚠️ **HFT의 fatal weakness**: 정상 RTT가 200µs인 환경에서도 손실 발생 시 200ms 대기. 즉 **1,000배 지연 폭증**.

### 3.4 흐름 제어 (Flow Control)

- 수신자가 자신의 버퍼 여유 공간을 `rwnd` 필드에 광고
- 송신자: in-flight 데이터 ≤ rwnd 유지
- **목적**: 수신자 버퍼 오버플로우 방지

### 3.5 혼잡 제어 (Congestion Control)

- 네트워크 혼잡 감지 시 송신 속도 자동 감속
- AIMD (Additive Increase Multiplicative Decrease)
- **HFT 영향**: 1건 손실 → CWND 절반으로 → 후속 트래픽 전체에 영향

### 3.6 Demultiplexing (강의 내용)

→ **4-tuple 매칭** (srcIP, srcPort, dstIP, dstPort)
- 같은 서버 포트라도 송신자가 다르면 다른 소켓

---

## 4. HFT 환경에서의 트레이드오프

### 4.1 손실 없는 환경

| 측면 | TCP | UDP | 차이 |
|------|-----|-----|------|
| 첫 메시지 지연 | 1 RTT (handshake) + 전송 | 즉시 전송 | **UDP 1 RTT 빠름** |
| 정상 메시지 지연 | ~동일 | ~동일 | 헤더 12B 차이 (미미) |
| 재전송 메커니즘 | 발동 안 함 | 없음 | **차이 없음** |

→ **차이 미미** (손한주 실측: 평균 ~10µs, P99에서는 UDP가 오히려 약간 높음)

### 4.2 손실 1% 환경

| 측면 | TCP | UDP | 차이 |
|------|-----|-----|------|
| 정상 패킷 (99%) | ~동일 | ~동일 | 차이 없음 |
| **손실 패킷 (1%)** | **RTO 200ms+ 후 복구** | **포기** | **TCP 1,000x 느림** |
| **P99 지연** | **~200ms** | **~370µs** | **545x** |
| 신뢰성 | 100% (전체 복구) | 99% (1% 손실) | TCP 우위 |

→ **TCP의 P99 폭등이 핵심 발견** (손한주 실측으로 입증)

### 4.3 HFT에서의 실용적 결론

> "주문 1개 영구 손실" vs "주문 1개 200ms+ 지연" 중 어느 쪽이 더 큰 손해인가?

| 시나리오 | TCP 손실 비용 | UDP 손실 비용 |
|---------|------------|------------|
| 거래 신호 1건 (가격 정보) | 200ms 지연 → 시장 이미 움직임 → **가치 0** | 신호 영구 손실 → **가치 0** |
| 후속 정상 신호들 | TCP의 후속 처리 정체 가능 | 영향 없음 |
| **전체적 손해** | **더 큼 (시스템 전체 영향)** | **국소적** |

→ **HFT에서 UDP가 합리적 선택**

---

## 5. 실제 HFT 시스템의 선택

### 5.1 시세 데이터 배포: UDP 멀티캐스트

- NYSE, NASDAQ, CME 등 대부분의 거래소가 **UDP 멀티캐스트** 사용
- 이유:
  - 한 서버 → 다수 수신자 동시 전달 (TCP 불가능)
  - 손실되어도 다음 시세 업데이트가 곧 옴
  - 일관된 지연 (재전송 없음)

### 5.2 주문 전송: TCP + 응용 계층 보완

- 주문은 **신뢰성도 중요** (잃어버리면 안 됨)
- 하지만 커널 TCP의 RTO 200ms는 부적절
- 해결책:
  - **FPGA 기반 TCP 스택** (커널 우회 + RTO 단축)
  - **응용 계층에서 자체 재전송** (UDP + 자체 ACK)
  - **이중 전송** (한 메시지를 두 경로로 동시에)

### 5.3 본 프로젝트와의 관계

- 본 프로젝트는 **표준 Linux TCP/UDP** 만으로 비교
- 실제 HFT 시스템의 정교한 우회 기법은 [`../protocol/`](../../protocol/) 에서 김정하가 분석
- 그러나 **표준 프로토콜의 본질적 차이**가 이미 545배 영향 → 분석 의의 충분

---

## 6. 본 문서의 핵심 정리

### 6.1 프로토콜 선택은 HFT 시스템의 가장 중요한 설계 결정 중 하나다

- 손실 없는 환경: 차이 미미
- **손실 발생 환경: 545배 차이 (실측)**

### 6.2 TCP의 fatal weakness는 RTO 200ms 하한선이다

- Linux 커널 기본 동작
- 정상 RTT가 µs 단위인 HFT 환경에서 **1,000배 지연 폭증**
- 이것이 본 프로젝트가 "TCP가 HFT에 부적합"을 주장하는 근거

### 6.3 UDP는 "예측 가능한 지연"의 대가로 신뢰성을 포기한다

- HFT 도메인에선 합리적 트레이드오프
- "잃어버린 신호" 보다 "지연된 신호" 가 더 위험

---

## 📌 다음 문서로

본 프로젝트의 **가설(H1, H2, H3)** 과 검증 방법론은 [`../03_hypothesis/why_protocol_matters.md`](../03_hypothesis/why_protocol_matters.md) 참조.

---

## References

- Kurose & Ross, 8th ed., Sec. 3.3 (UDP), Sec. 3.4 (RDT), Sec. 3.5 (TCP)
- 강의자료: `CN_Module2_Session1_mux.pdf`, `CN_Module2_Session5_RDT.pdf`, `CN_Module2_Session6_TCP_WithQuiz.pdf`
- IETF RFC 793, *Transmission Control Protocol*, 1981
- IETF RFC 6298, *Computing TCP's Retransmission Timer*, 2011
- IETF RFC 768, *User Datagram Protocol*, 1980
