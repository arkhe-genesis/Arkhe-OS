// functions-source.js — Código executado off-chain pelo Chainlink
// Busca preços de recursos de APIs externas (ex: AWS, GCP, energy markets)

const resourceApis = {
  "energy_gj": "https://api.energymarket.com/spot-price?unit=GJ",
  "compute_tflops": "https://api.cloudprovider.com/pricing?instance=gpu",
  "bandwidth_mbps": "https://api.cdnprovider.com/bandwidth-cost",
  "crystal_time_ms": "https://api.quantumcloud.com/pentacene-time"
};

// Função principal executada pelo Chainlink Functions runtime
async function main() {
  const resource = args[0];  // passado via requestResourcePrice
  const api = resourceApis[resource];

  if (!api) {
    throw Error(`Recurso não suportado: ${resource}`);
  }

  // Buscar preço da API externa
  const response = await Functions.makeHttpRequest({
    url: api,
    method: "GET",
    headers: { "Authorization": `Bearer ${secrets.apiKey}` }
  });

  if (response.error) {
    throw Error(`Erro na API: ${response.error}`);
  }

  // Extrair preço do JSON de resposta
  const data = JSON.parse(response.data);
  const price = Math.round(data.price * 1e18);  // converter para wei (18 decimals)

  // Retornar resultado codificado para a blockchain
  return Functions.encodeUint256(price);
}
