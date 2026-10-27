pub fn sockets() -> Result<Vec<netstat2::SocketInfo>, netstat2::error::Error> {
    netstat2::get_sockets_info(
        netstat2::AddressFamilyFlags::IPV4,
        netstat2::ProtocolFlags::TCP,
    )
}
