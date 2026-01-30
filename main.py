#!/usr/bin/env python3
# main.py - Point d'entrée principal du système Refactoring Swarm

import argparse
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from src.utils.logger import log_experiment, ActionType
from src.agents.auditor import AuditorAgent
from src.agents.fixer import FixerAgent
from src.agents.judge import JudgeAgent

# Charger les variables d'environnement
load_dotenv()


def main():
    """
    Point d'entrée principal - Sera appelé par le Bot de Correction avec:
    python main.py --target_dir "./sandbox/dataset_inconnu"
    """
    
    # Parser les arguments de ligne de commande
    parser = argparse.ArgumentParser(description="Refactoring Swarm - TP IGL 2025-2026")
    parser.add_argument("--target_dir", type=str, required=True, 
                        help="Dossier contenant le code à analyser et corriger")
    parser.add_argument("--max_iterations", type=int, default=10,
                        help="Nombre maximum d'itérations de la boucle (défaut: 10)")
    args = parser.parse_args()

    # Vérifier que le dossier cible existe
    target_dir = Path(args.target_dir)
    if not target_dir.exists():
        print(f"❌ ERREUR: Dossier {args.target_dir} introuvable.")
        sys.exit(1)

    print("\n" + "="*70)
    print("🚀 REFACTORING SWARM - DÉMARRAGE")
    print("="*70)
    print(f"📂 Dossier cible: {args.target_dir}")
    print(f"🔄 Itérations max: {args.max_iterations}")
    print("="*70 + "\n")

    # Logger le démarrage du système
    log_experiment(
        agent_name="System",
        model_used="N/A",
        action=ActionType.ANALYSIS,
        details={
            "input_prompt": f"Starting Refactoring Swarm on {args.target_dir}",
            "output_response": f"System initialized with max {args.max_iterations} iterations",
            "target_directory": str(target_dir)
        },
        status="SUCCESS"
    )

    # Initialiser les agents
    print("🔧 Initialisation des agents...")
    try:
        auditor = AuditorAgent()
        fixer = FixerAgent()
        judge = JudgeAgent()
        print("✅ Agents initialisés avec succès\n")
    except Exception as e:
        print(f"❌ ERREUR lors de l'initialisation des agents: {e}")
        sys.exit(1)

    # Trouver tous les fichiers Python à analyser
    python_files = list(target_dir.glob("*.py"))
    
    # Filter out test files - only analyze source files
    source_files = [f for f in python_files if not f.name.startswith("test_")]
    
    if not source_files:
        print(f"⚠️  Aucun fichier Python source trouvé dans {target_dir}")
        print("✅ MISSION_COMPLETE (rien à faire)")
        return

    print(f"📝 {len(source_files)} fichier(s) Python source trouvé(s):")
    for f in source_files:
        print(f"   - {f.name}")
    print()

    # 🔄 BOUCLE PRINCIPALE (max 10 itérations pour éviter les boucles infinies)
    iteration = 0
    all_tests_passed = False

    while iteration < args.max_iterations and not all_tests_passed:
        iteration += 1
        print("\n" + "="*70)
        print(f"🔄 ITÉRATION {iteration}/{args.max_iterations}")
        print("="*70 + "\n")

        # ============================================================
        # ÉTAPE 1: AUDITOR - Analyser le code
        # ============================================================
        print("🔍 [ÉTAPE 1/3] AUDITOR - Analyse du code...")
        print("-"*70)
        
        auditor_reports = {}
        for py_file in source_files:
            # Skip test files - Auditor only analyzes source files
            if py_file.name.startswith("test_"):
                print(f"   ⏭️  {py_file.name} ignoré (fichier de test)")
                continue
                
            print(f"   📄 Analyse de {py_file.name}...")
            try:
                # Pass only the filename, not the full path
                # Auditor expects files relative to sandbox
                report = auditor.analyze_file(py_file.name)
                auditor_reports[py_file] = report
                print(f"   ✅ {py_file.name} analysé")
            except Exception as e:
                print(f"   ❌ Erreur sur {py_file.name}: {e}")
                auditor_reports[py_file] = {"status": "ERROR", "error": str(e)}
        
        print(f"\n✅ Auditor terminé - {len(auditor_reports)} fichier(s) analysé(s)\n")

        # ============================================================
        # ÉTAPE 2: FIXER - Corriger le code
        # ============================================================
        print("🔧 [ÉTAPE 2/3] FIXER - Correction du code...")
        print("-"*70)
        
        for py_file, report in auditor_reports.items():
            if report.get("status") == "SUCCESS":
                print(f"   🛠️  Correction de {py_file.name}...")
                try:
                    # Pass the LLM analysis to the Fixer
                    llm_analysis = report.get("llm_analysis", "No analysis available")
                    # Fixer also expects Path object
                    fixer.run(Path("sandbox") / py_file.name, llm_analysis, overwrite=True)
                    print(f"   ✅ {py_file.name} corrigé")
                except Exception as e:
                    print(f"   ❌ Erreur sur {py_file.name}: {e}")
            else:
                print(f"   ⏭️  {py_file.name} ignoré (erreur d'audit)")
        
        print(f"\n✅ Fixer terminé\n")

        # ============================================================
        # ÉTAPE 3: JUDGE - Exécuter les tests
        # ============================================================
        print("⚖️  [ÉTAPE 3/3] JUDGE - Exécution des tests...")
        print("-"*70)
        
        test_result = judge.execute_tests(str(target_dir))
        judge.print_summary(test_result)

        # ============================================================
        # DÉCISION: Continuer ou arrêter ?
        # ============================================================
        if test_result['all_passed']:
            all_tests_passed = True
            print("\n🎉 SUCCÈS! Tous les tests passent!")
            print("➡️  La boucle s'arrête - Mission accomplie!\n")
        else:
            print(f"\n⚠️  {test_result['failed']} test(s) échoué(s)")
            if iteration < args.max_iterations:
                print(f"➡️  Redémarrage de la boucle (itération {iteration + 1})...\n")
            else:
                print(f"⚠️  Limite d'itérations atteinte ({args.max_iterations})")
                print("➡️  Arrêt de la boucle\n")

    # ============================================================
    # RÉSUMÉ FINAL
    # ============================================================
    print("\n" + "="*70)
    print("📊 RÉSUMÉ FINAL")
    print("="*70)
    print(f"Itérations effectuées: {iteration}/{args.max_iterations}")
    print(f"Fichiers traités: {len(source_files)}")
    
    if all_tests_passed:
        print("\n✅ STATUS: MISSION_COMPLETE")
        print("🎯 Tous les tests unitaires passent!")
    else:
        print("\n⚠️  STATUS: MISSION_INCOMPLETE")
        print(f"❌ {test_result.get('failed', 0)} test(s) encore en échec")
    
    print("="*70 + "\n")

    # Logger la fin du système
    log_experiment(
        agent_name="System",
        model_used="N/A",
        action=ActionType.ANALYSIS,
        details={
            "input_prompt": f"Complete Refactoring Swarm process on {args.target_dir}",
            "output_response": f"Process completed after {iteration} iterations. All tests passed: {all_tests_passed}",
            "iterations_used": iteration,
            "all_tests_passed": all_tests_passed
        },
        status="SUCCESS" if all_tests_passed else "PARTIAL"
    )


if __name__ == "__main__":
    main()