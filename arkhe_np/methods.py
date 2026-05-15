import binsreg
import portsort
import lpdensity
import scpi_pkg

class ArkheNP:
    def __init__(self):
        self.methods = [
            "binsreg (Binscatter Methods)",
            "portsort (Portfolio Sorting)",
            "lpdensity (Local Polynomial Density)",
            "scpi (Synthetic Control Methods)"
        ]

    def get_supported_methods(self):
        return self.methods

    def run_binsreg(self, *args, **kwargs):
        """Wrapper for binsreg.binsreg"""
        return binsreg.binsreg(*args, **kwargs)

    def run_portsort(self, *args, **kwargs):
        """Wrapper for portsort.portsort"""
        return portsort.portsort(*args, **kwargs)

    def run_lpdensity(self, *args, **kwargs):
        """Wrapper for lpdensity.lpdensity"""
        return lpdensity.lpdensity(*args, **kwargs)

    def run_scpi(self, *args, **kwargs):
        """Wrapper for scpi_pkg.scpi"""
        return scpi_pkg.scpi(*args, **kwargs)
