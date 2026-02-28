import argparse
import sys
import os
from dotenv import load_dotenv
from src.utils.logger import log_experiment, ActionType
import subprocess

load_dotenv()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target_dir", type=str, required=True)
    args = parser.parse_args()
    
    if not os.path.exists(args.target_dir):
        print(f"❌ Dossier {args.target_dir} introuvable.")
        sys.exit(1)
    
    print(f"🚀 DEMARRAGE SUR : {args.target_dir}")
    
    log_experiment(
        agent_name="System",
        model_used="N/A",
        action=ActionType.ANALYSIS,
        details={
            "target_dir": args.target_dir,
            "input_prompt": f"System startup with target directory: {args.target_dir}",
            "output_response": "System initialized successfully"
        },
        status="SUCCESS"
    )
    
    print("✅ MISSION_COMPLETE")
    
    # =========================================================================
    # APPELS DES 3 SCRIPTS (AJOUTÉS ICI)
    # =========================================================================
    
    
    # Appel du script 2 : test_all_files.py
    result = subprocess.run([sys.executable, "test_all_files.py"], 
                          capture_output=False)
    if result.returncode != 0:
        print("❌ Erreur lors des tests")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("✅ ÉTAPE 3/3 : VÉRIFICATION DE LA QUALITÉ DES DONNÉES")
    print("=" * 70)
    
    # Appel du script 3 : check_data_quality.py
    result = subprocess.run([sys.executable, "check_data_quality.py"], 
                          capture_output=False)
    if result.returncode != 0:
        print("⚠️  Des problèmes de qualité ont été détectés")
    
    print("\n" + "=" * 70)
    print("🎉 PROCESSUS COMPLET TERMINÉ !")
    print("=" * 70)

if __name__ == "__main__":
    main()