import http.client, requests, json, os, argparse
from datetime import datetime

def get_addr(adapter):
    response = requests.get('https://api.ipify.org?format=json')
    ipv4_addr = ""
    if response.status_code == 200:
       ipv4_data = json.loads(response.text)
       ipv4_addr = ipv4_data["ip"]
    else:
        print(f"Failed to retrieve IPv4 address. Status code: {response.status_code}")

    # Aquire the permanent, publically addressable ipv6 address of the specified adapter
    ipv6_addr = os.system(f'ip -6 addr show dev {adapter} mngtmpaddr | grep -oE "([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}"')
    #ipv6_addr = "2600:1702:59d8:ac80:be24:11ff:fee4:2418" #FIXME: Test case
    
    print(f"\033[94m IPv4: {ipv4_addr}\033[0m")
    print(f"\033[94m IPv6: {ipv6_addr}\033[0m")
    while True:
        user_input = input("Are these values correct? (Y/n) ").lower()
        if user_input == '' or user_input == 'y':
            return {'ipv4_addr': ipv4_addr, 'ipv6_addr': ipv6_addr} 
        elif user_input == 'n':
            return False
        else:
            print("Invalid input. Please enter 'y' or 'n'.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-k', '--api-key', type=str, required=True, help="Cloudflare API Key")
    parser.add_argument('-a', '--adapter', type=str, required=False, help="Adapter name for IPv6 address detection")
    parser.add_argument('-v', '--verbose', action="store_true", required=False, help="Increase verbosity")
    parser.add_argument('-n', '--dry-run', action="store_true", required=False, help="Show changes without applying")

    args = parser.parse_args()
    if args.verbose:
        print(f"\033[94m Adapter: {args.adapter if args.adapter else 'N/A'} \033[0m")
    
    addrs = get_addr(adapter=args.adapter)
    if not addrs: exit()

    # Aquire zones
    conn = http.client.HTTPSConnection("api.cloudflare.com")
    
    headers = {
        'Content-Type': "application/json",
        'Authorization': f"Bearer {args.api_key}"
        }
    
    conn.request("GET", "/client/v4/zones", headers=headers)
    
    res = conn.getresponse()
    data = res.read()

    data = json.loads(data.decode())['result']
    
    if not data: raise Exception("Error fetching zone data: Check API key")

    zone_ids = [{'name': d['name'], 'id': d['id']} for d in data]
    dns_ids = []
    
    # Get the ID of each record that is needed to be changed
    for i in zone_ids:
        conn.request("GET", f"/client/v4/zones/{i['id']}/dns_records", headers=headers)
        records = json.loads(conn.getresponse().read().decode())['result']
        for r in records:
            if r['content'] != addrs['ipv4_addr'] and r['type'] == "A":
                if args.verbose: print(f'{r['name']} {r['type']} needs to be updated')
                dns_ids.append({"id": r['id'], "zone_id": r['zone_id'], "name": r['name'], "type": r['type'], "content": r['content']})
                continue
            if r['content'] != addrs['ipv6_addr'] and r['type'] == "AAAA" and args.adapter:
                if args.verbose: print(f'{r['name']} {r['type']} needs to be updated')
                dns_ids.append({"id": r['id'], "zone_id": r['zone_id'], "name": r['name'], "type": r['type'], "content": r['content']})
                continue

    
    # Modify the records

    if not dns_ids: 
        print("Already up to date!")
        exit()

    print(dns_ids)

    for i in dns_ids:
        if args.verbose or args.dry_run: print(f"Updating {i['name']}!")
        if not args.dry_run:
            json_body = json.dumps({'content': addrs['ipv4_addr'] if i['type'] == 'A' else addrs['ipv6_addr'], 'comment': f"Updated on {datetime.now().isoformat()}"})
            conn.request("PATCH", f"/client/v4/zones/{i['zone_id']}/dns_records/{i['id']}", body=json_body, headers=headers)
    
    print("\033[92m Finished updating\033[0m")

if __name__ == "__main__":
    main()
