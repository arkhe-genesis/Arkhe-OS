FROM rust:1.76-slim as builder

WORKDIR /usr/src/app
COPY trading-engine/ trading-engine/
COPY data-feeds/ data-feeds/

WORKDIR /usr/src/app/trading-engine
RUN cargo build --release

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y libssl-dev ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /usr/src/app/trading-engine/target/release/trading-engine /usr/local/bin/trading-engine

CMD ["trading-engine"]
