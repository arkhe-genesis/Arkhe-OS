package formats

import (
	"arkhe/parser/frontends/api/models"
)

func ParseInfraConfig(source []byte, filename string) (*models.APISpecification, error) {
    // Stub
    return &models.APISpecification{
        Name: "Infra Config",
        Infrastructure: &models.InfrastructureSpec{
            Components: []models.InfrastructureComponent{
                {
                    ID: "1",
                    Name: "Redis",
                    Type: models.TypeCache,
                    Replicas: 3,
                    HealthCheck: &models.HealthCheckConfig{Endpoint: "/health"},
                    Config: map[string]interface{}{"pattern": map[string]interface{}{"type": "read-through"}},
                },
                {
                    ID: "2",
                    Name: "DB",
                    Type: models.TypeDatabase,
                    Replicas: 3,
                    HealthCheck: &models.HealthCheckConfig{Endpoint: "/health"},
                    Config: map[string]interface{}{"data_strategy": map[string]interface{}{"consistency_model": "strong"}},
                },
                {
                    ID: "3",
                    Name: "Gateway",
                    Type: models.TypeAPIGateway,
                    Replicas: 3,
                    HealthCheck: &models.HealthCheckConfig{Endpoint: "/health"},
                },
            },
        },
    }, nil
}

func ExtractInfrastructure(source []byte, filename string) (*models.InfrastructureSpec, error) {
    // Stub
    return &models.InfrastructureSpec{
        Components: []models.InfrastructureComponent{
            {
                ID: "1",
                Name: "Redis",
                Type: models.TypeCache,
                Replicas: 3,
                HealthCheck: &models.HealthCheckConfig{Endpoint: "/health"},
                Config: map[string]interface{}{"pattern": map[string]interface{}{"type": "read-through"}},
            },
            {
                ID: "2",
                Name: "DB",
                Type: models.TypeDatabase,
                Replicas: 3,
                HealthCheck: &models.HealthCheckConfig{Endpoint: "/health"},
                Config: map[string]interface{}{"data_strategy": map[string]interface{}{"consistency_model": "strong"}},
            },
            {
                ID: "3",
                Name: "Gateway",
                Type: models.TypeAPIGateway,
                Replicas: 3,
                HealthCheck: &models.HealthCheckConfig{Endpoint: "/health"},
            },
        },
    }, nil
}
