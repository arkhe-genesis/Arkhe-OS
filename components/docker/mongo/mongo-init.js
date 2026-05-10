db = db.getSiblingDB('arkhe_telemetry');
db.createCollection('telemetry_logs');
db.telemetry_logs.createIndex({ "nodeId": 1, "timestamp": -1 });
db.telemetry_logs.createIndex({ "lambda_2": 1 });
