pub fn describe(value: &str) -> Result<String, String> {
    let port = config::parse_port(value).map_err(|error| error.to_string())?;
    Ok(format!("Endpoint: {}", formatting::endpoint(port)))
}
