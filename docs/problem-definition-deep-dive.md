# Problem Definition — Deep Dive

**Boseok Kim (Problem Lead) · DCCS307 Computer Networks · Module 5, Group 07**

This is the long version of the problem definition summarized in the
[main README](../README.md). It works through the four delays formally, derives
why queueing delay is the one that explodes, compares TCP and UDP at the
mechanism level, and states the hypotheses our measurement tested. It is the
research I did to decide what the project should actually be about.

---

## 1. The delay budget

A packet crossing one hop pays four delays (Kurose & Ross, Ch. 1.4):

```
d_total = d_proc + d_queue + d_trans + d_prop
```

End to end, that sum runs over every hop on the path:

```
d_e2e = Σ_i (d_proc,i + d_queue,i + d_trans,i + d_prop,i)
```

The project's first job was to decide which of these four is worth a student's
attention. The test I used: *can a software decision change it, and does it
matter in the environment we care about (short distance, microsecond scale)?*

### 1.1 Propagation delay — `d_prop = d / s`

The time for the signal to travel the medium. `d` is distance, `s` is
propagation speed: about 2×10⁸ m/s in fibre (≈67% of c), close to c in air for
microwave.

| Distance | `d_prop` (fibre) |
|---|---|
| 1 m (inside a co-lo rack) | 5 ns |
| 1 km (within a city) | 5 µs |
| 1,300 km (Chicago–New York, straight) | ~6.5 ms |

This is bounded by physics. You reduce it only by reducing `d` (co-location, a
straighter cable) or raising `s` (microwave instead of fibre). No code touches
it. Over long distances it dominates everything — Chicago–New York is ~99%
`d_prop` — which is why HFT infrastructure spends hundreds of millions on
straight fibre and microwave towers. None of that is a networking-course
problem, so the project treats `d_prop` as a constant.

### 1.2 Transmission delay — `d_trans = L / R`

The time to clock all `L` bits of the packet onto a link of rate `R`.

| Packet | Link | `d_trans` |
|---|---|---|
| 64 B (an order message) | 1 Gbps | 0.51 µs |
| 64 B | 10 Gbps | 0.051 µs |
| 1500 B (a full MTU) | 1 Gbps | 12 µs |

HFT messages are tiny (tens of bytes) and 10/40/100 GbE NICs are standard, so
`d_trans` is tens of nanoseconds. It is "solved by buying the right card."
Constant for our purposes.

### 1.3 Processing delay — `d_proc`

Header/checksum validation, forwarding-table lookup, and on a host the entire
journey through the OS network stack. The textbook calls it "typically
negligible" (< 1 µs on a router), but on a host it is mostly kernel overhead and
it accumulates:

- interrupt handling per packet,
- copies from NIC ring → kernel buffer → user buffer,
- a context switch on every system call (register + TLB churn),
- the TCP state machine, congestion control, scheduling.

A standard round trip enters the kernel twice and pays roughly 20–60 µs for it.
This *is* reducible by software — kernel bypass (DPDK, OpenOnload, RDMA) skips
the stack and brings it toward 1 µs. That made `d_proc` a real target, and it
became my teammate Jeongha's part. The project's own measurement, in Python,
includes this overhead in its baseline, which is why our clean RTT is ~180 µs
rather than the single-digit microseconds a C++/DPDK system would show — the
*relative* TCP-vs-UDP gap is what survives the difference.

### 1.4 Queueing delay — `d_queue`

Time spent waiting in the output buffer for the link to free up. Unlike the
other three it has no fixed size: it runs from zero to unbounded depending on
load, and when the buffer fills it turns into packet loss. This is the one the
project is really about, so it gets its own section.

| Delay | Software-controllable? | In this project |
|---|---|---|
| `d_prop` | No (physics) | constant; explained, not analysed |
| `d_trans` | No (already solved) | constant |
| `d_proc` | Partly (kernel bypass) | Jeongha (Protocol Lead) |
| **`d_queue` + loss recovery** | **Yes (protocol choice)** | **the main target** |

## 2. Why queueing delay explodes

### 2.1 Traffic intensity

Define traffic intensity as

```
ρ = L · a / R
```

with `L` the mean packet size in bits, `a` the mean arrival rate in packets/s,
and `R` the link rate in bits/s. So `La` is the arrival bit-rate and `ρ` is
arrival rate over service rate — a dimensionless ratio.

- `ρ ≈ 0`: packets find an empty queue and leave immediately.
- `ρ < 1`: some waiting, finite.
- `ρ → 1`: average queueing delay grows without bound.
- `ρ > 1`: arrivals outrun service, the queue grows forever, and a finite buffer
  overflows — packets are dropped.

### 2.2 The M/M/1 result

For an M/M/1 queue the mean waiting time is

```
E[w] = ρ / (1 − ρ) · (L / R)
```

Look at the `1 − ρ` denominator:

| ρ | `E[w]` in units of `L/R` |
|---|---|
| 0.5 | 1 |
| 0.9 | 9 |
| 0.95 | 19 |
| 0.99 | 99 |
| 0.999 | 999 |

Going from a normal load of ρ=0.7 to ρ=0.95 — not even close to saturation —
multiplies the average wait by about 8×, and the curve keeps steepening.
`delay_simulator.py` plots this as Figure 1 in the README. It is the same shape
as the course slide for `La/R → 1`.

The key property for HFT is not the average, though — it is the variance. Even
when `E[w]` is small, the distribution has a long right tail, and that tail is
exactly the P99/P99.9 that decides whether a trading system wins or loses races.
A system that averages microseconds can still spend milliseconds in the queue on
its worst 1% of packets.

### 2.3 Why HFT lands on the steep part at the worst time

HFT traffic is bursty, and the bursts line up with the money. A scheduled
event — an FOMC decision, an earnings release, a geopolitical shock — does two
things at once:

1. It creates the arbitrage opportunity (prices move).
2. It makes every algorithm submit and cancel at once, so `a` spikes and ρ jumps
   toward 1.

The result is structural: the system is slowest, and most likely to drop
packets, at precisely the moments being fast is worth the most. The 15 October
2014 US Treasury flash event is the documented version of this — record volume,
6–10× average, a 16 bp round trip in twelve minutes, and a five-agency report
that found no single cause (see README §3, Joint Staff Report). A market hitting
the steep part of the curve, with no fat finger required.

## 3. After the drop: TCP vs UDP

Once ρ>1 forces a loss, recovery is the transport layer's job, and this is where
the two protocols stop being interchangeable.

### 3.1 The two designs

| | TCP | UDP |
|---|---|---|
| Connection | 3-way handshake (1 RTT setup) | connectionless |
| Loss recovery | automatic retransmit (RTO timer) | none — application's problem |
| Ordering | yes (sequence numbers) | no |
| Flow control | yes (`rwnd`) | no |
| Congestion control | yes (AIMD on `cwnd`) | no |
| Header | 20+ bytes | 8 bytes |

### 3.2 The mechanism that matters: RTO

TCP cannot notice a lost packet faster than its retransmission timeout. The
timeout is estimated from measured RTT:

```
EstimatedRTT = (1−α)·EstimatedRTT + α·SampleRTT        (α = 1/8)
DevRTT       = (1−β)·DevRTT + β·|SampleRTT − EstimatedRTT|   (β = 1/4)
TimeoutInterval = EstimatedRTT + 4·DevRTT
```

but it is floored. Linux sets `TCP_RTO_MIN = HZ/5 = 200 ms` in
`include/net/tcp.h` — a deliberate choice below RFC 6298's recommended
one-second minimum, but still enormous next to a ~180 µs clean RTT. So a single
drop costs at least 200 ms before TCP even retries. The packet is delivered, but
about a thousand times too late. TCP's reliability is real, and you pay for it in
latency.

UDP, by contrast, does nothing on loss. The packet is gone; the next one is sent
on schedule; the latency of every surviving packet is untouched.

### 3.3 Why "late" equals "lost" for HFT

The domain decides which cost is worse. A trade signal's value as a function of
delay is roughly:

- delivered immediately → worth `V`,
- delivered 200 ms late → worth ≈ 0 (the market has already moved),
- never delivered → worth 0.

So in this domain a 200 ms-late packet is worth the same as a dropped one —
nothing — except that TCP's version also stalls the packets queued behind it
(head-of-line blocking) and halves `cwnd`, hurting the flow that follows. UDP's
loss is local; TCP's recovery is systemic. That is why "give up the packet"
beats "guarantee the packet" for market data, even though it sounds backwards.

## 4. Hypotheses and how they resolved

The analysis above produces three testable claims, which became the brief for
the team's measurement (Hanju) and the spec for the experiment.

**H1 — no loss, no real difference.** With no loss TCP never retransmits and
congestion control never engages, so only the 12-byte header difference
separates them — below the measurement floor.
*Result:* mean gap ~10 µs, P99 gap ~10 µs (UDP slightly higher). Holds.

**H2 — 1% loss explodes TCP's tail.** With 1% loss, ~10 of 1000 packets are
dropped in flight. TCP retransmits all of them — it still delivers 1000/1000 —
but each retransmit pays the RTO floor, so its P99 lands on those packets and
jumps past 100 ms. UDP just loses ~8 of them, and the survivors stay put.
*Result:* TCP P99 204,812 µs (≈205 ms) vs UDP P99 374.5 µs — **545×**. Holds,
and the 205 ms is the 200 ms `RTO_MIN` floor showing through.

**H3 — the trade-off favours UDP for market data.** Given H1 and H2 plus the
domain value function in §3.3, predictable latency beats guaranteed delivery for
market data, so a rational exchange puts market data on UDP and keeps TCP for
order entry.
*Result:* interpretive, and confirmed by what real exchanges do — NASDAQ, CME
and NYSE all run UDP multicast for market data and TCP for orders (Junseo's
part).

| Scenario | TCP P99 | UDP P99 | Ratio | Verdict |
|---|---|---|---|---|
| Baseline (no loss) | 375.7 µs | 386.1 µs | ~1× | H1 |
| 1% loss | 204,812 µs | 374.5 µs | 545× | H2 |

## 5. Limits of this analysis

- The numbers are Python over a Docker bridge, so the *absolute* latencies carry
  interpreter and stack overhead a production C++/DPDK system would not. The
  finding is the *relative* 545× asymmetry, which is independent of that
  baseline.
- A single-host Docker bridge does not reproduce the multi-router queueing
  dynamics of a real network; `tc netem` injects loss rather than letting a
  queue overflow naturally.
- M/M/1 assumes Poisson arrivals and exponential service. Real HFT traffic is
  burstier than Poisson, which makes the tail *worse* than the model, not
  better — so the model is a conservative description of the problem.

None of these touch the conclusion. They only bound how far to trust the
absolute numbers; the 545× asymmetry survives all three.

## References

[1] J. F. Kurose and K. W. Ross, *Computer Networking: A Top-Down Approach*,
8th ed., Pearson, 2021, Ch. 1.4 and Ch. 3 (UDP, reliable transport, TCP).

[2] V. Paxson, M. Allman, J. Chu, and M. Sargent, *Computing TCP's
Retransmission Timer*, RFC 6298, IETF, June 2011.

[3] U.S. Department of the Treasury et al., *Joint Staff Report: The U.S.
Treasury Market on October 15, 2014*, July 13, 2015.

[4] M. Aquilina, E. Budish, and P. O'Neill, "Quantifying the High-Frequency
Trading 'Arms Race'," *The Quarterly Journal of Economics*, vol. 137, no. 1,
pp. 493–564, 2022.

See the [main README](../README.md) for the full reference list and the team's
solution, measurement, and industry sections.
