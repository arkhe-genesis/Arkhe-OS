using System;
using System.Threading.Tasks;
using RestSharp;
using Newtonsoft.Json;
using System.Collections.Generic;

namespace Arkhe.ArchimedesAgent
{
    public class ArchimedesClient
    {
        private readonly RestClient _client;
        public ArchimedesClient(string baseUrl) => _client = new RestClient(baseUrl);

        public async Task<string> AnalyzeAsync(object request)
        {
            var req = new RestRequest("/analyze", Method.Post);
            req.AddJsonBody(request);
            var response = await _client.ExecuteAsync(req);
            return response.Content;
        }

        public async Task<string> SimulateSU2Async(object request)
        {
            var req = new RestRequest("/simulate/su2", Method.Post);
            req.AddJsonBody(request);
            var response = await _client.ExecuteAsync(req);
            return response.Content;
        }

        public async Task<string> SimulateSL3ZAsync(object request)
        {
            var req = new RestRequest("/simulate/sl3z", Method.Post);
            req.AddJsonBody(request);
            var response = await _client.ExecuteAsync(req);
            return response.Content;
        }

        public async Task<string> SimulateWStateAsync(object request)
        {
            var req = new RestRequest("/simulate/wstate", Method.Post);
            req.AddJsonBody(request);
            var response = await _client.ExecuteAsync(req);
            return response.Content;
        }

        public async Task<string> DetectPeaksAsync(object request)
        {
            var req = new RestRequest("/detect/peaks", Method.Post);
            req.AddJsonBody(request);
            var response = await _client.ExecuteAsync(req);
            return response.Content;
        }

        public async Task<string> CheckTeleportationResourceAsync(List<double> phases, List<double> coherence, int nodes = 3, double lossProb = 0.2)
        {
            var req = new RestRequest("/analyze/teleportation-resource", Method.Post);
            req.AddJsonBody(new {
                phases = phases,
                coherence = coherence,
                nodes = nodes,
                loss_probability = lossProb
            });
            var response = await _client.ExecuteAsync(req);
            return response.Content;
        }
    }
}
