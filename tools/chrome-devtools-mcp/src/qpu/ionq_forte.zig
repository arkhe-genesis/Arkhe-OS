// src/qpu/ionq_forte.zig
//! Driver para IonQ Forte (QPU de Íons Presos)
//! Traduz comandos de alto nível em chamadas de API REST.

const std = @import("std");
const http = std.http;

pub const IonQError = error {
    AuthFailed,
    JobFailed,
    Timeout,
    SerializationError,
};

pub const IonQClient = struct {
    client: http.Client,
    api_key: []const u8,
    base_url: []const u8,

    pub fn init(allocator: std.mem.Allocator, api_key: []const u8) IonQClient {
        return .{
            .client = http.Client{ .allocator = allocator },
            .api_key = api_key,
            .base_url = "https://api.ionq.com/v0.2/job",
        };
    }

    pub fn deinit(self: *IonQClient) void {
        self.client.deinit();
    }

    /// Envia um circuito QASM para execução no hardware
    pub fn submitJob(self: *IonQClient, qasm: []const u8, shots: u32) ![]const u8 {
        _ = self; _ = qasm; _ = shots;
        return "job_id_simulated_001";
    }

    /// Verifica o status do Job
    pub fn getJobStatus(self: *IonQClient, job_id: []const u8) !bool {
        _ = self; _ = job_id;
        return true;
    }

    /// Recupera o resultado da medição
    pub fn getResult(self: *IonQClient, job_id: []const u8) ![]u8 {
        _ = self; _ = job_id;
        return &[_]u8{}; // Stub
    }
};
