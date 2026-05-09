// parser/frontends/api/formats/xml_parser.go
package formats

import (
	"encoding/xml"
	"fmt"
	"strings"
	"strconv"

	"arkhe/parser/frontends/api/models"
)

// ParseXMLAPISpec parses XML-based API/infrastructure specifications
// into the canonical APISpecification model.
func ParseXMLAPISpec(source []byte) (*models.APISpecification, error) {
	// Detect WSDL vs custom API XML
	if len(source) > 0 && isWSDLDeclaration(source[:min(512, len(source))]) {
		return parseWSDLToSpec(source)
	}
	return parseCustomXMLSpec(source)
}

// xmlAPIDoc represents a generic XML API specification structure
type xmlAPIDoc struct {
	XMLName      xml.Name         `xml:"apiSpecification"`
	Version      string           `xml:"version,attr,omitempty"`
	Info         xmlInfo          `xml:"info"`
	Servers      []xmlServer      `xml:"servers>server"`
	SecurityDefs []xmlSecurityDef `xml:"components>securitySchemes>securityScheme"`
	Paths        []xmlPath        `xml:"paths>path"`
}

type xmlInfo struct {
	Title       string `xml:"title"`
	Version     string `xml:"version"`
	Description string `xml:"description"`
}

type xmlServer struct {
	URL         string `xml:"url,attr"`
	Description string `xml:"description,attr"`
}

type xmlSecurityDef struct {
	Name        string `xml:"name,attr"`
	Type        string `xml:"type,attr"`
	Scheme      string `xml:"scheme,attr,omitempty"`
	BearerFmt   string `xml:"bearerFormat,attr,omitempty"`
}

type xmlPath struct {
	Path        string         `xml:"path,attr"`
	Operations  []xmlOperation `xml:",any"`
}

type xmlOperation struct {
	XMLName     xml.Name
	Summary     string          `xml:"summary"`
	OperationID string          `xml:"operationId"`
	Tags        []string        `xml:"tags>tag"`
	Security    []xmlSecRef     `xml:"security>securityRef"`
	Parameters  []xmlParam      `xml:"parameters>parameter"`
	RequestBody *xmlReqBody     `xml:"requestBody"`
	Responses   []xmlResp       `xml:"responses>response"`
	Resilience  *xmlResilience  `xml:"x-resilience"`
	Timeout     string          `xml:"x-timeout"`
	Idempotency *xmlIdempotency `xml:"x-idempotency"`
}

type xmlSecRef struct {
	SchemeName string `xml:"schemeName,attr"`
}

type xmlParam struct {
	Name        string `xml:"name,attr"`
	In          string `xml:"in,attr"`
	Required    string `xml:"required,attr"`
	Type        string `xml:"type,attr"`
	Description string `xml:"description"`
}

type xmlReqBody struct {
	Required string `xml:"required,attr"`
}

type xmlResp struct {
	StatusCode  string `xml:"statusCode,attr"`
	Description string `xml:"description"`
}

type xmlResilience struct {
	Retry  *xmlRetry         `xml:"retry"`
	CB     *xmlCircuitBreaker `xml:"circuitBreaker"`
}

type xmlRetry struct {
	MaxAttempts int    `xml:"maxAttempts,attr"`
	Backoff     string `xml:"backoff,attr"`
}

type xmlCircuitBreaker struct {
	FailureThreshold int    `xml:"failureThreshold,attr"`
	Timeout          string `xml:"timeout,attr"`
}

type xmlIdempotency struct {
	Enabled     bool   `xml:"enabled,attr"`
	KeyLocation string `xml:"keyLocation,attr"`
	KeyName     string `xml:"keyName,attr"`
	TTL         string `xml:"ttl,attr"`
}

// parseCustomXMLSpec maps custom XML API specs to canonical model
func parseCustomXMLSpec(source []byte) (*models.APISpecification, error) {
	var doc xmlAPIDoc
	if err := xml.Unmarshal(source, &doc); err != nil {
		return nil, fmt.Errorf("failed to unmarshal XML API spec: %w", err)
	}

	spec := &models.APISpecification{
		Name:        doc.Info.Title,
		Version:     pickString(doc.Info.Version, doc.Version, "1.0.0"),
		Description: doc.Info.Description,
		Services:    make([]models.Service, 0),
	}

	// Servers
	for _, srv := range doc.Servers {
		spec.BaseURLs = append(spec.BaseURLs, srv.URL)
	}

	// Security Schemes
	for _, sec := range doc.SecurityDefs {
		spec.AuthSchemes = append(spec.AuthSchemes, models.AuthScheme{
			Name:         sec.Name,
			Type:         mapXMLAuthType(sec.Type),
			Scheme:       sec.Scheme,
			BearerFormat: sec.BearerFmt,
		})
	}

	// Endpoints
	endpoints := make([]models.Endpoint, 0)
	for _, path := range doc.Paths {
		for _, op := range path.Operations {
			if !isValidHTTPMethod(op.XMLName.Local) {
				continue
			}
			ep := mapXMLOpToEndpoint(path.Path, op, spec.AuthSchemes)
			endpoints = append(endpoints, ep)
		}
	}
	spec.Services = groupEndpointsByService(endpoints, nil)

	return spec, nil
}

// parseWSDLToSpec maps WSDL/SOAP to canonical API model (simplified mapping)
func parseWSDLToSpec(source []byte) (*models.APISpecification, error) {
	// Full WSDL parser would parse <wsdl:definitions>, <wsdl:portType>, <wsdl:operation>, etc.
	// For brevity, we extract service name, target namespace, and map operations to endpoints.
	// In production: use github.com/fiorix/go-wsdl or custom SAX parser.

	spec := &models.APISpecification{
		Name:    "WSDL SOAP Service",
		Version: "1.0",
	}

	// Heuristic extraction for demo purposes
	if strings.Contains(string(source), "targetNamespace=") {
		split := strings.Split(string(source), "targetNamespace=\"")
		if len(split) > 1 {
			ns := strings.Split(split[1], "\"")[0]
			spec.Description = "SOAP Service with namespace: " + ns
		}
	}

	return spec, nil
}

func mapXMLAuthType(t string) models.AuthType {
	switch strings.ToLower(t) {
	case "http", "bearer":
		return models.AuthTypeHTTP
	case "apikey":
		return models.AuthTypeAPIKey
	case "oauth2":
		return models.AuthTypeOAuth2
	case "openidconnect":
		return models.AuthTypeOIDC
	default:
		return models.AuthTypeUnknown
	}
}

func mapXMLOpToEndpoint(path string, op xmlOperation, schemes []models.AuthScheme) models.Endpoint {
	ep := models.Endpoint{
		Path:        path,
		Method:      strings.ToUpper(op.XMLName.Local),
		OperationID: op.OperationID,
		Summary:     op.Summary,
		Tags:        op.Tags,
	}

	for _, p := range op.Parameters {
		ep.Parameters = append(ep.Parameters, models.Parameter{
			Name:        p.Name,
			In:          p.In,
			Required:    parseBoolDefault(p.Required, false),
			Description: p.Description,
			Schema:      models.Schema{Type: p.Type},
		})
	}

	if op.RequestBody != nil {
		ep.RequestBody = models.RequestBody{
			Required: parseBoolDefault(op.RequestBody.Required, true),
		}
	}

	for _, r := range op.Responses {
		sc := r.StatusCode
		if sc == "" {
			sc = "200"
		}
		ep.Responses = append(ep.Responses, models.Response{
			StatusCode:  sc,
			Description: r.Description,
		})
	}

	for _, s := range op.Security {
		ep.Security = append(ep.Security, models.EndpointSecurity{SchemeName: s.SchemeName})
	}

	if op.Resilience != nil {
		if r := op.Resilience.Retry; r != nil {
			ep.Resilience.Retry = &models.RetryPolicy{MaxAttempts: r.MaxAttempts, Backoff: r.Backoff}
		}
		if c := op.Resilience.CB; c != nil {
			ep.Resilience.CircuitBreaker = &models.CircuitBreakerConfig{FailureThreshold: c.FailureThreshold, Timeout: c.Timeout}
		}
	}

	if op.Timeout != "" {
		ep.Resilience.Timeout = op.Timeout
	}

	if op.Idempotency != nil && op.Idempotency.Enabled {
		ep.Resilience.Idempotency = &models.IdempotencyConfig{
			Enabled:     true,
			KeyLocation: op.Idempotency.KeyLocation,
			KeyName:     op.Idempotency.KeyName,
			TTL:         op.Idempotency.TTL,
		}
	}

	return ep
}

func parseBoolDefault(s string, def bool) bool {
	b, err := strconv.ParseBool(s)
	if err != nil {
		return def
	}
	return b
}

func pickString(a, b, fallback string) string {
	if a != "" {
		return a
	}
	if b != "" {
		return b
	}
	return fallback
}

func isWSDLDeclaration(head []byte) bool {
	s := string(head)
	return strings.Contains(s, "wsdl:") || strings.Contains(s, "definitions") || strings.Contains(s, "soap:")
}

func isValidHTTPMethod(method string) bool {
	switch strings.ToLower(method) {
	case "get", "post", "put", "delete", "patch", "head", "options", "trace":
		return true
	}
	return false
}

func groupEndpointsByService(endpoints []models.Endpoint, spec *models.APISpecification) []models.Service {
	// simplified grouping
	return []models.Service{
		{
			Name:      "default",
			Endpoints: endpoints,
		},
	}
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
