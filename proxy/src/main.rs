// proxy/src/main.rs
// Reverse proxy for llama-server with rate limiting and metrics.
//
// Endpoints exposed:
//   GET  /health                → health check (passes through to backend)
//   POST /completion            → raw completion (proxied)
//   POST /v1/chat/completions   → OpenAI-compatible chat (proxied)
//   GET  /metrics               → Prometheus metrics (local counters)
//   GET  /stats                 → JSON stats summary
//
// Configuration via environment variables:
//   BACKEND_URL          (default: http://localhost:8080)
//   PROXY_HOST           (default: 0.0.0.0)
//   PROXY_PORT           (default: 8242)
//   MAX_CONCURRENT       (default: 16)
//   REQUEST_TIMEOUT_SECS (default: 300)
//   RUST_LOG             (default: info)

use actix_web::{
    middleware, web, App, HttpRequest, HttpResponse, HttpServer,
};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::{
    env,
    sync::{
        atomic::{AtomicU64, Ordering},
        Arc,
    },
    time::{Duration, Instant, SystemTime, UNIX_EPOCH},
};
use tokio::sync::Semaphore;

// ── Metrics ──────────────────────────────────────────────────────────────────

#[derive(Default)]
struct Metrics {
    requests_total: AtomicU64,
    requests_ok: AtomicU64,
    requests_err: AtomicU64,
    requests_rejected: AtomicU64, // rate-limited
    tokens_generated: AtomicU64,
    total_latency_ms: AtomicU64,
}

impl Metrics {
    fn record_ok(&self, latency_ms: u64, tokens: u64) {
        self.requests_total.fetch_add(1, Ordering::Relaxed);
        self.requests_ok.fetch_add(1, Ordering::Relaxed);
        self.total_latency_ms.fetch_add(latency_ms, Ordering::Relaxed);
        self.tokens_generated.fetch_add(tokens, Ordering::Relaxed);
    }

    fn record_err(&self) {
        self.requests_total.fetch_add(1, Ordering::Relaxed);
        self.requests_err.fetch_add(1, Ordering::Relaxed);
    }

    fn record_rejected(&self) {
        self.requests_total.fetch_add(1, Ordering::Relaxed);
        self.requests_rejected.fetch_add(1, Ordering::Relaxed);
    }

    fn avg_latency_ms(&self) -> f64 {
        let ok = self.requests_ok.load(Ordering::Relaxed);
        if ok == 0 {
            return 0.0;
        }
        self.total_latency_ms.load(Ordering::Relaxed) as f64 / ok as f64
    }

    fn prometheus_text(&self) -> String {
        format!(
            "# HELP llm_proxy_requests_total Total requests received\n\
             # TYPE llm_proxy_requests_total counter\n\
             llm_proxy_requests_total {}\n\
             # HELP llm_proxy_requests_ok Successful requests\n\
             # TYPE llm_proxy_requests_ok counter\n\
             llm_proxy_requests_ok {}\n\
             # HELP llm_proxy_requests_err Failed requests\n\
             # TYPE llm_proxy_requests_err counter\n\
             llm_proxy_requests_err {}\n\
             # HELP llm_proxy_requests_rejected Rate-limited requests\n\
             # TYPE llm_proxy_requests_rejected counter\n\
             llm_proxy_requests_rejected {}\n\
             # HELP llm_proxy_tokens_generated Total tokens generated\n\
             # TYPE llm_proxy_tokens_generated counter\n\
             llm_proxy_tokens_generated {}\n\
             # HELP llm_proxy_avg_latency_ms Average request latency\n\
             # TYPE llm_proxy_avg_latency_ms gauge\n\
             llm_proxy_avg_latency_ms {:.2}\n",
            self.requests_total.load(Ordering::Relaxed),
            self.requests_ok.load(Ordering::Relaxed),
            self.requests_err.load(Ordering::Relaxed),
            self.requests_rejected.load(Ordering::Relaxed),
            self.tokens_generated.load(Ordering::Relaxed),
            self.avg_latency_ms(),
        )
    }
}

// ── App state ─────────────────────────────────────────────────────────────────

struct AppState {
    backend_url: String,
    http_client: Client,
    semaphore: Arc<Semaphore>,
    metrics: Arc<Metrics>,
    start_time: Instant,
}

// ── Request / response types ─────────────────────────────────────────────────

#[derive(Debug, Serialize, Deserialize)]
struct StatsResponse {
    uptime_secs: u64,
    backend_url: String,
    max_concurrent: usize,
    requests_total: u64,
    requests_ok: u64,
    requests_err: u64,
    requests_rejected: u64,
    tokens_generated: u64,
    avg_latency_ms: f64,
    timestamp: u64,
}

// ── Handlers ─────────────────────────────────────────────────────────────────

async fn health(state: web::Data<AppState>) -> HttpResponse {
    // Forward to backend; if it fails, return degraded status
    match state
        .http_client
        .get(format!("{}/health", state.backend_url))
        .timeout(Duration::from_secs(5))
        .send()
        .await
    {
        Ok(resp) if resp.status().is_success() => HttpResponse::Ok().json(serde_json::json!({
            "status": "ok",
            "backend": "reachable",
        })),
        Ok(resp) => HttpResponse::ServiceUnavailable().json(serde_json::json!({
            "status": "degraded",
            "backend_status": resp.status().as_u16(),
        })),
        Err(e) => HttpResponse::ServiceUnavailable().json(serde_json::json!({
            "status": "degraded",
            "backend": "unreachable",
            "error": e.to_string(),
        })),
    }
}

async fn proxy_completion(
    req: HttpRequest,
    body: web::Bytes,
    state: web::Data<AppState>,
) -> HttpResponse {
    proxy_request(req, body, state, "/completion").await
}

async fn proxy_chat(
    req: HttpRequest,
    body: web::Bytes,
    state: web::Data<AppState>,
) -> HttpResponse {
    proxy_request(req, body, state, "/v1/chat/completions").await
}

async fn proxy_request(
    _req: HttpRequest,
    body: web::Bytes,
    state: web::Data<AppState>,
    path: &str,
) -> HttpResponse {
    // Acquire slot (rate limiting)
    let _permit = match state.semaphore.try_acquire() {
        Ok(p) => p,
        Err(_) => {
            state.metrics.record_rejected();
            return HttpResponse::TooManyRequests().json(serde_json::json!({
                "error": "rate_limit_exceeded",
                "message": "Server is at capacity. Retry after a moment.",
            }));
        }
    };

    let t0 = Instant::now();
    let url = format!("{}{}", state.backend_url, path);

    let result = state
        .http_client
        .post(&url)
        .header("Content-Type", "application/json")
        .body(body.to_vec())
        .send()
        .await;

    match result {
        Ok(backend_resp) => {
            let status = backend_resp.status();
            let latency_ms = t0.elapsed().as_millis() as u64;

            match backend_resp.bytes().await {
                Ok(resp_bytes) => {
                    // Try to extract token count for metrics
                    let tokens = if let Ok(json) =
                        serde_json::from_slice::<serde_json::Value>(&resp_bytes)
                    {
                        json.get("tokens_predicted")
                            .and_then(|v| v.as_u64())
                            .unwrap_or(0)
                    } else {
                        0
                    };

                    if status.is_success() {
                        state.metrics.record_ok(latency_ms, tokens);
                    } else {
                        state.metrics.record_err();
                    }

                    HttpResponse::build(
                        actix_web::http::StatusCode::from_u16(status.as_u16())
                            .unwrap_or(actix_web::http::StatusCode::INTERNAL_SERVER_ERROR),
                    )
                    .content_type("application/json")
                    .body(resp_bytes)
                }
                Err(e) => {
                    state.metrics.record_err();
                    log::error!("Failed to read backend response: {}", e);
                    HttpResponse::BadGateway().json(serde_json::json!({
                        "error": "backend_read_error",
                        "detail": e.to_string(),
                    }))
                }
            }
        }
        Err(e) => {
            state.metrics.record_err();
            let is_timeout = e.is_timeout();
            log::error!("Backend request failed (timeout={}): {}", is_timeout, e);
            if is_timeout {
                HttpResponse::GatewayTimeout().json(serde_json::json!({
                    "error": "backend_timeout",
                    "detail": "The model took too long to respond.",
                }))
            } else {
                HttpResponse::BadGateway().json(serde_json::json!({
                    "error": "backend_unreachable",
                    "detail": e.to_string(),
                }))
            }
        }
    }
}

async fn metrics(state: web::Data<AppState>) -> HttpResponse {
    HttpResponse::Ok()
        .content_type("text/plain; version=0.0.4")
        .body(state.metrics.prometheus_text())
}

async fn stats(state: web::Data<AppState>) -> HttpResponse {
    let ts = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs();

    let max_concurrent = state.semaphore.available_permits()
        + (env::var("MAX_CONCURRENT")
            .ok()
            .and_then(|v| v.parse::<usize>().ok())
            .unwrap_or(16)
            - state.semaphore.available_permits());

    HttpResponse::Ok().json(StatsResponse {
        uptime_secs: state.start_time.elapsed().as_secs(),
        backend_url: state.backend_url.clone(),
        max_concurrent,
        requests_total: state.metrics.requests_total.load(Ordering::Relaxed),
        requests_ok: state.metrics.requests_ok.load(Ordering::Relaxed),
        requests_err: state.metrics.requests_err.load(Ordering::Relaxed),
        requests_rejected: state.metrics.requests_rejected.load(Ordering::Relaxed),
        tokens_generated: state.metrics.tokens_generated.load(Ordering::Relaxed),
        avg_latency_ms: state.metrics.avg_latency_ms(),
        timestamp: ts,
    })
}

// ── Main ─────────────────────────────────────────────────────────────────────

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    // Initialise logger (RUST_LOG=info by default)
    env_logger::Builder::from_env(
        env_logger::Env::default().default_filter_or("info"),
    )
    .init();

    // Read config from environment
    let backend_url = env::var("BACKEND_URL")
        .unwrap_or_else(|_| "http://localhost:8080".to_string());
    let host = env::var("PROXY_HOST").unwrap_or_else(|_| "0.0.0.0".to_string());
    let port: u16 = env::var("PROXY_PORT")
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(8242);
    let max_concurrent: usize = env::var("MAX_CONCURRENT")
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(16);
    let request_timeout: u64 = env::var("REQUEST_TIMEOUT_SECS")
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(300);

    // Build shared HTTP client with connection pooling
    let http_client = Client::builder()
        .timeout(Duration::from_secs(request_timeout))
        .pool_max_idle_per_host(max_concurrent)
        .build()
        .expect("Failed to build HTTP client");

    let state = web::Data::new(AppState {
        backend_url: backend_url.clone(),
        http_client,
        semaphore: Arc::new(Semaphore::new(max_concurrent)),
        metrics: Arc::new(Metrics::default()),
        start_time: Instant::now(),
    });

    log::info!("LLM Proxy starting");
    log::info!("  Backend:        {}", backend_url);
    log::info!("  Listen:         {}:{}", host, port);
    log::info!("  Max concurrent: {}", max_concurrent);
    log::info!("  Timeout:        {}s", request_timeout);

    HttpServer::new(move || {
        App::new()
            .app_data(state.clone())
            // Log every request: method, path, status, latency
            .wrap(middleware::Logger::new(
                "%r → %s (%Dms)",
            ))
            .route("/health", web::get().to(health))
            .route("/completion", web::post().to(proxy_completion))
            .route("/v1/chat/completions", web::post().to(proxy_chat))
            .route("/metrics", web::get().to(metrics))
            .route("/stats", web::get().to(stats))
    })
    .bind(format!("{}:{}", host, port))?
    .run()
    .await
}