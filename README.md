# Unifi IP Reservation Importer

A Python utility for easily importing and configuring static IP reservations with VLAN assignments on UniFi networking equipment.

## Features

- Bulk import of IP reservations from CSV file to UniFi controller
- Static IP address assignment with VLAN tagging
- Works with UDM Pro, UDM SE, and other UniFi controllers
- Secure credential management via separate secrets file
- Detailed logging and error reporting

## Requirements

- Python 3.6 or higher
- `requests` library (`pip install requests`)
- UniFi controller (UDM Pro, UDM SE, Cloud Key, etc.)
- Admin access to your UniFi controller

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/unifi-ip-reservation-importer.git
   cd unifi-ip-reservation-importer
   ```

2. Install the required Python package:
   ```
   pip install requests
   ```

3. Create your secrets file:
   ```
   cp secrets_example.py secrets.py
   ```

4. Edit `secrets.py` with your UniFi controller credentials

## CSV File Format

Create a CSV file with the following columns:

| VLAN | MAC | Client Name | IP |
|------|-----|-------------|------|
| 1 | 00:11:22:33:44:55 | Living Room TV | 192.168.1.50 |
| 2 | AA:BB:CC:DD:EE:FF | IoT Camera | 192.168.10.10 |

- **VLAN**: The VLAN ID number
- **MAC**: The device MAC address (format doesn't matter - the script normalizes it)
- **Client Name**: A friendly name for the device
- **IP**: The static IP address to assign

## Usage

1. Prepare your CSV file with the device information
2. Update the `CSV_PATH` in `unifi.py` to point to your file
3. Run the script:
   ```
   python unifi.py
   ```

## Notes

- The script will detect VLANs automatically from your UniFi controller configuration
- Make sure your UniFi networks are properly configured with VLANs before running
- For devices to use the assigned VLANs, you'll also need to configure:
  - Switch ports for wired devices
  - SSIDs with appropriate VLAN tags for wireless devices

## Security Considerations

- Keep your `secrets.py` file secure
- Add `secrets.py` to your `.gitignore` file if using Git
- Consider using a dedicated service account with limited permissions

## License

MIT 