# substrates/494-gw-atomic/fisher_estimator.jl
using LinearAlgebra, SpecialFunctions

module GWFisher

export compute_fisher_information, optimal_evolution_time, min_atoms_required

const h_bar = 1.054571817e-34  # J*s
const c = 299792458             # m/s

struct GWParameters
    amplitude::Float64    # h (strain)
    frequency::Float64    # omega (Hz)
    polarization::Char    # '+' ou 'x'
end

struct AtomicSystem
    transition_frequency::Float64  # omega0 (Hz)
    natural_linewidth::Float64     # Gamma (Hz)
    quality_factor::Float64        # Q = omega0/Gamma
    num_atoms::Int64
    cloud_temperature::Float64     # Kelvin
end

function compute_fisher_information(gw::GWParameters, atom::AtomicSystem,
                                   evolution_time::Float64)::Float64
    k = atom.transition_frequency / c  # numero de onda

    # Fator de amplificacao (k/omega)
    amplification = k / gw.frequency

    # Numero esperado de fotoes emitidos no tempo T
    N_photons = atom.num_atoms * (1 - exp(-atom.natural_linewidth * evolution_time))

    # Funcao de dependencia angular g(theta, phi) para polarizacao '+'
    # Fig. 1(b) do artigo: padrao quadrupolar
    function g_plus(theta, phi)
        return cos(theta/2)^2 * cos(2*phi)
    end

    # Integracao sobre angulo solido (aproximacao: direcao otima)
    g_optimal = g_plus(0.0, 0.0)  # Maximo: direcao de propagacao da GW

    # Fisher Information
    F = N_photons * (amplification * gw.amplitude * g_optimal)^2

    return F
end

function optimal_evolution_time(atom::AtomicSystem)::Float64
    # T_opt ~ 1/Gamma (uma vida util do estado excitado)
    return 1.0 / atom.natural_linewidth
end

function min_atoms_required(gw::GWParameters, atom::AtomicSystem,
                           target_snr::Float64 = 5.0)::Int64
    T_opt = optimal_evolution_time(atom)
    F = compute_fisher_information(gw, atom, T_opt)

    # SNR^2 = N_atoms * F (para medicoes independentes)
    N_min = ceil(Int64, target_snr^2 / max(F, 1e-30))

    return max(N_min, 1)
end

# Teste com parametros do artigo
function test_strontium87()
    # Sr-87: Q ~ 10^17, transicao de relogio
    atom = AtomicSystem(
        4.29e14,    # omega0 ~ 429 THz (698 nm)
        4.29e-3,    # Gamma ~ 4.29 mHz
        1.0e17,     # Q = 10^17
        10^7,       # 10 milhoes de atomos
        1.0e-6      # 1 uK
    )

    # GW de milihertz (LISA band)
    gw = GWParameters(1e-21, 1e-3, '+')

    T_opt = optimal_evolution_time(atom)
    F = compute_fisher_information(gw, atom, T_opt)
    N_min = min_atoms_required(gw, atom)

    println("[494-GW-ATOMIC] Sr-87: T_opt = $(round(T_opt, digits=2)) s")
    println("[494-GW-ATOMIC] Fisher = $(round(F, digits=6))")
    println("[494-GW-ATOMIC] N_min = $(N_min) atomos")
end

end # module