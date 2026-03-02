# LYNK Event System

Event sistemi, sürü içerisinde önemli olayların broadcast edilmesi ve paylaşılması için kullanılır.

---

## Genel Bakış

Event sistemi, drone'ların birbirlerine önemli olayları bildirmesini sağlar:
- QR kod tespiti
- Çarpışma riski
- Sistem hataları
- Görev durumu değişiklikleri
- Acil durumlar

**Temel Özellikler:**
- ✅ Broadcast (tüm sürüye)
- ✅ Priority-based redundancy (kritik event'ler 3x gönderilir)
- ✅ Duplicate detection (source_vehicle_id + boot_counter + sequence ile)
- ✅ TTL-based relay (komşular iletir)
- ✅ Rate limiting (bant genişliği koruması)
- ✅ Genişletilebilir (yeni event tipleri eklenebilir)

---

## Event Envelope Yapısı

```protobuf
syntax = "proto3";

message EventEnvelope {
  // Metadata
  uint32 source_vehicle_id = 1;    // Event'i üreten drone (collision prevention)
  uint32 boot_counter = 2;         // Persistent boot counter (reboot-safe, increments on each boot)
  uint32 sequence = 3;             // Drone'un kendi sequence'ı (monotonic counter within boot)
  EventType event_type = 4;        // Event type ID
  EventPriority priority = 5;      // Event priority level
  uint64 timestamp_ms = 6;         // Event occurrence time
  
  // Optional location
  optional float lat = 7;
  optional float lon = 8;
  optional float alt = 9;
  
  // Event-specific payload (oneof field numbers are separate from EventType enum values)
  oneof payload {
    // Detection events
    QrDetected qr_detected = 20;
    ObstacleDetected obstacle_detected = 21;
    
    // Safety events
    CollisionRisk collision_risk = 30;
    BatteryLow battery_low = 31;
    FailsafeTriggered failsafe_triggered = 32;
    EmergencyCrash emergency_crash = 33;
    
    // System events
    GpsDegraded gps_degraded = 40;
    LinkQualityDegraded link_quality_degraded = 41;
    MotorFailure motor_failure = 42;
    CommandStatus command_status = 43;
    
    // Mission events
    MissionWaypointReached mission_waypoint_reached = 50;
    MissionComplete mission_complete = 51;
    
    // Swarm events
    FormationBroken formation_broken = 60;
    VehicleLost vehicle_lost = 61;
    CrashDetected crash_detected = 62;
    
    // Custom events
    CustomEvent custom_event = 100;
  }
}
```

---

## Priority Levels

| Priority | Value | Transmissions | Delays (ms) | Use Case |
|----------|-------|---------------|-------------|----------|
| **CRITICAL** | 3 | 3 | 0, 50, 150 | Motor failure, crash, collision imminent |
| **HIGH** | 2 | 2 | 0, 100 | Battery critical, GPS lost, failsafe |
| **NORMAL** | 1 | 1 | 0 | QR detected, waypoint reached |
| **LOW** | 0 | 1 | 0 | Info messages, status updates |

---

## Redundancy Mekanizması

Event'ler priority'ye göre otomatik olarak birden fazla kez gönderilir (proaktif güvenilirlik):

```python
# 1. CRITICAL event gönderimi (3x transmission) - En yüksek öncelik
t=0ms:   1. gönderim
t=50ms:  2. gönderim
t=150ms: 3. gönderim

# 2. HIGH event gönderimi (2x transmission) - Yüksek öncelik
t=0ms:   1. gönderim
t=100ms: 2. gönderim

# 3. NORMAL event gönderimi (1x transmission) - Normal öncelik
t=0ms:   1. gönderim

# 4. LOW event gönderimi (1x transmission) - Düşük öncelik
t=0ms:   1. gönderim
```

**Not:** Alıcı tarafta `(source_vehicle_id, boot_counter, sequence)` tuple ile duplicate detection yapılır, aynı event birden fazla alınsa bile sadece bir kez işlenir.

---

## Duplicate Detection

Alıcı tarafta aynı `(source_vehicle_id, boot_counter, sequence)` tuple ile gelen event'ler sadece bir kez işlenir:

```python
# İlk event geldi
(vehicle_id=5, boot=3, seq=100) → İşlenir ✅

# Aynı event tekrar geldi (redundant transmission)
(vehicle_id=5, boot=3, seq=100) → İşlenmez (duplicate) ❌

# Farklı drone, aynı boot+sequence
(vehicle_id=7, boot=3, seq=100) → İşlenir ✅ (farklı drone)

# Aynı drone, farklı sequence
(vehicle_id=5, boot=3, seq=101) → İşlenir ✅ (yeni event)

# Aynı drone, reboot sonrası aynı sequence
(vehicle_id=5, boot=4, seq=100) → İşlenir ✅ (farklı boot cycle)
```

**Implementasyon (boot_counter-based):**
```python
_received_events = {}  # (vehicle_id, boot_counter, sequence) -> timestamp_ms
CACHE_TTL_MS = 60000   # 60 saniye
_last_cleanup = 0
CLEANUP_INTERVAL_MS = 10000  # 10 saniyede bir cleanup

def cleanup_expired_events():
    """Periyodik cache temizliği"""
    now_ms = time.time() * 1000
    expired = [k for k, v in _received_events.items() if now_ms - v > CACHE_TTL_MS]
    for k in expired:
        del _received_events[k]
    if expired:
        logger.debug(f"[EVENT] Cleaned {len(expired)} expired events")

def handle_event(payload, frame_meta, interface):
    global _last_cleanup
    event_data = deserialize_event(payload)
    event_key = (event_data["source_vehicle_id"], 
                 event_data["boot_counter"],
                 event_data["sequence"])
    event_ts = event_data["timestamp_ms"]
    now_ms = time.time() * 1000
    
    # Periyodik cleanup
    if now_ms - _last_cleanup > CLEANUP_INTERVAL_MS:
        cleanup_expired_events()
        _last_cleanup = now_ms
    
    # Duplicate check
    if event_key in _received_events:
        logger.debug(f"[EVENT] Duplicate ignored: {event_key}")
        return
    
    # İlk kez alıyoruz
    _received_events[event_key] = event_ts
    process_event(event_data)
```

**Reboot Safety:**
- Drone reboot olur, boot_counter artar (persistent)
- Sequence sıfırlanır ama boot_counter farklı olduğu için collision yok
- %100 collision-free garanti ✅

---

## Enums

```protobuf
// Event priority levels
enum EventPriority {
  PRIORITY_LOW = 0;
  PRIORITY_NORMAL = 1;
  PRIORITY_HIGH = 2;
  PRIORITY_CRITICAL = 3;
}

// Event types
enum EventType {
  // Detection events (20-29)
  EVENT_QR_DETECTED = 20;
  EVENT_OBSTACLE_DETECTED = 21;
  
  // Safety events (30-39)
  EVENT_COLLISION_RISK = 30;
  EVENT_BATTERY_LOW = 31;
  EVENT_FAILSAFE_TRIGGERED = 32;
  EVENT_EMERGENCY_CRASH = 33;
  
  // System events (40-49)
  EVENT_GPS_DEGRADED = 40;
  EVENT_LINK_QUALITY_DEGRADED = 41;
  EVENT_MOTOR_FAILURE = 42;
  EVENT_COMMAND_STATUS = 43;
  
  // Mission events (50-59)
  EVENT_MISSION_WAYPOINT_REACHED = 50;
  EVENT_MISSION_COMPLETE = 51;
  
  // Swarm events (60-69)
  EVENT_FORMATION_BROKEN = 60;
  EVENT_VEHICLE_LOST = 61;
  EVENT_CRASH_DETECTED = 62;
  
  // Custom events (100+)
  EVENT_CUSTOM = 100;
}

// Obstacle types
enum ObstacleType {
  OBSTACLE_UNKNOWN = 0;
  OBSTACLE_STATIC = 1;
  OBSTACLE_DYNAMIC = 2;
}

// Failsafe reasons
enum FailsafeReason {
  FAILSAFE_RC_LOST = 0;
  FAILSAFE_GPS_LOST = 1;
  FAILSAFE_BATTERY_LOW = 2;
  FAILSAFE_GCS_LOST = 3;
}

// Failsafe actions
enum FailsafeAction {
  FAILSAFE_RTL = 0;
  FAILSAFE_LAND = 1;
  FAILSAFE_HOLD = 2;
}

// Crash reasons
enum CrashReason {
  CRASH_MOTOR_FAILURE = 0;
  CRASH_BATTERY_DEAD = 1;
  CRASH_COLLISION = 2;
  CRASH_UNKNOWN = 3;
}

// GPS degradation reasons
enum GpsDegradedReason {
  GPS_LOW_SATELLITES = 0;
  GPS_HIGH_HDOP = 1;
  GPS_SIGNAL_LOSS = 2;
}

// Motor failure types
enum MotorFailureType {
  MOTOR_STOPPED = 0;
  MOTOR_DEGRADED = 1;
  MOTOR_OVERHEATING = 2;
}

// Formation broken reasons
enum FormationBrokenReason {
  FORMATION_LINK_LOST = 0;
  FORMATION_OUT_OF_RANGE = 1;
  FORMATION_MANUAL_OVERRIDE = 2;
}

// Crash detection methods
enum CrashDetectionMethod {
  CRASH_DETECT_TELEMETRY_ANOMALY = 0;
  CRASH_DETECT_VISUAL = 1;
  CRASH_DETECT_HEARTBEAT_TIMEOUT = 2;
}
```

---

## Event Types

### Detection Events (20-29)

#### QrDetected (20)
```protobuf
message QrDetected {
  string qr_code = 1;
  float confidence = 2;
  optional bytes image_thumbnail = 3;
}
```

#### ObstacleDetected (21)
```protobuf
message ObstacleDetected {
  float distance_m = 1;
  float bearing_deg = 2;
  ObstacleType obstacle_type = 3;
}
```

### Safety Events (30-39)

#### CollisionRisk (30)
```protobuf
message CollisionRisk {
  uint32 target_vehicle_id = 1;
  float distance_m = 2;
  float relative_velocity_mps = 3;
  float time_to_collision_s = 4;
}
```

#### BatteryLow (31)
```protobuf
message BatteryLow {
  float voltage = 1;
  uint32 remaining_percent = 2;
  float estimated_flight_time_s = 3;
}
```

#### FailsafeTriggered (32)
```protobuf
message FailsafeTriggered {
  FailsafeReason reason = 1;
  FailsafeAction action = 2;
}
```

#### EmergencyCrash (33)
```protobuf
message EmergencyCrash {
  CrashReason reason = 1;
  float altitude_m = 2;
  uint32 battery_percent = 3;
  optional string last_error = 4;
}
```

### System Events (40-49)

#### GpsDegraded (40)
```protobuf
message GpsDegraded {
  uint32 satellites = 1;
  float hdop = 2;
  GpsDegradedReason reason = 3;
}
```

#### LinkQualityDegraded (41)
```protobuf
message LinkQualityDegraded {
  uint32 link_quality_percent = 1;
  uint32 packet_loss_percent = 2;
  float rssi_dbm = 3;
}
```

#### MotorFailure (42)
```protobuf
message MotorFailure {
  uint32 motor_id = 1;
  uint32 current_rpm = 2;
  uint32 expected_rpm = 3;
  MotorFailureType failure_type = 4;
}
```

### Mission Events (50-59)

#### MissionWaypointReached (50)
```protobuf
message MissionWaypointReached {
  uint32 waypoint_index = 1;
  uint32 total_waypoints = 2;
  float distance_error_m = 3;
}
```

#### MissionComplete (51)
```protobuf
message MissionComplete {
  uint32 total_waypoints = 1;
  float total_distance_m = 2;
  float total_time_s = 3;
}
```

### Swarm Events (60-69)

#### FormationBroken (60)
```protobuf
message FormationBroken {
  uint32 missing_vehicle_id = 1;
  FormationBrokenReason reason = 2;
  float time_since_last_contact_s = 3;
}
```

#### VehicleLost (61)
```protobuf
message VehicleLost {
  uint32 lost_vehicle_id = 1;
  float last_known_lat = 2;
  float last_known_lon = 3;
  float time_since_contact_s = 4;
}
```

#### CrashDetected (62)
```protobuf
message CrashDetected {
  uint32 crashed_vehicle_id = 1;
  float estimated_crash_lat = 2;
  float estimated_crash_lon = 3;
  CrashDetectionMethod detection_method = 4;
  optional float vertical_velocity_mps = 5;
}
```

### Custom Events (100+)

#### CustomEvent (100)
```protobuf
message CustomEvent {
  string event_name = 1;
  string description = 2;
  map<string, string> metadata = 3;
  optional bytes raw_data = 4;
}
```

---

## Kullanım Örnekleri

### Örnek 1: QR Kod Tespit Edildi
```python
send_event(
    interface,
    event_type=EVENT_QR_DETECTED,
    priority=PRIORITY_NORMAL,
    lat=41.0082,
    lon=28.9784,
    payload=QrDetected(qr_code="TEKNOFEST2024", confidence=0.95)
)
```

### Örnek 2: Motor Arızası (Kritik)
```python
send_event(
    interface,
    event_type=EVENT_MOTOR_FAILURE,
    priority=PRIORITY_CRITICAL,  # 3x transmission
    payload=MotorFailure(
        motor_id=3,
        current_rpm=0,
        expected_rpm=5000,
        failure_type=MOTOR_STOPPED
    )
)
```

---

## Rate Limiting

| Priority | Max Events/Second |
|----------|-------------------|
| CRITICAL | 10 |
| HIGH | 5 |
| NORMAL | 2 |
| LOW | 1 |

**Implementasyon (Token bucket):**
```python
_rate_limiters = {}  # priority -> (tokens, last_refill_time)
RATE_LIMITS = {PRIORITY_CRITICAL: 10, PRIORITY_HIGH: 5, PRIORITY_NORMAL: 2, PRIORITY_LOW: 1}

def check_rate_limit(priority):
    """Token bucket rate limiting"""
    now = time.time()
    max_rate = RATE_LIMITS[priority]
    
    if priority not in _rate_limiters:
        _rate_limiters[priority] = [max_rate, now]
        return True
    
    tokens, last_refill = _rate_limiters[priority]
    
    # Refill tokens
    elapsed = now - last_refill
    tokens = min(max_rate, tokens + elapsed * max_rate)
    
    # Check if we have tokens
    if tokens >= 1.0:
        _rate_limiters[priority] = [tokens - 1.0, now]
        return True
    else:
        _rate_limiters[priority] = [tokens, now]
        logger.warning(f"[EVENT] Rate limit exceeded for priority {priority}")
        return False
```

---

## Config Ayarları

```yaml
event:
  enabled: true
  
  redundancy:
    critical:
      count: 3
      delays_ms: [0, 50, 150]
    high:
      count: 2
      delays_ms: [0, 100]
    normal:
      count: 1
      delays_ms: [0]
    low:
      count: 1
      delays_ms: [0]
  
  rate_limit:
    critical: 10
    high: 5
    normal: 2
    low: 1
  
  cache:
    ttl_seconds: 60
    max_size: 1000
```

---

**Status:** Production-ready  
**Version:** 1.0
