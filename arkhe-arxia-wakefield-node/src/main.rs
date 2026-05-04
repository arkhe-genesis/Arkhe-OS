#![no_std]
#![no_main]

use core::cell::RefCell;
use embassy_executor::Spawner;
use embassy_time::{Duration, Timer, Instant};
use esp_hal::clock::ClockControl;
use esp_hal::peripherals::Peripherals;
use esp_hal::prelude::*;
use esp_hal::spi::{master::Spi, SpiMode};
use esp_hal::gpio::{Output, Input, PullDown};
use esp_hal::Delay;
use esp_println::println;
use critical_section::Mutex;
use sha2::{Sha256, Digest};
use heapless::Vec;
use static_cell::StaticCell;

// Stubs simplificados para os módulos Arxia e Wakefield
mod wakefield;
mod arxia_bridge;
mod nonce_registry;
mod finality;

use wakefield::EmbeddedWakefieldAgent;
use arxia_bridge::LoRaTransport;
use nonce_registry::NonceRegistry;
use finality::{FinalityLevel, gap_to_finality};

// ============================================================================
// Configuração de hardware
// ============================================================================
static LORA: StaticCell<Mutex<RefCell<LoRaTransport>>> = StaticCell::new();
static AGENT: StaticCell<Mutex<RefCell<EmbeddedWakefieldAgent>>> = StaticCell::new();
static CACHE: StaticCell<Mutex<RefCell<NonceRegistry>>> = StaticCell::new();

#[embassy_executor::task]
async fn wakefield_loop() {
    let agent = AGENT.get().lock().await;
    let mut lora = LORA.get().lock().await;
    let mut cache = CACHE.get().lock().await;

    loop {
        // 1. Atualizar estado do wakefield local
        agent.borrow_mut().update_wakefield(120, 50);
        let snap = agent.borrow().snapshot();
        let kt_gap = agent.borrow().kt_gap;
        let hallucination = agent.borrow().hallucination;
        let finality = gap_to_finality(kt_gap);

        // 2. Construir bloco Arxia de 193 bytes (kind = 0x20)
        let mut payload = [0u8; 192];
        let snap_bytes: &[u8] = &snap.as_bytes(); // 24 bytes
        payload[..snap_bytes.len()].copy_from_slice(snap_bytes);
        // Zona ID
        payload[24..28].copy_from_slice(b"WFL1");
        // Preencher com mais dados, se necessário, até 192 bytes
        let block = arxia_bridge::SignedBlock::new(0x20, &payload).unwrap();
        let tx_buf = block.to_bytes(); // 193 bytes

        // 3. Transmitir via LoRa
        lora.borrow_mut().send(&tx_buf).await.ok();

        // 4. Aguardar recepção de outros nós (timeout de 5s)
        let mut rx_buf = [0u8; 200];
        if let Ok(len) = lora.borrow_mut().receive(&mut rx_buf, Duration::from_secs(5)).await {
            if len >= 2 && rx_buf[0] == 0x20 {
                if let Some(snap_remote) = wakefield::WakefieldSnapshot::from_bytes(&rx_buf[1..25]) {
                    let query_hash: [u8; 16] = rx_buf[25..41].try_into().unwrap_or_default();
                    let cost = snap_remote.kt_gap_scaled as u32;
                    cache.borrow_mut().store_query(&query_hash, snap_remote.timestamp as u64, cost);
                }
            }
        }

        // 5. Log via serial
        println!(
            "Wakefield | gap={:.2} hall={} final={:?} | cache_entries={}",
            kt_gap, hallucination, finality, cache.borrow().len()
        );

        Timer::after(Duration::from_secs(30)).await;
    }
}

#[entry]
fn main() -> ! {
    let peripherals = Peripherals::take();
    let system = peripherals.SYSTEM.split();
    let clocks = ClockControl::max(system.clock_control).freeze();
    let delay = Delay::new(&clocks);

    // Inicializar SPI para LoRa (exemplo: HSPI)
    let io = esp_hal::IO::new(peripherals.GPIO, peripherals.IO_MUX);
    let sclk = io.pins.gpio5;
    let miso = io.pins.gpio19;
    let mosi = io.pins.gpio27;
    let cs = io.pins.gpio18.into_push_pull_output();
    let spi = Spi::new_half_duplex(peripherals.SPI2, 100u32.kHz(), SpiMode::Mode0, &clocks)
        .with_pins(sclk, mosi, miso, cs);

    // Configurar reset do LoRa (opcional)
    let rst = io.pins.gpio14.into_push_pull_output();
    let lora_transport = LoRaTransport::new(spi, rst, delay);

    // Inicializar estruturas globais
    let agent = EmbeddedWakefieldAgent::new();
    let cache = NonceRegistry::new(100);

    LORA.init(Mutex::new(RefCell::new(lora_transport)));
    AGENT.init(Mutex::new(RefCell::new(agent)));
    CACHE.init(Mutex::new(RefCell::new(cache)));

    // Inicializar executor embassy
    let executor = embassy_executor::Executor::new();
    executor.run(|spawner| {
        spawner.spawn(wakefield_loop()).unwrap();
    })
}
