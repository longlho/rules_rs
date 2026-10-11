pub fn https_port() -> u16 {
    logging::parse_port("443").expect("a literal port is valid")
}

#[cfg(test)]
mod tests {
    use super::https_port;

    #[test]
    fn obtains_a_port_through_the_first_party_dependency() {
        assert_eq!(https_port(), 443);
    }
}
