import gymnasium as gym
from stable_baselines3 import PPO
from thm_env import THMUniversalEnv
import os

# --- TRYHACKME CONFIG ---
# TryHackMe'de makineyi başlat ve verilen IP'yi buraya yaz
TARGET_IP = "192.168.139.227"  
MODEL_PATH = "logs/best_model.zip" # Eğittiğin Ninja Model

def main():
    print(f"--- STARTING OPERATION ON {TARGET_IP} ---")
    
    # 1. Setup Environment
    env = THMUniversalEnv(target_ip=TARGET_IP)
    
    # 2. Load the Brain
    if not os.path.exists(MODEL_PATH):
        print("Model bulunamadı! Lütfen yolu kontrol et.")
        return
    
    model = PPO.load(MODEL_PATH)
    
    # 3. Execution Loop
    obs, _ = env.reset()
    
    # Ajanın 20 hamle hakkı var
    for i in range(20):
        action, _ = model.predict(obs, deterministic=True)
        
        # Action Decoding for Print
        if action == 0: act_name = "SCAN"
        else: act_name = f"EXPLOIT SLOT {action}"
        
        print(f"\nStep {i+1}: AI Chose -> {act_name}")
        
        obs, reward, done, truncated, info = env.step(action)
        
        if done:
            print("\n--- MISSION ACCOMPLISHED ---")
            break

if __name__ == "__main__":
    main()