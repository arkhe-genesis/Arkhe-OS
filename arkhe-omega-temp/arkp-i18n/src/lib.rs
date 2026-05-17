
use fluent::{FluentBundle, FluentResource};
use unic_langid::LanguageIdentifier;
use std::collections::HashMap;

pub struct I18n {
    bundles: HashMap<LanguageIdentifier, FluentBundle<FluentResource>>,
}

impl I18n {
    pub fn new() -> Self {
        let mut bundles = HashMap::new();

        let en_us: LanguageIdentifier = "en-US".parse().unwrap();
        let mut bundle_en = FluentBundle::new(vec![en_us.clone()]);
        bundle_en.add_resource(FluentResource::try_new(include_str!("../locales/en-US/main.ftl").to_string()).unwrap()).unwrap();
        bundles.insert(en_us, bundle_en);

        let pt_br: LanguageIdentifier = "pt-BR".parse().unwrap();
        let mut bundle_pt = FluentBundle::new(vec![pt_br.clone()]);
        bundle_pt.add_resource(FluentResource::try_new(include_str!("../locales/pt-BR/main.ftl").to_string()).unwrap()).unwrap();
        bundles.insert(pt_br, bundle_pt);

        Self { bundles }
    }

    pub fn get(&self, lang: &LanguageIdentifier, id: &str, args: Option<&fluent::FluentArgs>) -> String {
        let default_lang: LanguageIdentifier = "en-US".parse().unwrap();
        let bundle = self.bundles.get(lang).or_else(|| self.bundles.get(&default_lang)).unwrap();
        let mut errors = vec![];
        let msg = bundle.get_message(id).unwrap();
        let pattern = msg.value().expect("Message has no value");
        bundle.format_pattern(pattern, args, &mut errors).to_string()
    }
}
