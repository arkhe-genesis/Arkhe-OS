#ifndef ArkheCoreShared_h
#define ArkheCoreShared_h

#include <stdint.h>

char* arkhe_calculate_phi_c_json(const char* metrics_json);
char* arkhe_generate_seal(const char* event_type, const char* payload_json);
char* arkhe_verify_constitutional_compliance(const char* operation, const char* principles_json, const char* context_json);
void arkhe_free_string(char* s);

#endif /* ArkheCoreShared_h */
