# FidelityGate — Dataset Catalog & Provenance Register

This document registers all public, replayed, and synthetic network telemetry sources ingested into FidelityGate Layer 1.

---

## 1. Primary Public Telemetry Source: Cisco Innovation Edge Telemetry

- **Source Identifier**: `cisco-ie-telemetry`
- **Canonical Repository**: [https://github.com/cisco-ie/telemetry](https://github.com/cisco-ie/telemetry)
- **Publication Reference**: ACM SIGCOMM BigDama'18 / IEEE INFOCOM'18
- **Dataset Version / Tag**: `master` (commit snapshot 2020-05-28)
- **License**: Community Data License Agreement – Permissive – Version 1.0 (`CDLA-Permissive-1.0`)
- **Attribution**: Cisco Systems, Inc. / CDLA-Permissive-1.0
- **Acquisition Mechanism**: Automated via `scripts/download_datasets.py` with sha256 checksum and size boundary verification. No API keys required.

### Acquired Raw Datasets

| Source Sub-folder | Remote File | Local Relative Path | SHA-256 Checksum | Size | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Folder 0** | `README.md` | `data/raw/cisco_telemetry/0/README.md` | `c13029de8f25...` | 1.45 KB | Baseline experiment case documentation |
| **Folder 0** | `baseline_header.txt` | `data/raw/cisco_telemetry/0/baseline_header.txt` | `4d0a488c4a1b...` | 1.80 KB | 87 column header definitions |
| **Folder 0** | `baseline_no_anomaly.csv.gz` | `data/raw/cisco_telemetry/0/baseline_no_anomaly.csv.gz` | `820aca1f1487...` | 17.97 MB | Raw time-series telemetry under steady-state baseline |
| **Folder 0 (Sample)** | Calibrated excerpt | `data/raw/cisco_telemetry/0/baseline_sample_1000.csv` | `9d77af9d1212...` | 247 KB | Calibrated 1,000-row baseline sample (22,000 metric points) |
| **Folder 3** | `README.md` | `data/raw/cisco_telemetry/3/README.md` | `0aa5d3ac16bf...` | 5.56 KB | BGP clear experiment case documentation |
| **Folder 3** | `bgpclear_header.txt` | `data/raw/cisco_telemetry/3/bgpclear_header.txt` | `4d0a488c4a1b...` | 1.80 KB | Header definitions for BGP clear event |
| **Folder 3** | `bgpclear_casedata.txt` | `data/raw/cisco_telemetry/3/bgpclear_casedata.txt` | `40313b4ac60d...` | 1.68 KB | Event timelines on leaf1, leaf6, spine2 switches |
| **Folder 3** | `bgpclear08042017.csv.gz` | `data/raw/cisco_telemetry/3/bgpclear08042017.csv.gz` | `e196dc698ac3...` | 12.24 MB | Anomaly telemetry during controlled BGP clears |
| **Folder 3 (Sample)** | Calibrated excerpt | `data/raw/cisco_telemetry/3/bgpclear_sample_1000.csv` | `aed9f23075ff...` | 255 KB | Calibrated 1,000-row BGP clear sample (22,000 metric points) |

---

## 2. Telemetry Schema & Field Mapping

The Cisco IOS-XR telemetry format comprises 87 header columns. The adapter extracts, validates, and normalizes them into canonical `NormalizedObservation` records:

### Core Identity & Temporal Columns

| Source Column | Target Canonical Field | Parsing & Transformation Rules |
| :--- | :--- | :--- |
| `name` | Metadata YANG path | Stored in observation metadata, e.g. `fib-statistics/nodes/node/drops` |
| `time` | `timestamp` | Nanosecond epoch divided by $10^9$ into ISO-8601 UTC string. If missing or unparseable, field is `None` and issue is logged. |
| `Producer` | `entity_id` (fallback) | Network device hostname (e.g. `leaf1`, `leaf5`, `spine2`). |
| `node-name` | `entity_id` (node) | Router sub-card (e.g. `0/RP0/CPU0`). Sets `entity_type="node"`. |
| `interface-name` | `entity_id` (interface) | Physical/logical interface (e.g. `Hu0/0/0/8`). Sets `entity_type="interface"`. |

### Physical Metric Columns & Documented Units

Units are attached strictly from verified Cisco documentation. Unverified or undocumented metrics retain `unit=None` (never guessed).

| Metric Name | Canonical `metric_name` | Verified Unit | Description |
| :--- | :--- | :--- | :--- |
| `bytes-received` | `bytes-received` | `bytes` | Total octets received |
| `bytes-sent` | `bytes-sent` | `bytes` | Total octets transmitted |
| `packets-received` | `packets-received` | `packets` | Total packets received |
| `packets-sent` | `packets-sent` | `packets` | Total packets transmitted |
| `bandwidth` | `bandwidth` | `kbps` | Configured interface bandwidth |
| `input-data-rate` | `input-data-rate` | `bits/sec` | Bitrate received |
| `output-data-rate` | `output-data-rate` | `bits/sec` | Bitrate transmitted |
| `input-packet-rate`| `input-packet-rate` | `packets/sec` | Packet rate received |
| `output-packet-rate`| `output-packet-rate`| `packets/sec` | Packet rate transmitted |
| `total-cpu-one-minute` | `total-cpu-one-minute` | `percent` | 1-minute CPU utilization |
| `total-cpu-five-minute`| `total-cpu-five-minute`| `percent` | 5-minute CPU utilization |
| `total-cpu-fifteen-minute` | `total-cpu-fifteen-minute` | `percent` | 15-minute CPU utilization |
| `free-physical-memory` | `free-physical-memory` | `bytes` | Unallocated RAM |
| `free-application-memory` | `free-application-memory` | `bytes` | App-available RAM |
| `total-number-of-drop-packets` | `total-number-of-drop-packets` | `packets` | Total packet drops in FIB |
| `no-route-packets` | `no-route-packets` | `packets` | Unroutable packets |
| `active-routes-count` | `active-routes-count` | `routes` | RIB active prefix count |
| `input-drops` / `output-drops` | `input-drops` / `output-drops` | `None` (undocumented) | Explicitly unassigned unit |

---

## 3. Explicit Data Mode Separation

FidelityGate enforces a rigid boundary between data classes via the `DataMode` enumeration:

1. `PUBLIC_DATA`: Directly derived from real public observations (e.g. Cisco IE telemetry). Free from synthetic model assumptions.
2. `REPLAY`: Real public observations replayed through simulation clocks or pipeline stages.
3. `SYNTHETIC_FIXTURE`: Deterministic offline scenarios used for benchmark regression tests.
4. `SYNTHETIC_FAULT_INJECTION`: Controlled perturbations with declared ground-truth schedules.
5. `SIMULATED`: Posterior outputs computed by mathematical models (e.g. $M/M/1$ queue approximations).
6. `UNKNOWN`: Data whose provenance cannot be verified.

---

## 4. Known Data Limitations

1. **Topology Absence**: The Cisco telemetry CSVs record device and interface time-series counters but do not provide an explicit graph topology adjacency matrix. Graph topology must be correlated from separate topology documentation or representative topologies.
2. **Missing End-to-End Latency**: The Cisco traces provide interface rates and drop counters, not end-to-end user SLO path latency. Path latency in later layers is modeled or approximated by the simulator.
3. **No Injected Mitigations**: Public telemetry does not record reroute interventions or counterfactual alternatives. Those are computed in Layer 2+ simulation.
4. **Independent Evaluator Isolation**: Public data contains no reference evaluator ground truth; reference evaluator data is strictly segregated from agent-accessible telemetry.

