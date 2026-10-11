use anyhow::{Context, Result};

pub fn parse_port(value: &str) -> Result<u16> {
    value.parse().context("port must be an integer between 0 and 65535")
}
