# Chapter 21: Metrics Monitoring and Alerting System

> Source: [ByteByteGo - System Design Interview](https://bytebytego.com/courses/system-design-interview/metrics-monitoring-and-alerting-system)

Design an infrastructure monitoring system like Datadog, Prometheus + Grafana, or New Relic.

---

## Step 1 - Understand the problem and establish design scope

**Requirements:** Monitor infrastructure metrics (CPU, memory, disk, network), support various metrics including business metrics, configurable alerting with multiple channels (email, PagerDuty, webhook), dashboard visualization, configurable retention period.

**Non-functional:** Scalability (100M metrics/day), low query latency for dashboards, reliability, flexibility.

**Estimations:** 1000 server pools, 100 machines per pool, 100 metrics per machine → 10 million metrics, written every 10 seconds → 1M write ops/sec.

---

## Step 2 - High-level design

### Data model

Metric data is inherently a **time series**: metric name, set of labels/tags, array of (timestamp, value) pairs.

Example:
```
cpu.usage host=webserver01 region=us-east 1640000000 0.73
```

### Storage — Time Series Database (TSDB)

Regular RDBMS is not optimized for time series data. Use specialized TSDBs:
- **InfluxDB**: Popular open-source TSDB
- **Prometheus**: Pull-based metrics system
- **OpenTSDB**: Built on HBase

### Architecture components

1. **Metrics source**: Servers, applications, databases
2. **Metrics collector**: Gathers metrics (push or pull model)
3. **Time Series DB**: Persistent storage
4. **Query service**: Interface for dashboards and alerting
5. **Alerting system**: Evaluates rules, sends notifications
6. **Visualization**: Grafana-like dashboards

### Push vs Pull model

| Aspect | Push | Pull |
|--------|------|------|
| How | Agents push metrics to collector | Collector scrapes metrics endpoints |
| Example | StatsD, Graphite | Prometheus |
| Pros | Immediate, works behind firewall | Simple agent, single source of truth |
| Cons | Collector overload risk | Harder behind firewall |

### Java Example – Metrics Collection System

```java
import java.util.*;
import java.util.concurrent.*;

public class MetricsMonitor {

    record MetricPoint(String name, Map<String, String> tags, 
                       double value, long timestamp) {}

    // Ring buffer per metric (retention window)
    private final Map<String, Deque<MetricPoint>> timeSeries = new ConcurrentHashMap<>();
    private final Map<String, Double> alertThresholds = new ConcurrentHashMap<>();
    private static final int MAX_POINTS = 1000;

    public void recordMetric(String name, Map<String, String> tags, double value) {
        MetricPoint point = new MetricPoint(name, tags, value, System.currentTimeMillis());
        Deque<MetricPoint> series = timeSeries.computeIfAbsent(name, 
            k -> new ConcurrentLinkedDeque<>());
        series.addLast(point);
        if (series.size() > MAX_POINTS) series.pollFirst();

        // Check alert
        Double threshold = alertThresholds.get(name);
        if (threshold != null && value > threshold) {
            System.out.printf("🚨 ALERT: %s = %.2f (threshold: %.2f) tags=%s%n",
                name, value, threshold, tags);
        }
    }

    public void setAlert(String metricName, double threshold) {
        alertThresholds.put(metricName, threshold);
    }

    public double getAverage(String name, long windowMs) {
        Deque<MetricPoint> series = timeSeries.get(name);
        if (series == null) return 0;
        long cutoff = System.currentTimeMillis() - windowMs;
        return series.stream()
            .filter(p -> p.timestamp() > cutoff)
            .mapToDouble(MetricPoint::value)
            .average()
            .orElse(0);
    }

    public static void main(String[] args) throws InterruptedException {
        MetricsMonitor monitor = new MetricsMonitor();
        monitor.setAlert("cpu.usage", 0.90);
        monitor.setAlert("memory.usage", 0.85);

        Random rand = new Random();
        Map<String, String> tags = Map.of("host", "web-01", "region", "us-east");

        for (int i = 0; i < 10; i++) {
            monitor.recordMetric("cpu.usage", tags, 0.5 + rand.nextDouble() * 0.5);
            monitor.recordMetric("memory.usage", tags, 0.6 + rand.nextDouble() * 0.3);
            Thread.sleep(100);
        }

        System.out.printf("%nAvg CPU (last 5s): %.2f%n", 
            monitor.getAverage("cpu.usage", 5000));
    }
}
```

---

## Step 3 - Design deep dive

### Time series data down-sampling
- Store high-resolution (1s) data for 7 days
- Aggregate to 1-minute resolution for 30 days
- Aggregate to 1-hour resolution for 1 year

### Alerting system
1. **Rules config** (YAML-based): metric, condition, threshold, duration, notification channels
2. **Alert manager**: Dedup, throttle, route alerts
3. **Notification channels**: Email, Slack, PagerDuty, webhook

### Query language
- Prometheus uses PromQL: `rate(http_requests_total[5m])`
- Support for aggregation (sum, avg, max, min), filtering by labels

---

## Step 4 - Wrap up

Additional talking points:
- **Anomaly detection with ML** instead of static thresholds
- **Log monitoring integration**
- **Distributed tracing** (Jaeger, Zipkin)
- **SLO/SLI/SLA monitoring dashboards**
