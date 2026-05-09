package sensors

import "context"

type GeomagneticSensor struct{}

type SensorConfig struct {
    SamplingRate float64
}

type GeomagneticReading struct {
    FieldStrength float64
}

func NewGeomagneticSensor(id string, config SensorConfig) *GeomagneticSensor {
    return &GeomagneticSensor{}
}

func (s *GeomagneticSensor) ReadField(ctx context.Context) (GeomagneticReading, error) {
    return GeomagneticReading{FieldStrength: 1.0}, nil
}
