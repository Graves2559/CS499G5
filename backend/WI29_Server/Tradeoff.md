
Download:
1. mongoenv
2. (crossed) mkcert   (to generat a cert.pem and key.pem for localhost)
3. fastapi
4. Tailscale or ngrok

Ensure that the gitignore includes a way to ignore the private key of the fastAPI, so it doesn't get committed 

To activate: (Server) run the program inside the WI129 (not the certs) and then go to the browser and enter https://localhost:8443

To make it connect to the LAN, you need to change the cert.pem with the SAN (your LAN IP)
Connect (Client) via: https:// (LAN):8443
    Example: https://192.168.1.253:8443 

Note: private relay on iOS may be the resason why iPhone cannot connect. Turn it off for debugging purposes.
Note: Quit some donwloaded VPN, even if it is disconnected. It has a "kill switch" feature (a Network Lock) that filters traffic


Update: considering using tailscale or ngrok instead. Much more easier to connect to HTTPS rather than mkcert.
- The tailscale allows a mesh network, so it works for VPNs as well. 

ngrok config add-authtoken (AUTH_TOKEN)
- The client doesn't need to make janky configurations anymore. It easily connects to the website.
- More convenient to set up, but less secure.
- Seemingly provides a public address via https://hanky-drank-contend.ngrok-free.dev/

Tailscale
- Tailscale requires downloading of its app for a private network
- Allows only ones that are connected to said private IP address will be able to access it.
- Requires more set up.


How to use ngrok:
1. Server set up in different terminal: ngrok http 8000
2. Run the main program
