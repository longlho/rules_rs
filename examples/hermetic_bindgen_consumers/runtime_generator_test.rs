mod runtime_linking;

use std::collections::BTreeSet;

fn functions(source: &str) -> BTreeSet<String> {
    syn::parse_file(source)
        .unwrap()
        .items
        .into_iter()
        .filter_map(|item| match item {
            syn::Item::ForeignMod(module) => Some(module.items),
            _ => None,
        })
        .flatten()
        .filter_map(|item| match item {
            syn::ForeignItem::Fn(function) => Some(function.sig.ident.to_string()),
            _ => None,
        })
        .collect()
}

fn symbols(path: &std::path::Path) -> BTreeSet<String> {
    let source = std::fs::read_to_string(path).unwrap();
    let syntax = syn::parse_file(&source).unwrap();
    let syn::Item::Macro(item) = &syntax.items[0] else {
        panic!()
    };
    functions(&format!("unsafe extern \"C\" {{ {} }}", item.mac.tokens))
}

#[test]
fn preserves_every_header_symbol() {
    let source = include_str!("aic_bindings.rs");
    let mut expected: BTreeSet<_> = functions(source)
        .into_iter()
        .filter(|name| name.starts_with("aic_"))
        .collect();
    expected.insert("aic_set_sdk_wrapper_id".into());
    assert_eq!(expected.len(), 38);
    let output = std::path::PathBuf::from(std::env::var_os("TEST_TMPDIR").unwrap())
        .join("header_symbols.rs");
    let bindings = runtime_linking::generate_from_source(source, &output);
    assert_eq!(symbols(&output), expected);
    assert!(
        !functions(&bindings)
            .iter()
            .any(|name| name.starts_with("aic_"))
    );
}

#[test]
fn preserves_other_foreign_items_and_repeated_symbols() {
    let source = r#"
        unsafe extern "C" {
            pub fn aic_probe(value: *const u32) -> u32;
            pub fn other_probe();
            pub static OTHER: u32;
            pub type Other;
        }
    "#;
    let output = std::path::PathBuf::from(std::env::var_os("TEST_TMPDIR").unwrap())
        .join("runtime_symbols.rs");
    for _ in 0..3 {
        let bindings = runtime_linking::generate_from_source(source, &output);
        assert_eq!(functions(&bindings), BTreeSet::from(["other_probe".into()]));
        let syntax = syn::parse_file(&bindings).unwrap();
        let syn::Item::ForeignMod(module) = &syntax.items[0] else {
            panic!()
        };
        assert!(
            module
                .items
                .iter()
                .any(|item| matches!(item, syn::ForeignItem::Static(_)))
        );
        assert!(
            module
                .items
                .iter()
                .any(|item| matches!(item, syn::ForeignItem::Type(_)))
        );
        assert_eq!(
            symbols(&output),
            BTreeSet::from(["aic_probe".into(), "aic_set_sdk_wrapper_id".into(),])
        );
    }
}
