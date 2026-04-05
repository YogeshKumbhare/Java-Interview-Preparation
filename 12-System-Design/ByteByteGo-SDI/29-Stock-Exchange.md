# Chapter 29: Stock Exchange

> Source: [ByteByteGo - System Design Interview](https://bytebytego.com/courses/system-design-interview/stock-exchange)

Design the core of a stock exchange system — the matching engine and surrounding infrastructure.

---

## Step 1 - Understand the problem and establish design scope

**Features:** Place orders (buy/sell), match orders, real-time market data, order book management.

**Non-functional:** Ultra-low latency (< 1ms matching), high availability, deterministic processing, fairness (FIFO ordering).

**Scale:** 100 symbols, 1 billion orders/day for all symbols, peak: 100K orders/sec.

---

## Step 2 - High-level design

### Core concepts

- **Order**: Buy/sell instruction (symbol, side, price, quantity, type)
- **Order Book**: Collection of all open buy (bid) and sell (ask) orders for a symbol, sorted by price-time priority
- **Matching Engine**: Matches buy and sell orders when prices cross
- **Market Data**: Real-time feed of trades and order book updates

### Order types
| Type | Description |
|------|-------------|
| Market | Execute immediately at best available price |
| Limit | Execute at specified price or better |
| Stop | Triggered when market reaches a price |

### Architecture

1. **Gateway**: Receives orders, validates, and forwards
2. **Sequencer**: Assigns global sequence number for deterministic processing
3. **Matching Engine**: Core component — runs single-threaded per symbol for determinism
4. **Market Data Publisher**: Broadcasts trades and order book updates
5. **Reporter**: Trade confirmation, clearing, settlement

### Java Example – Order Matching Engine

```java
import java.util.*;

public class MatchingEngine {
    enum Side { BUY, SELL }
    enum OrderType { MARKET, LIMIT }

    record Order(String id, String symbol, Side side, OrderType type,
                 double price, int quantity, long timestamp) implements Comparable<Order> {
        @Override
        public int compareTo(Order o) {
            if (this.side == Side.BUY) {
                // Highest price first, then earliest timestamp
                int priceCmp = Double.compare(o.price, this.price);
                return priceCmp != 0 ? priceCmp : Long.compare(this.timestamp, o.timestamp);
            } else {
                // Lowest price first, then earliest timestamp
                int priceCmp = Double.compare(this.price, o.price);
                return priceCmp != 0 ? priceCmp : Long.compare(this.timestamp, o.timestamp);
            }
        }
    }

    record Trade(String buyOrderId, String sellOrderId, String symbol,
                 double price, int quantity, long timestamp) {}

    private final PriorityQueue<Order> buyOrders = new PriorityQueue<>();
    private final PriorityQueue<Order> sellOrders = new PriorityQueue<>();
    private final List<Trade> trades = new ArrayList<>();

    public void submitOrder(Order order) {
        System.out.printf("[ORDER] %s %s %d %s @ $%.2f%n",
            order.side(), order.symbol(), order.quantity(),
            order.type(), order.price());

        if (order.side() == Side.BUY) {
            matchBuy(order);
        } else {
            matchSell(order);
        }
    }

    private void matchBuy(Order buyOrder) {
        int remaining = buyOrder.quantity();
        while (remaining > 0 && !sellOrders.isEmpty()) {
            Order bestSell = sellOrders.peek();
            if (buyOrder.type() == OrderType.LIMIT && bestSell.price() > buyOrder.price()) break;

            sellOrders.poll();
            int filled = Math.min(remaining, bestSell.quantity());
            double tradePrice = bestSell.price(); // Price-time priority

            trades.add(new Trade(buyOrder.id(), bestSell.id(), buyOrder.symbol(),
                                  tradePrice, filled, System.currentTimeMillis()));
            System.out.printf("  🔄 TRADE: %d shares @ $%.2f (buy=%s, sell=%s)%n",
                filled, tradePrice, buyOrder.id(), bestSell.id());

            remaining -= filled;
            if (bestSell.quantity() > filled) {
                sellOrders.offer(new Order(bestSell.id(), bestSell.symbol(), Side.SELL,
                    bestSell.type(), bestSell.price(), bestSell.quantity() - filled, bestSell.timestamp()));
            }
        }
        if (remaining > 0 && buyOrder.type() == OrderType.LIMIT) {
            buyOrders.offer(new Order(buyOrder.id(), buyOrder.symbol(), Side.BUY,
                buyOrder.type(), buyOrder.price(), remaining, buyOrder.timestamp()));
        }
    }

    private void matchSell(Order sellOrder) {
        int remaining = sellOrder.quantity();
        while (remaining > 0 && !buyOrders.isEmpty()) {
            Order bestBuy = buyOrders.peek();
            if (sellOrder.type() == OrderType.LIMIT && bestBuy.price() < sellOrder.price()) break;

            buyOrders.poll();
            int filled = Math.min(remaining, bestBuy.quantity());
            double tradePrice = bestBuy.price();

            trades.add(new Trade(bestBuy.id(), sellOrder.id(), sellOrder.symbol(),
                                  tradePrice, filled, System.currentTimeMillis()));
            System.out.printf("  🔄 TRADE: %d shares @ $%.2f (buy=%s, sell=%s)%n",
                filled, tradePrice, bestBuy.id(), sellOrder.id());

            remaining -= filled;
            if (bestBuy.quantity() > filled) {
                buyOrders.offer(new Order(bestBuy.id(), bestBuy.symbol(), Side.BUY,
                    bestBuy.type(), bestBuy.price(), bestBuy.quantity() - filled, bestBuy.timestamp()));
            }
        }
        if (remaining > 0 && sellOrder.type() == OrderType.LIMIT) {
            sellOrders.offer(new Order(sellOrder.id(), sellOrder.symbol(), Side.SELL,
                sellOrder.type(), sellOrder.price(), remaining, sellOrder.timestamp()));
        }
    }

    public void printOrderBook() {
        System.out.println("\n=== ORDER BOOK ===");
        System.out.println("BIDS (Buy):");
        new PriorityQueue<>(buyOrders).stream().limit(5)
            .forEach(o -> System.out.printf("  $%.2f x %d%n", o.price(), o.quantity()));
        System.out.println("ASKS (Sell):");
        new PriorityQueue<>(sellOrders).stream().limit(5)
            .forEach(o -> System.out.printf("  $%.2f x %d%n", o.price(), o.quantity()));
    }

    public static void main(String[] args) {
        MatchingEngine engine = new MatchingEngine();
        long t = System.currentTimeMillis();

        engine.submitOrder(new Order("S1", "AAPL", Side.SELL, OrderType.LIMIT, 150.00, 100, t++));
        engine.submitOrder(new Order("S2", "AAPL", Side.SELL, OrderType.LIMIT, 151.00, 200, t++));
        engine.submitOrder(new Order("B1", "AAPL", Side.BUY, OrderType.LIMIT, 149.00, 50, t++));
        engine.submitOrder(new Order("B2", "AAPL", Side.BUY, OrderType.LIMIT, 150.00, 150, t++)); // matches S1

        engine.printOrderBook();
        System.out.println("\nTotal trades: " + engine.trades.size());
    }
}
```

---

## Step 3 - Design deep dive

### Matching engine
- **Single-threaded per symbol**: Eliminates need for locks, ensures deterministic matching
- **Memory-mapped files** for speed
- **Pre-allocated memory**: Avoid GC pauses (critical for < 1ms latency)
- In Java: Use off-heap memory (Unsafe or Chronicle libraries)

### Sequencer
- Assigns monotonically increasing sequence numbers
- Every event is deterministic and replayable
- If matching engine crashes, replay from sequencer log

### Market data distribution
- Use multicast (UDP) for lowest latency
- L1 data: best bid/ask prices
- L2 data: full order book depth
- L3 data: every individual order

### Risk checks
- Pre-trade risk checks (sufficient funds, position limits)
- Must be as fast as possible to not add latency

---

## Step 4 - Wrap up

Additional talking points:
- **Hot-warm architecture** for failover (< 1 second recovery)
- **Colocation**: Traders place servers physically near exchange
- **Dark pools**: Private trading venues
- **Circuit breakers**: Halt trading during extreme volatility
- **Clearing and settlement** (T+1 or T+2)
