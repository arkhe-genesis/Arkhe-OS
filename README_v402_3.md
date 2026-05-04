# Arkhe OS v∞.402.3 — Debye Vectorial Propagation

## Implementations
- `core/propagation/debye_vectorial.py`: Debye-Wolf integral for vectorial diffraction
- `core/validation/experimental_comparison.py`: Validation framework
- `config/experimental_data_substrate85_89.py`: Datasets 85 and 89
- `core/validation/run_experimental_validation.py`: Runner

## Updates
Added support for vectorial propagation to overcome limitations in paraxial approximations for numerical apertures (NA) > 0.3. Implemented realistic polarization and apodization matrices, paving the way for full Fresnel implementations.
