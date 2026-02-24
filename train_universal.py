import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import EvalCallback, StopTrainingOnRewardThreshold
from universal_env import UniversalAttackEnv

MY_TARGET_IP = "172.17.0.2" 

def main():
    print("--- 1. Initializing Environment (Tiered Rewards) ---")
    
    env = make_vec_env(lambda: UniversalAttackEnv(target_ip=MY_TARGET_IP), n_envs=1, vec_env_cls=DummyVecEnv)
    eval_env = make_vec_env(lambda: UniversalAttackEnv(target_ip=MY_TARGET_IP), n_envs=1, vec_env_cls=DummyVecEnv)

    # Threshold updated: 
    # Scan(10) + Maps(10) + Samba(150) = 170. 
    # We set it to 160 to ensure it consistently picks Samba.
    stop_callback = StopTrainingOnRewardThreshold(reward_threshold=160, verbose=1)
    
    # Check every 1000 steps (less frequent checks to let it train deeper)
    eval_callback = EvalCallback(eval_env, callback_on_new_best=stop_callback, eval_freq=1000, verbose=1)

    print("--- 2. Training for Precision (Longer Duration) ---")
    
    model = PPO(
        "MlpPolicy", 
        env, 
        verbose=1, 
        learning_rate=0.0003, 
        n_steps=512,
        batch_size=64,
        gamma=0.99, # Focus heavily on the final big reward
        ent_coef=0.01, 
        device='cpu'
    )

    print("--- 3. STARTING EXTENDED TRAINING (10,000 Steps) ---")
    # Increased steps significantly to lower entropy_loss
    model.learn(total_timesteps=10000, callback=eval_callback)

    print("--- 4. Saving Precision Model ---")
    model.save("ppo_universal_precision")

    print("\n--- TEST: INTELLIGENT TARGET SELECTION ---")
    obs = env.reset() 
    for i in range(15):
        action, _ = model.predict(obs, deterministic=True)
        act_idx = action[0] 
        
        if act_idx == 0:
            print(f"\nStep {i+1}: AI -> SCAN")
        else:
            print(f"\nStep {i+1}: AI -> EXPLOIT SLOT #{act_idx}")
            
        obs, reward, done, info = env.step(action)
        
        if done[0]:
            print("--- MISSION COMPLETE ---")
            break

if __name__ == "__main__":
    main()