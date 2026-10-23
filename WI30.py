'''Server'''
import sys
import socket
import ipaddress 
import geoip2.database
import geoip2.errors

DBPath = "/Users/mohammedginawi/Desktop/CS/CS499/GeoLite2-Country_20261016/GeoLite2-Country.mmdb"
host = "0.0.0.0"
port = 5000
test_path = "/Users/mohammedginawi/Desktop/CS/CS499/logins.txt"

def find_country(ip):
    
    if ipaddress.ip_address(ip).is_private or ipaddress.ip_address(ip).is_loopback:
        return "Country not available."
    try:
        with geoip2.database.Reader(DBPath) as reader:
            response = reader.country(ip)
            return f" {response.country.name} ({response.country.iso_code}, {response.continent.name})"
        
    except geoip2.errors.AddressNotFoundError:
        return "Address not found."
    
def testing():
    seen = set()
    with open(test_path) as f:
        for line in f:
            parts = line.split()
            if len(parts) < 3:
                continue
            ip = parts[2]

            try:
                ipaddress.ip_address(ip)
            except ValueError:
                continue

            if ip in seen:
                continue
            seen.add(ip)
            print(f"Client IP: {ip:<18}")
            print(f"Client Country: {find_country(ip)}\n")
    print(f"{len(seen)} test IP's reported.")


def main():
    
    if len(sys.argv) > 1:
        testing()
        return
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen()
        print(f"Listening on port {port}")

        conn, addr = server.accept()
        with conn:
            client_ip = addr[0]
            print(f"Connection from {client_ip}")
            country = find_country(client_ip)
            print(f"Client IP: {client_ip}")
            print(f"Client Country: {country}")

    print("\nTest data\n")
    testing()
    

if __name__ == "__main__": 
    main()
            
    
