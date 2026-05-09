module arkhf
  use, intrinsic :: iso_c_binding
  implicit none
  private

  ! Constante do pacote
  integer(c_int), parameter :: CRAG_REQUEST_SIZE = 192

  ! Tipos C
  type, bind(C) :: CragRequest
     integer(c_int8_t) :: version
     integer(c_int8_t) :: method
     integer(c_int8_t) :: zone_id(4)
     integer(c_int8_t) :: query_hash(16)
     integer(c_int8_t) :: max_retrieved
     integer(c_int8_t) :: flags
     integer(c_int8_t) :: payload(168)
  end type CragRequest

  type, bind(C) :: FinalityLevel
     integer(c_int) :: value
  end type FinalityLevel
  integer(c_int), parameter :: PENDING = 0, L0 = 1, L1 = 2, L2 = 3

  interface
     subroutine crag_pack_request(req, buf) bind(C, name="crag_pack_request")
       import :: CragRequest, c_char
       type(CragRequest), intent(in) :: req
       character(kind=c_char), intent(out) :: buf(*)
     end subroutine

     function kolmogorov_gap(query, source, response) bind(C, name="kolmogorov_gap")
       import :: c_char, c_double
       character(kind=c_char), intent(in) :: query(*)
       character(kind=c_char), intent(in) :: source(*)
       character(kind=c_char), intent(in) :: response(*)
       real(c_double) :: kolmogorov_gap
     end function

     function gap_to_finality(gap) bind(C, name="gap_to_finality")
       import :: c_int, c_double
       real(c_double), value :: gap
       integer(c_int) :: gap_to_finality
     end function
  end interface

  public :: CragRequest, CRAG_REQUEST_SIZE, kolmogorov_gap, gap_to_finality, FinalityLevel, PENDING, L0, L1, L2
end module arkhf
