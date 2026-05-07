package formats

import (

	"arkhe/parser/frontends/api/models"
)

// ParsegRPCProto parseia spec protobuf
func ParsegRPCProto(source []byte, filename string) (*models.APISpecification, error) {
    // Stub
    spec := &models.APISpecification{
        Name: filename,
        Services: []models.Service{
            {
                Name: "gRPC Service",
                Protocol: "gRPC",
                Endpoints: []models.Endpoint{
                    {
                        Path: "/grpc",
                        Method: "RPC",
                        Resilience: models.ResilienceHints{
                            Timeout: "30s",
                        },
                    },
                },
            },
        },
    }
    return spec, nil
}
