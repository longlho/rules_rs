fn main() {
    let port = std::env::args().nth(1).unwrap_or_else(|| "8080".to_owned());
    match service::describe(&port) {
        Ok(message) => println!("{message}"),
        Err(message) => {
            eprintln!("{message}");
            std::process::exit(1);
        }
    }
}
