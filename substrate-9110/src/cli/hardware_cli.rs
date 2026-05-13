use crate::hardware::device::SpaceHardware;
use crate::hardware::jetson_orin::JetsonOrin;
use clap::Parser;

#[derive(Parser)]
pub enum HardwareCommand {
    /// Provisionar um Jetson Orin edge
    ProvisionJetson { ip: String },
    /// Listar device profiles disponíveis
    ListDevices,
    /// Gerar atestação ZK para um dispositivo
    Attest { device_id: String },
}

pub async fn handle_hardware_cmd(cmd: HardwareCommand) {
    match cmd {
        HardwareCommand::ProvisionJetson { ip } => {
            let mut device = JetsonOrin::connect(&ip).await.unwrap();
            device.provision().await.unwrap();
            println!("Jetson Orin provisionado com sucesso");
        }
        HardwareCommand::ListDevices => {
            println!("Dispositivos: Jetson Orin, Vera Rubin");
        }
        HardwareCommand::Attest { device_id } => {
            println!("Atestando {}", device_id);
        }
    }
}
