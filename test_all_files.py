"""
TEST ALL FILES IN SANDBOX
=========================
Ce script teste automatiquement TOUS les fichiers Python du sandbox.
Pour chaque fichier : Auditor analyse → Fixer corrige

Author: Quality & Data Manager
"""

from pathlib import Path
from src.agents.fixer import FixerAgent
from src.agents.auditor import AuditorAgent
from src.tools.file_manager import list_python_files

print("=" * 70)
print("🚀 TEST AUTOMATIQUE DE TOUS LES FICHIERS")
print("=" * 70)

# Initialize agents
auditor = AuditorAgent()
fixer = FixerAgent()

# Get ALL Python files from sandbox
print("\n📁 Recherche des fichiers dans /sandbox...")
all_files = list_python_files("")  # "" = racine du sandbox

if not all_files:
    print("❌ Aucun fichier Python trouvé dans /sandbox !")
    print("💡 Exécute d'abord : python create_comprehensive_tests.py")
    exit(1)

print(f"✅ {len(all_files)} fichier(s) trouvé(s) :\n")
for i, f in enumerate(all_files, 1):
    print(f"   {i}. {f}")

print("\n" + "=" * 70)
print("🔄 DÉBUT DES TESTS")
print("=" * 70)

# Statistiques
total_files = len(all_files)
successful_fixes = 0
failed_fixes = 0

# Test chaque fichier
for file_num, file_path in enumerate(all_files, 1):
    print(f"\n{'='*70}")
    print(f"📝 [{file_num}/{total_files}] Traitement de : {file_path}")
    print(f"{'='*70}")
    
    try:
        # Step 1: Run Auditor
        print(f"\n🔍 [ÉTAPE 1] Analyse avec Auditor...")
        audit_result = auditor.analyze_file(file_path)
        
        if audit_result['status'] != 'SUCCESS':
            print(f"❌ Erreur lors de l'analyse : {audit_result.get('error', 'Unknown')}")
            failed_fixes += 1
            continue
        
        print(f"✅ Analyse terminée")
        print(f"   Score Pylint : {audit_result['pylint_score']}/10")
        print(f"   Problèmes trouvés : {len(audit_result.get('pylint_issues', []))}")
        
        # Step 2: Build Fixer report from Auditor output
        print(f"\n📋 [ÉTAPE 2] Préparation du rapport pour le Fixer...")
        priority_issues = audit_result.get('analysis_report', {}).get('priority_issues', [])
        
        if not priority_issues:
            print(f"⚠️  Aucun problème prioritaire détecté")
            # Utiliser tous les issues de Pylint si pas de priority_issues
            all_issues = audit_result.get('pylint_issues', [])
            auditor_report = ""
            for i, issue in enumerate(all_issues[:10], 1):  # Max 10 issues
                msg = issue.get('message', 'Unknown issue')
                auditor_report += f"{i}. {msg}\n"
        else:
            auditor_report = ""
            for i, issue in enumerate(priority_issues, 1):
                msg = issue.get('message', 'Unknown issue')
                auditor_report += f"{i}. {msg}\n"
        
        if not auditor_report.strip():
            print(f"✅ Code déjà propre ! Aucune correction nécessaire")
            successful_fixes += 1
            continue
        
        print(f"✅ Rapport généré avec {len(priority_issues) or len(audit_result.get('pylint_issues', [])[:10])} problèmes")
        
        # Step 3: Run Fixer
        print(f"\n🔧 [ÉTAPE 3] Correction avec le Fixer...")
        # Prepend 'sandbox/' here because Fixer needs the real file path
        fixed_code = fixer.run(Path("sandbox") / file_path, auditor_report, overwrite=True)
        
        print(f"✅ Correction terminée !")
        print(f"\n{'─'*70}")
        print(f"CODE CORRIGÉ (extrait) :")
        print(f"{'─'*70}")
        # Afficher les 15 premières lignes du code corrigé
        lines = fixed_code.split('\n')[:15]
        for line in lines:
            print(line)
        if len(fixed_code.split('\n')) > 15:
            print("... (code tronqué)")
        print(f"{'─'*70}")
        
        successful_fixes += 1
        
    except Exception as e:
        print(f"\n❌ ERREUR lors du traitement de {file_path}")
        print(f"   Détails : {e}")
        import traceback
        print(f"   Traceback : {traceback.format_exc()}")
        failed_fixes += 1

# Résumé final
print("\n" + "=" * 70)
print("📊 RÉSUMÉ FINAL")
print("=" * 70)
print(f"\n✅ Fichiers traités avec succès : {successful_fixes}/{total_files}")
if failed_fixes > 0:
    print(f"❌ Fichiers en échec : {failed_fixes}/{total_files}")
print(f"\n{'='*70}")

# Calcul du taux de réussite
success_rate = (successful_fixes / total_files * 100) if total_files > 0 else 0
print(f"📈 Taux de réussite : {success_rate:.1f}%")

if success_rate == 100:
    print(f"🎉 PARFAIT ! Tous les fichiers ont été corrigés !")
elif success_rate >= 80:
    print(f"✅ BIEN ! La plupart des fichiers ont été corrigés")
elif success_rate >= 50:
    print(f"⚠️  MOYEN - Certains fichiers n'ont pas pu être corrigés")
else:
    print(f"❌ ATTENTION - Beaucoup de fichiers n'ont pas pu être corrigés")

print(f"\n💡 Prochaine étape :")
print(f"   Vérifie la qualité des logs avec : python check_data_quality.py")
print(f"   Tu devrais maintenant avoir ~{total_files * 2} entrées (ANALYSIS + FIX)")
print("\n" + "=" * 70)