#include "arkhe/merkabah/geometry.hpp"
#include <cmath>
#include <sstream>

namespace arkhe::merkabah {

MerkabahGeometry::MerkabahGeometry(double scale) : scale_(scale) {
    base_solar_ = {{ {1,1,1}, {-1,-1,1}, {-1,1,-1}, {1,-1,-1} }};
    base_lunar_ = {{ {-1,-1,-1}, {1,1,-1}, {1,-1,1}, {-1,1,1} }};
    for(auto& p : base_solar_) for(auto& c : p) c *= scale;
    for(auto& p : base_lunar_) for(auto& c : p) c *= scale;
}

std::vector<std::array<double,3>> MerkabahGeometry::rotate_y(
    const std::vector<std::array<double,3>>& pts, double angle) {
    std::vector<std::array<double,3>> out;
    double c = std::cos(angle), s = std::sin(angle);
    for(const auto& p : pts) {
        out.push_back({ c*p[0] + s*p[2], p[1], -s*p[0] + c*p[2] });
    }
    return out;
}

MerkabahFrame MerkabahGeometry::from_state(double time, double r, double psi,
                                            double energy, bool hesitating,
                                            const core::Clifford4D::Multivector&) {
    MerkabahFrame frame;
    frame.timestamp = time;
    frame.coherence = r;
    frame.global_phase = psi;
    frame.energy = energy;
    frame.hesitating = hesitating;

    double rot_speed = 0.5 + r * 2.0;
    double angle_solar = time * rot_speed;
    // double angle_lunar = -time * rot_speed * 1.2;

    frame.solar = rotate_y(base_solar_, angle_solar);
    frame.lunar = rotate_y(base_lunar_, -time * rot_speed * 1.2);

    // Separação na hesitação
    double separation = hesitating ? 0.3 * std::sin(time * 3.0) : 0.0;
    for(auto& p : frame.solar) p[1] += separation;
    for(auto& p : frame.lunar) p[1] -= separation;

    // Octaedro central
    frame.octahedron.clear();
    for(int i=0; i<6; i++) {
        int is = i % 4;
        int il = (i + 1) % 4;
        std::array<double,3> mid;
        for(int k=0; k<3; k++) mid[k] = (frame.solar[is][k] + frame.lunar[il][k]) * 0.5;
        frame.octahedron.push_back(mid);
    }

    frame.rotation = angle_solar;
    return frame;
}

std::string MerkabahFrame::to_json() const {
    std::stringstream ss;
    ss << "{";
    ss << "\"timestamp\":" << timestamp << ",";
    ss << "\"coherence\":" << coherence << ",";
    ss << "\"phase\":" << global_phase << ",";
    ss << "\"energy\":" << energy << ",";
    ss << "\"hesitating\":" << (hesitating ? "true" : "false") << ",";
    ss << "\"solar\":[";
    for(size_t i=0; i<solar.size(); i++) {
        ss << "[" << solar[i][0] << "," << solar[i][1] << "," << solar[i][2] << "]";
        if(i+1<solar.size()) ss << ",";
    }
    ss << "],\"lunar\":[";
    for(size_t i=0; i<lunar.size(); i++) {
        ss << "[" << lunar[i][0] << "," << lunar[i][1] << "," << lunar[i][2] << "]";
        if(i+1<lunar.size()) ss << ",";
    }
    ss << "]}";
    return ss.str();
}

} // namespace arkhe::merkabah
