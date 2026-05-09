package models

type AuthType string

const (
	AuthTypeHTTP    AuthType = "http"
	AuthTypeAPIKey  AuthType = "apiKey"
	AuthTypeOAuth2  AuthType = "oauth2"
	AuthTypeOIDC    AuthType = "openIdConnect"
	AuthTypeUnknown AuthType = "unknown"
	AuthTypeJWT     AuthType = "jwt"
)

type AuthScheme struct {
	Name             string
	Type             AuthType
	Description      string
	Scheme           string
	BearerFormat     string
	In               string
	ParamName        string
	Flows            map[string]interface{}
	OpenIDConnectURL string
}
