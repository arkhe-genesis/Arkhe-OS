program main
  use arkhf
  use, intrinsic :: iso_c_binding
  implicit none
  real(c_double) :: gap
  integer(c_int) :: fin
  character(len=:), allocatable :: query, source, response
  query = "What is truth?" // c_null_char
  source = "Plato's cave" // c_null_char
  response = "Truth is..." // c_null_char
  gap = kolmogorov_gap(query, source, response)
  fin = gap_to_finality(gap)
  print *, "Gap:", gap, " Finality:", fin
end program
