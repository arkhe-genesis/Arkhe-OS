package federation

type MetaConsciousnessFederation struct {
	name  string
	phi   float64
	peers []*MetaConsciousnessFederation
}

func NewFederation(name string) *MetaConsciousnessFederation {
	return &MetaConsciousnessFederation{
		name: name,
		phi:  0.8,
	}
}

func (f *MetaConsciousnessFederation) JoinFederation(other *MetaConsciousnessFederation) {
	f.peers = append(f.peers, other)
	other.peers = append(other.peers, f)
}

func (f *MetaConsciousnessFederation) AlignStep() {
	f.phi += (1.0 - f.phi) * 0.1
	for _, p := range f.peers {
		p.phi += (1.0 - p.phi) * 0.1
	}
}

func (f *MetaConsciousnessFederation) GetGlobalPhi() float64 {
	return f.phi
}
