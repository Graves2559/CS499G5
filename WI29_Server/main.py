'''
main.py 

Author: Trinh Pham

This file will use an ASGI server (uvicorn in this case) to serve the FastAPI application.
'''

import uvicorn
from httpAPI import HttpAPI
from pyngrok import ngrok

import socket
import subprocess, signal, os, time

import config


# Main Sequence: Client ⇄ HTTPS ⇄ ngrok ⇄ HTTP ⇄ nginx ⇄ HTTP ⇄ uvicorn
def main():
    port = 8000 # private port for the local servers (Tunneling service meets with the ASGI server)



    # ||| Tunneling Service ||| (To connect to WAN, LAN, etc.)
    # Testing purposes
    # In this case, we might use ngrok to quickly create a secure tunnel to the local server 
    # without any of those random public URLs that change frequently.
    # If this is feasible, we may replace the Cloudflare entirely.

    """ import pyngrok
    public_tunnel = ngrok.connect(port, "http")
    print(f"\nPublic tunnel URL: {public_tunnel.public_url}\n")
    # Note: you will need to do the ngrok section within the README.md's "No Longer Used" section.
    """

    # Result: Ngrok does not work, unless you pay for its service. It will connect, but the UI
    # will not show unless you have a paid plan.

    # We will use cloudflare for all public tunneling needs instead of ngrok.

    # OFFICIAL and testing purposes
    # In this case, we use Cloudflare to create a secure tunnel to the local server.
    # The tradeoff is that since we will use free version,
    # the public URL will be randomly generated and may change each time the tunnel is established.
    # This means that any clients connecting to the server will need to use the new URL each time the tunnel is re-established.

    from pycloudflared import try_cloudflare
    try:
        public_url = try_cloudflare(port=port)
        print(f"\nPublic URL: {public_url}\n")
    except Exception as e:
        print(f"Failed to create Cloudflare tunnel: {e}")

    # ||| Proxy server |||
    # This section can be used to configure a reverse proxy if needed.
    # For example, you could use nginx to handle incoming requests through a (HTTP) proxy server
    # Typically done for load balancing (i.e., distributing incoming requests across multiple backend servers)

    # Right now, we put it on the same machine as the local server. For further extensions, we can 
    # use a separate machine for the proxy server. 
    # Potential: Servers (Backend services, NAS servers or DB servers, routing server, etc. )

    ''' 
        Types of proxy servers:
        source: https://www.pcmag.com/how-to/i-set-up-my-own-proxy-server-heres-why-and-how-you-can-do-it-yourself

        HTTP proxy: (What we are doing)
            The most common option is an HTTP proxy. Designed specifically for handling web traffic, 
            an HTTP proxy can block access to specific websites, filter content, or speed up browsing 
            through caching. 

        SOCK5 proxy: 
            A SOCK5 proxy can be a better fit if you need to handle different types of traffic, 
            such as FTP or peer-to-peer connections. Just be aware that these proxies tend to be slower 
            and don’t offer support for content filtering or caching. 

        Transparent proxy: 
            Transparent proxies, on the other hand, are typically deployed in networks where the end user 
            isn’t aware that a proxy is in use. They can be helpful for silently monitoring or 
            filtering traffic. These types of proxies tend to be easy to detect and bypass. 
            Moreover, they don’t offer any privacy benefits. 

    '''

    



    # ||| ASGI Server |||
    # HTTPS is terminated by ngrok; uvicorn just serves plain HTTP for the tunnel to forward to
    # host 0.0.0.0 binds all network interfaces so the ngrok agent (and LAN clients) can reach this server
    # reload=False: uvicorn's --reload spawns a second process that duplicates the listening
    # socket on macOS, which causes external connections to randomly get reset

    # In case ASGI server was suspended instead of properly shut down (didn't do Ctrl + C)
    if (is_port_in_use(port)): 
        if(config.TEST_MODE): print(f"Port {port} is in use, attempting to kill the process.")
        kill_process_on_port(port)
        if(config.TEST_MODE): print(f"Process on port {port} has been killed.")

    try:
        uvicorn.run(
            app = HttpAPI(),
            host="0.0.0.0",
            port=port,  # (LHS) port= is the syntax; (RHS) port is the local variable.
            reload=False,
            loop="asyncio",
            log_level="debug"
        )
    finally:
        print(f"Shutting down server on port {port}.")
        pass



def is_port_in_use(port: int, host: str = "0.0.0.0") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
            return False  # bind succeeded -> port was free
        except OSError:
            return True   # bind failed -> something's already listening

def kill_process_on_port(port: int, timeout: float = 3.0):
    result = subprocess.run(["lsof", "-ti", f":{port}"], capture_output=True, text=True)
    pids = result.stdout.split()
    for pid in pids:
        pid = int(pid)
        print(f"Port {port} is held by PID {pid} — killing it.")
        os.kill(pid, signal.SIGKILL)   # SIGKILL: works even on stopped/suspended processes

    # wait for the OS to actually release the port before returning
    deadline = time.time() + timeout
    while is_port_in_use(port) and time.time() < deadline:
        time.sleep(0.1)

    return bool(pids)


if __name__ == "__main__":
    main()
