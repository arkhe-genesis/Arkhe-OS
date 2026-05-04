package arkhgo

/*
#cgo LDFLAGS: -L.. -larkhe -lz
#include <stdlib.h>
#include <string.h>
#include "../arkhe.h"
*/
import "C"
import "unsafe"

type FinalityLevel int

const (
	Pending FinalityLevel = iota
	L0
	L1
	L2
)

type CragRequest struct {
	Version       uint8
	Method        uint8
	ZoneID        [4]byte
	QueryHash     [16]byte
	MaxRetrieved  uint8
	Flags         uint8
	Payload       [168]byte
}

func PackRequest(req *CragRequest) [C.CRAG_REQUEST_SIZE]byte {
	var cReq C.CragRequest
	cReq.version = C.uint8_t(req.Version)
	cReq.method  = C.uint8_t(req.Method)

    // Use C.memcpy since types do not match exactly in Go
    C.memcpy(unsafe.Pointer(&cReq.zone_id[0]), unsafe.Pointer(&req.ZoneID[0]), 4)
    C.memcpy(unsafe.Pointer(&cReq.query_hash[0]), unsafe.Pointer(&req.QueryHash[0]), 16)
    C.memcpy(unsafe.Pointer(&cReq.payload[0]), unsafe.Pointer(&req.Payload[0]), 168)

	cReq.max_retrieved = C.uint8_t(req.MaxRetrieved)
	cReq.flags = C.uint8_t(req.Flags)

	var buf [C.CRAG_REQUEST_SIZE]C.uint8_t
	C.crag_pack_request(&cReq, &buf[0])
	return *(*[192]byte)(unsafe.Pointer(&buf))
}

func KolmogorovGap(query, source, response string) float64 {
	cQuery := C.CString(query)
	cSource := C.CString(source)
	cResponse := C.CString(response)
	defer C.free(unsafe.Pointer(cQuery))
	defer C.free(unsafe.Pointer(cSource))
	defer C.free(unsafe.Pointer(cResponse))
	return float64(C.kolmogorov_gap(cQuery, cSource, cResponse))
}

func GapToFinality(gap float64) FinalityLevel {
	return FinalityLevel(C.gap_to_finality(C.double(gap)))
}
