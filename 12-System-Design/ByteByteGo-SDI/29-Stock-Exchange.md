# Stock Exchange (Full Content)

In this chapter, we design an electronic stock exchange system.

The basic function of an exchange is to facilitate the matching of buyers and sellers efficiently. This fundamental function has not changed over time. Before the rise of computing, people exchanged tangible goods by bartering and shouting at each other to get matched. Today, orders are processed silently by supercomputers, and people trade not only for the exchange of products, but also for speculation and arbitrage. Technology has greatly changed the landscape of trading and exponentially boosted electronic market trading volume.

When it comes to stock exchanges, most people think about major market players like The New York Stock Exchange (NYSE) or Nasdaq, which have existed for over fifty years. In fact, there are many other types of exchange. Some focus on vertical segmentation of the financial industry and place special focus on technology [1], while others have an emphasis on fairness [2]. Before diving into the design, it is important to check with the interviewer about the scale and the important characteristics of the exchange in question.

Just to get a taste of the kind of problem we are dealing with; NYSE is trading billions of matches per day [3], and HKEX about 200 billion shares per day [4]. Figure 1 shows the big exchanges in the “trillion-dollar club” by market capitalization.

Figure 1 Largest stock exchanges (Source: [5])

## Step 1 - Understand the Problem and Establish Design scope

A modern exchange is a complicated system with stringent requirements on latency, throughput, and robustness. Before we start, let’s ask the interviewer a few questions to clarify the requirements.

Candidate: Which securities are we going to trade? Stocks, options, or futures?
Interviewer: For simplicity, only stocks.

Candidate: Which types of order operations are supported: placing a new order, canceling an order, or replacing an order? Do we need to support limit order, market order, or conditional order?
Interviewer: We need to support the following: placing a new order and canceling an order. For the order type, we only need to consider the limit order.

Candidate: Does the system need to support after-hours trading?
Interviewer: No, we just need to support the normal trading hours.

Candidate: Could you describe the basic functions of the exchange? And the scale of the exchange, such as how many users, how many symbols, and how many orders?
Interviewer: A client can place new limit orders or cancel them, and receive matched trades in real-time. A client can view the real-time order book (the list of buy and sell orders). The exchange needs to support at least tens of thousands of users trading at the same time, and it needs to support at least 100 symbols. For the trading volume, we should support billions of orders per day. Also, the exchange is a regulated facility, so we need to make sure it runs risk checks.

Candidate: Could you please elaborate on risk checks?
Interviewer: Let’s just do simple risk checks. For example, a user can only trade a maximum of 1 million shares of Apple stock in one day.

Candidate: I noticed you didn’t mention user wallet management. Is it something we also need to consider?
Interviewer: Good catch! We need to make sure users have sufficient funds when they place orders. If an order is waiting in the order book to be filled, the funds required for the order need to be withheld to prevent overspending.

### Non-functional requirements
After checking with the interviewer for the functional requirements, we should determine the non-functional requirements. In fact, requirements like “at least 100 symbols” and “tens of thousands of users” tell us that the interviewer wants us to design a small-to-medium scale exchange. On top of this, we should make sure the design can be extended to support more symbols and users. Many interviewers focus on extensibility as an area for follow-up questions.

Here is a list of non-functional requirements:
- Availability. At least 99.99%.
- Fault tolerance. Fault tolerance and a fast recovery mechanism are needed.
- Latency. The round-trip latency should be at the millisecond level.
- Security. The exchange should have an account management system.

### Back-of-the-envelope estimation
- 100 symbols
- 1 billion orders per day
- NYSE is open for 6.5 hours.
- QPS: 1 billion / 6.5 / 3600 = ~43,000
- Peak QPS: 5 * QPS = 215,000.

## Step 2 - Propose High-Level Design and Get Buy-In

### Business Knowledge 101
- Broker: Most retail clients trade via a broker.
- Institutional client: Trade in large volumes using specialized software.
- Limit order: Buy or sell order with a fixed price.
- Market order: Executed at the prevailing market price immediately.
- Market data levels: L1 (best bid/ask), L2 (more price levels), L3 (price levels and queued quantity).
- Candlestick chart: Represents stock price for a certain period.
- FIX: Financial Information eXchange protocol.

### High-level design
The system consists of a trading flow (critical path), market data flow, and reporting flow. The trading flow includes: Client -> Broker -> Client Gateway -> Order Manager -> Sequencer -> Matching Engine.

## API Design
- POST /v1/order: Place an order.
- GET /execution: Query execution info.
- GET /marketdata/orderBook/L2: Query L2 order book info.
- GET /marketdata/candles: Query candlestick chart data.

## Data models
- Product, order, and execution
- Order book (efficient via doubly-linked list and Map)
- Candlestick chart

## Step 3 - Design Deep Dive

### Performance
- Reduce tasks on critical path.
- Pin application loops to CPU cores.
- Use mmap for low-latency communication (Shared Memory).

### Event sourcing
- Store immutable log of all state-changing events.
- Guarantees identical and replayable states.

### High availability
- Use redundant instances (Hot-Warm).
- Heartbeat detection for failover.

### Fault tolerance
- Use Raft cluster for state consensus and leader election.

### Matching algorithms
- FIFO (First In First Out) is common.

### Determinism
- Functional and latency determinism are crucial.

### Market data publisher optimizations
- Use ring buffers (lock-free, pre-allocated).

### Distribution fairness
- Reliable UDP Multicast and Random order assignment.

### Colocation
- VIP service for low latency.

### Network security
- Combat DDoS via isolation, caching, and rate limiting.

## Wrap Up
Exchanges can run on a single gigantic server. Cloud infrastructure and DeFi/AMM are also alternative deployment models.

Content extracted from: https://bytebytego.com/courses/system-design-interview/stock-exchange

In this chapter, we design an electronic stock exchange system.

The basic function of an exchange is to facilitate the matching of buyers and sellers efficiently. This fundamental function has not changed over time. Before the rise of computing, people exchanged tangible goods by bartering and shouting at each other to get matched. Today, orders are processed silently by supercomputers, and people trade not only for the exchange of products, but also for speculation and arbitrage. Technology has greatly changed the landscape of trading and exponentially boosted electronic market trading volume.

When it comes to stock exchanges, most people think about major market players like The New York Stock Exchange (NYSE) or Nasdaq, which have existed for over fifty years. In fact, there are many other types of exchange. Some focus on vertical segmentation of the financial industry and place special focus on technology [1], while others have an emphasis on fairness [2]. Before diving into the design, it is important to check with the interviewer about the scale and the important characteristics of the exchange in question.

Just to get a taste of the kind of problem we are dealing with; NYSE is trading billions of matches per day [3], and HKEX about 200 billion shares per day [4]. Figure 1 shows the big exchanges in the “trillion-dollar club” by market capitalization.

Figure 1 Largest stock exchanges (Source: [5])

## Step 1 - Understand the Problem and Establish Design scope

A modern exchange is a complicated system with stringent requirements on latency, throughput, and robustness. Before we start, let’s ask the interviewer a few questions to clarify the requirements.

Candidate: Which securities are we going to trade? Stocks, options, or futures?
Interviewer: For simplicity, only stocks.

Candidate: Which types of order operations are supported: placing a new order, canceling an order, or replacing an order? Do we need to support limit order, market order, or conditional order?
Interviewer: We need to support the following: placing a new order and canceling an order. For the order type, we only need to consider the limit order.

Candidate: Does the system need to support after-hours trading?
Interviewer: No, we just need to support the normal trading hours.

Candidate: Could you describe the basic functions of the exchange? And the scale of the exchange, such as how many users, how many symbols, and how many orders?
Interviewer: A client can place new limit orders or cancel them, and receive matched trades in real-time. A client can view the real-time order book (the list of buy and sell orders). The exchange needs to support at least tens of thousands of users trading at the same time, and it needs to support at least 100 symbols. For the trading volume, we should support billions of orders per day. Also, the exchange is a regulated facility, so we need to make sure it runs risk checks.

Candidate: Could you please elaborate on risk checks?
Interviewer: Let’s just do simple risk checks. For example, a user can only trade a maximum of 1 million shares of Apple stock in one day.

Candidate: I noticed you didn’t mention user wallet management. Is it something we also need to consider?
Interviewer: Good catch! We need to make sure users have sufficient funds when they place orders. If an order is waiting in the order book to be filled, the funds required for the order need to be withheld to prevent overspending.

### Non-functional requirements

After checking with the interviewer for the functional requirements, we should determine the non-functional requirements. In fact, requirements like “at least 100 symbols” and “tens of thousands of users” tell us that the interviewer wants us to design a small-to-medium scale exchange. On top of this, we should make sure the design can be extended to support more symbols and users. Many interviewers focus on extensibility as an area for follow-up questions.

Here is a list of non-functional requirements:
- Availability. At least 99.99%.
- Fault tolerance. Fault tolerance and a fast recovery mechanism are needed.
- Latency. The round-trip latency should be at the millisecond level.
- Security. The exchange should have an account management system.

### Back-of-the-envelope estimation
- 100 symbols
- 1 billion orders per day
- NYSE is open for 6.5 hours.
- QPS: 1 billion / 6.5 / 3600 = ~43,000
- Peak QPS: 5 * QPS = 215,000.

## Step 2 - Propose High-Level Design and Get Buy-In

### Business Knowledge 101
- Broker: Most retail clients trade via a broker.
- Institutional client: Trade in large volumes using specialized software.
- Limit order: Buy or sell order with a fixed price.
- Market order: Executed at the prevailing market price immediately.
- Market data levels: L1 (best bid/ask), L2 (more price levels), L3 (price levels and queued quantity).
- Candlestick chart: Represents stock price for a certain period.
- FIX: Financial Information eXchange protocol.

### High-level design
The system consists of a trading flow (critical path), market data flow, and reporting flow.
The trading flow includes: Client -> Broker -> Client Gateway -> Order Manager -> Sequencer -> Matching Engine.

## API Design
- POST /v1/order: Place an order.
- GET /execution: Query execution info.
- GET /marketdata/orderBook/L2: Query L2 order book info.
- GET /marketdata/candles: Query candlestick chart data.

## Data models
- Product, order, and execution
- Order book (efficient via doubly-linked list and Map)
- Candlestick chart

## Step 3 - Design Deep Dive

### Performance
- Reduce tasks on critical path.
- Pin application loops to CPU cores.
- Use mmap for low-latency communication (Shared Memory).

### Event sourcing
- Store immutable log of all state-changing events.
- Guarantees identical and replayable states.

### High availability
- Use redundant instances (Hot-Warm).
- Heartbeat detection for failover.

### Fault tolerance
- Use Raft cluster for state consensus and leader election.

### Matching algorithms
- FIFO (First In First Out) is common.

### Determinism
- Functional and latency determinism are crucial.

### Market data publisher optimizations
- Use ring buffers (lock-free, pre-allocated).

### Distribution fairness
- Reliable UDP Multicast and Random order assignment.

### Colocation
- VIP service for low latency.

### Network security
- Combat DDoS via isolation, caching, and rate limiting.

## Wrap Up
Exchanges can run on a single gigantic server. Cloud infrastructure and DeFi/AMM are also alternative deployment models.

... (referenced materials omitted for brevity in summary, but extracted)
