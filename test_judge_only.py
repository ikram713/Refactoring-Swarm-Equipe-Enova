#!/usr/bin/env python3
# test_judge_only.py - Test simple du Judge uniquement

import sys
from pathlib import Path
from src.agents.judge import JudgeAgent

def main():
    print("\n" + "="*70)
    print("🧪 TEST DU JUDGE AGENT UNIQUEMENT")
    print("="*70)
    
    # Créer le Judge
    judge = JudgeAgent()
    
    # Tester sur le dossier sandbox (chemin absolu)
    sandbox_dir = "./sandbox"
    
    print(f"\n📂 Exécution des tests dans: {sandbox_dir}")
    print("-"*70)
    
    # Exécuter les tests
    result = judge.execute_tests(sandbox_dir)
    
    # Afficher les résultats
    judge.print_summary(result)
    
    # Verdict
    if result['all_passed']:
        print("\n✅ SUCCÈS: Tous les tests passent!")
        return 0
    else:
        print(f"\n❌ ÉCHEC: {result['failed']} test(s) ont échoué")
        print(f"Détails: {result['error_details']}")
        return 1

if __name__ == "__main__":
    sys.exit(main())