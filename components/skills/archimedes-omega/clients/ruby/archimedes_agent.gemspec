Gem::Specification.new do |s|
  s.name        = 'archimedes_agent'
  s.version     = '1.0.0'
  s.summary     = 'Ruby client for Archimedes-Ω coherence agent'
  s.authors     = ['Arkhe Consortium']
  s.email       = 'contact@arkhe.network'
  s.files       = ['lib/archimedes_agent.rb']
  s.homepage    = 'https://github.com/arkhe/archimedes-agent'
  s.license     = 'MIT'
  s.add_runtime_dependency 'httparty', '~> 0.21'
end
