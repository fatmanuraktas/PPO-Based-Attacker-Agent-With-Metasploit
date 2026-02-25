This repository contains an autonomous penetration testing agent trained using Proximal Policy Optimization (PPO). Unlike static scripts, this agent interacts directly with the Metasploit RPC (msfrpcd) to execute real-world exploits against a Metasploitable target within a Gymnasium-compliant environment.
🚀 Key Features

    Real-time Interaction: Connects to msfrpcd via SSL for live exploit execution.

    Action Masking: Implements logical constraints to prevent redundant or impossible attack vectors (e.g., preventing exploits before discovery scans).

    Time-Penalty Reward Shaping: Optimized reward function to prevent "Reward Hacking" and encourage the shortest path to compromise.

    Entropy-based Early Stopping: Prevents overfitting by monitoring the agent's strategy convergence (Entropy Loss).

🛠 Tech Stack

    RL Library: stable-baselines3 / sb3-contrib (Maskable PPO)

    Pentest Engine: Metasploit Framework (MSF RPC)

    Environment: Gymnasium (Custom Environment Wrapper)

    Target: Metasploitable2 / Custom Vulnerable Docker

📈 Training Metrics

The agent is trained to minimize Entropy Loss while maximizing Cumulative Reward. The use of Action Masking significantly reduces the state-action space, leading to faster convergence compared to vanilla RL approaches.
🛡 Academic & Research Context

This project serves as Phase 2 of a broader research initiative: GAN-Inspired Adversarial Self-Play for Autonomous Cyber Defense. While many RL agents operate in abstract simulations (like NASim), this framework focuses on the Reality Gap—bridging the space between neural network decisions and physical network packets.
📂 Installation & Usage

    Start Metasploit RPC:
    Bash

    msfrpcd -P yourpassword -S -a 127.0.0.1

    Configure Target: Update target_ip in training.py.

    Run Training:
    Bash

    python training.py
