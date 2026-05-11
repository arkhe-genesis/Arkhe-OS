package org.arkhe;

import okhttp3.*;
import com.google.gson.Gson;
import java.io.IOException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class ArchimedesClient {
    private final OkHttpClient httpClient;
    private final String baseUrl;
    private final Gson gson = new Gson();

    public ArchimedesClient(String baseUrl) {
        this.baseUrl = baseUrl;
        this.httpClient = new OkHttpClient();
    }

    public String analyze(Object request) throws IOException {
        String json = gson.toJson(request);
        RequestBody body = RequestBody.create(json, MediaType.get("application/json"));
        Request httpRequest = new Request.Builder()
                .url(baseUrl + "/analyze")
                .post(body)
                .build();
        try (Response response = httpClient.newCall(httpRequest).execute()) {
            if (!response.isSuccessful()) throw new IOException("Unexpected code " + response);
            return response.body().string();
        }
    }

    public String simulateSU2(Object request) throws IOException {
        String json = gson.toJson(request);
        RequestBody body = RequestBody.create(json, MediaType.get("application/json"));
        Request httpRequest = new Request.Builder()
                .url(baseUrl + "/simulate/su2")
                .post(body)
                .build();
        try (Response response = httpClient.newCall(httpRequest).execute()) {
            if (!response.isSuccessful()) throw new IOException("Unexpected code " + response);
            return response.body().string();
        }
    }

    public String simulateSL3Z(Object request) throws IOException {
        String json = gson.toJson(request);
        RequestBody body = RequestBody.create(json, MediaType.get("application/json"));
        Request httpRequest = new Request.Builder()
                .url(baseUrl + "/simulate/sl3z")
                .post(body)
                .build();
        try (Response response = httpClient.newCall(httpRequest).execute()) {
            if (!response.isSuccessful()) throw new IOException("Unexpected code " + response);
            return response.body().string();
        }
    }

    public String simulateWState(Object request) throws IOException {
        String json = gson.toJson(request);
        RequestBody body = RequestBody.create(json, MediaType.get("application/json"));
        Request httpRequest = new Request.Builder()
                .url(baseUrl + "/simulate/wstate")
                .post(body)
                .build();
        try (Response response = httpClient.newCall(httpRequest).execute()) {
            if (!response.isSuccessful()) throw new IOException("Unexpected code " + response);
            return response.body().string();
        }
    }

    public String detectPeaks(Object request) throws IOException {
        String json = gson.toJson(request);
        RequestBody body = RequestBody.create(json, MediaType.get("application/json"));
        Request httpRequest = new Request.Builder()
                .url(baseUrl + "/detect/peaks")
                .post(body)
                .build();
        try (Response response = httpClient.newCall(httpRequest).execute()) {
            if (!response.isSuccessful()) throw new IOException("Unexpected code " + response);
            return response.body().string();
        }
    }

    public String checkTeleportationResource(List<Double> phases, List<Double> coherence, int nodes, double lossProb) throws IOException {
        Map<String, Object> payload = new HashMap<>();
        payload.put("phases", phases);
        payload.put("coherence", coherence);
        payload.put("nodes", nodes);
        payload.put("loss_probability", lossProb);

        String json = gson.toJson(payload);
        RequestBody body = RequestBody.create(json, MediaType.get("application/json"));
        Request httpRequest = new Request.Builder()
                .url(baseUrl + "/analyze/teleportation-resource")
                .post(body)
                .build();
        try (Response response = httpClient.newCall(httpRequest).execute()) {
            if (!response.isSuccessful()) throw new IOException("Unexpected code " + response);
            return response.body().string();
        }
    }
}
