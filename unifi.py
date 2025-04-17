#!/usr/bin/env python3
"""
Unifi IP Reservation Importer

This script imports and configures static IP reservations with VLAN assignments
from a CSV file into a Unifi Dream Machine Pro or other Unifi controller.

Requirements:
    - Python 3.6+
    - requests library
    - A secrets.py file with your UniFi credentials (see secrets_example.py)
    - CSV file with device information
"""
import csv
import sys
import requests
import ipaddress
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Import credentials from secrets file
try:
    from secrets import UDM, USER, PASS, SITE
except ImportError:
    print("Error: secrets.py file not found")
    print("Please create a secrets.py file based on secrets_example.py")
    sys.exit(1)

# ───── CONFIG ───────────────────────────────────────────────────────────
CSV_PATH = "devices.csv"  # has VLAN,MAC,Client Name,IP columns
DEBUG    = True          # set to True for additional debug output
# ────────────────────────────────────────────────────────────────────────

# suppress self‑signed‑cert warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def main():
    # Setup session
    base    = f"https://{UDM}"
    login   = f"{base}/api/auth/login"
    prefix  = f"{base}/proxy/network/api/s/{SITE}"
    s       = requests.Session()
    s.headers.update({
        "Accept":       "application/json",
        "Content-Type": "application/json",
    })

    try:
        # 1) LOGIN
        print(f"Connecting to UniFi controller at {UDM}...")
        r = s.post(login, json={"username": USER, "password": PASS}, verify=False)
        r.raise_for_status()

        # 2) GET CSRF TOKEN
        r = s.get(f"{prefix}/self", verify=False)
        r.raise_for_status()
        csrf = r.headers.get("x-csrf-token")
        if not csrf:
            raise RuntimeError("No CSRF token; check UDM OS version")
        s.headers.update({"x-csrf-token": csrf})

        # 3) FETCH VLAN→NETWORK_ID MAP
        r = s.get(f"{prefix}/rest/networkconf", verify=False)
        r.raise_for_status()
        vlan_map = {}
        network_data = r.json().get("data", [])
        subnet_map = {}  # Store subnet info for each VLAN

        if DEBUG:
            print(f"Found {len(network_data)} networks in UniFi configuration")

        for net in network_data:
            # Special handling for the default network which might be VLAN 1
            if 'purpose' in net and net['purpose'] == 'corporate' and ('vlan' not in net or net.get('vlan') == 1):
                vlan_map[1] = net["_id"]
                subnet_map[1] = net.get("ip_subnet", "")
                if DEBUG:
                    print(f"Mapped Main LAN (VLAN 1) to network ID: {net['_id']}")
            elif 'vlan' in net:
                vlan_id = int(net.get("vlan"))
                vlan_map[vlan_id] = net["_id"]
                subnet_map[vlan_id] = net.get("ip_subnet", "")
                if DEBUG:
                    print(f"Mapped VLAN {vlan_id} to network ID: {net['_id']} (Subnet: {subnet_map[vlan_id]})")

        if DEBUG:
            print("Available VLANs:", sorted(list(vlan_map.keys())))

        # 4) PUSH STATIC‑DHCP + VLAN INFO
        api = f"{prefix}/rest/user"
        
        try:
            with open(CSV_PATH, newline="") as f:
                reader = csv.DictReader(f)
                if not all(field in reader.fieldnames for field in ["VLAN", "MAC", "Client Name", "IP"]):
                    print(f"Error: CSV file must contain VLAN, MAC, Client Name, and IP columns")
                    return
                
                success_count = 0
                error_count = 0
                
                for row in reader:
                    vlan_num = int(row["VLAN"])
                    net_id   = vlan_map.get(vlan_num)
                    if not net_id:
                        print(f"⚠️  Unknown VLAN {vlan_num} for MAC {row['MAC']}; skipping")
                        error_count += 1
                        continue

                    raw = row["MAC"].strip()
                    mac = raw.replace('-', ':').replace('.', ':').upper()
                    ip_address = row["IP"].strip()

                    # Verify IP is valid
                    try:
                        ipaddress.ip_address(ip_address)
                    except ValueError:
                        print(f"⚠️  Invalid IP {ip_address} for MAC {mac}; skipping")
                        error_count += 1
                        continue

                    payload = {
                        "mac":          mac,
                        "fixed_ip":     ip_address,
                        "name":         row["Client Name"].strip(),
                        "network_id":   net_id,
                        "use_fixedip":  True,
                        "note":         f"Added by unifi.py script",
                        "vlan_enabled": True,
                        "vlan":         vlan_num
                    }

                    if DEBUG:
                        print(f"Setting static IP for {payload['name']} ({payload['mac']}) to {payload['fixed_ip']} on VLAN {vlan_num}")

                    resp = s.post(api, json=payload, verify=False)
                    if resp.ok:
                        print(f"✅ {payload['mac']} → {payload['fixed_ip']} (VLAN {vlan_num})")
                        success_count += 1
                    else:
                        print(f"❌ {payload['mac']}: {resp.text}")
                        error_count += 1
                
                print(f"\nSummary: {success_count} devices configured successfully, {error_count} errors")
                
        except FileNotFoundError:
            print(f"Error: CSV file '{CSV_PATH}' not found")
            return

    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # 5) LOGOUT
        try:
            s.post(f"{base}/api/auth/logout", verify=False)
            print("Logged out of UniFi controller")
        except:
            pass

if __name__ == "__main__":
    main()