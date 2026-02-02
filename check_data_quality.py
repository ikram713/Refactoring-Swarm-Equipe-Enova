"""
DATA QUALITY CHECKER - Vérification selon le TP IGL
====================================================
Ce script vérifie la qualité des logs selon les critères du TP.

Critères du Bot de Correction (30% de la note) :
✅ Le fichier experiment_data.json est valide
✅ Il contient l'historique complet
✅ Tous les logs ont input_prompt et output_response

Author: Quality & Data Manager
Date: 2026
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Couleurs pour le terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print("\n" + "=" * 70)
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print("=" * 70)

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text):
    print(f"   {text}")


class DataQualityChecker:
    """Vérifie la qualité des données selon les exigences du TP"""
    
    def __init__(self, log_file="logs/experiment_data.json"):
        self.log_file = log_file
        self.logs = []
        self.total_errors = 0
        self.total_warnings = 0
        
        # ActionTypes valides selon le TP
        self.valid_actions = {
            "CODE_ANALYSIS",  # ActionType.ANALYSIS
            "CODE_GEN",       # ActionType.GENERATION
            "DEBUG",          # ActionType.DEBUG
            "FIX"             # ActionType.FIX
        }
    
    def run_all_checks(self):
        """Lance tous les tests de qualité"""
        print_header("🔍 VÉRIFICATION DE LA QUALITÉ DES DONNÉES")
        print(f"Fichier analysé : {self.log_file}")
        print(f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Test 1 : Fichier existe
        if not self.check_file_exists():
            print_error("ÉCHEC CRITIQUE : Le fichier de logs n'existe pas !")
            print_info("➡️  Exécutez d'abord votre système pour générer des logs")
            return False
        
        # Test 2 : JSON valide
        if not self.load_and_validate_json():
            print_error("ÉCHEC CRITIQUE : Le fichier JSON est invalide !")
            return False
        
        # Test 3 : Logs non vides
        if len(self.logs) == 0:
            print_error("ÉCHEC CRITIQUE : Aucun log trouvé !")
            print_info("➡️  Le fichier est vide, exécutez votre système")
            return False
        
        # Test 4 : Champs obligatoires
        self.check_required_fields()
        
        # Test 5 : ActionTypes
        self.check_action_types()
        
        # Test 6 : Distribution des agents
        self.check_agent_distribution()
        
        # Test 7 : Qualité des prompts
        self.check_prompt_quality()
        
        # Rapport final
        self.print_final_report()
        
        return self.total_errors == 0
    
    def check_file_exists(self):
        """Vérifie que le fichier existe"""
        print_header("TEST 1 : Existence du fichier")
        
        if not os.path.exists(self.log_file):
            return False
        
        size = os.path.getsize(self.log_file)
        print_success(f"Fichier trouvé : {self.log_file}")
        print_info(f"Taille : {size:,} bytes")
        
        if size == 0:
            print_error("Le fichier est vide !")
            return False
        
        return True
    
    def load_and_validate_json(self):
        """Charge et valide le JSON"""
        print_header("TEST 2 : Validation du format JSON")
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                self.logs = json.loads(content)
            
            if not isinstance(self.logs, list):
                print_error("Le JSON doit être une liste (array) !")
                return False
            
            print_success(f"JSON valide : {len(self.logs)} entrées trouvées")
            return True
            
        except json.JSONDecodeError as e:
            print_error(f"Erreur de parsing JSON : {e}")
            print_info(f"Ligne {e.lineno}, colonne {e.colno}")
            return False
        except Exception as e:
            print_error(f"Erreur : {e}")
            return False
    
    def check_required_fields(self):
        """Vérifie les champs obligatoires (CRITIQUE pour le TP)"""
        print_header("TEST 3 : Champs obligatoires (input_prompt & output_response)")
        
        valid_logs = 0
        invalid_logs = []
        
        for i, log in enumerate(self.logs, 1):
            # Vérifier la structure de base
            if 'details' not in log:
                invalid_logs.append(f"Log #{i}: Pas de champ 'details'")
                continue
            
            details = log['details']
            
            # Vérifier input_prompt
            has_input = 'input_prompt' in details and details['input_prompt']
            
            # Vérifier output_response
            has_output = 'output_response' in details and details['output_response']
            
            if not has_input or not has_output:
                missing = []
                if not has_input:
                    missing.append('input_prompt')
                if not has_output:
                    missing.append('output_response')
                
                agent = log.get('agent', 'Unknown')
                action = log.get('action', 'Unknown')
                invalid_logs.append(
                    f"Log #{i} [{agent} - {action}]: Manque {', '.join(missing)}"
                )
            else:
                valid_logs += 1
        
        # Résultats
        if len(invalid_logs) == 0:
            print_success(f"PARFAIT ! Tous les {valid_logs} logs sont valides")
            print_info("✓ Tous les logs contiennent input_prompt")
            print_info("✓ Tous les logs contiennent output_response")
        else:
            self.total_errors += len(invalid_logs)
            print_error(f"{len(invalid_logs)} logs INVALIDES sur {len(self.logs)}")
            print_warning("ATTENTION : Ceci affectera votre note 'Data Quality' (30%) !")
            print("\n⚠️  Logs problématiques :")
            for error in invalid_logs[:10]:  # Afficher max 10
                print_info(f"   • {error}")
            if len(invalid_logs) > 10:
                print_info(f"   ... et {len(invalid_logs) - 10} autres")
    
    def check_action_types(self):
        """Vérifie que les ActionTypes sont corrects"""
        print_header("TEST 4 : Validation des ActionType")
        
        action_counts = {}
        invalid_actions = []
        
        for i, log in enumerate(self.logs, 1):
            action = log.get('action', 'UNKNOWN')
            action_counts[action] = action_counts.get(action, 0) + 1
            
            if action not in self.valid_actions:
                agent = log.get('agent', 'Unknown')
                invalid_actions.append(f"Log #{i} [{agent}]: '{action}' invalide")
        
        # Affichage
        print_info("Distribution des actions :")
        for action, count in sorted(action_counts.items()):
            is_valid = action in self.valid_actions
            status = "✅" if is_valid else "❌"
            print_info(f"   {status} {action}: {count} fois")
        
        if invalid_actions:
            self.total_warnings += len(invalid_actions)
            print_warning(f"{len(invalid_actions)} ActionType invalides détectés")
            print_info("Actions valides selon le TP :")
            for valid_action in self.valid_actions:
                print_info(f"   • ActionType.{valid_action}")
        else:
            print_success("Tous les ActionType sont valides !")
    
    def check_agent_distribution(self):
        """Vérifie la distribution des agents"""
        print_header("TEST 5 : Distribution des agents")
        
        agent_counts = {}
        
        for log in self.logs:
            agent = log.get('agent', 'Unknown')
            agent_counts[agent] = agent_counts.get(agent, 0) + 1
        
        print_info("Agents actifs :")
        for agent, count in sorted(agent_counts.items()):
            print_info(f"   • {agent}: {count} actions")
        
        # Vérifier qu'on a au moins Auditor et Fixer
        expected_agents = ['Auditor_Agent', 'FixerAgent']
        missing = [a for a in expected_agents if a not in agent_counts]
        
        if missing:
            self.total_warnings += 1
            print_warning(f"Agents manquants : {', '.join(missing)}")
        else:
            print_success("Auditor et Fixer sont présents ✓")
    
    def check_prompt_quality(self):
        """Analyse la qualité des prompts"""
        print_header("TEST 6 : Qualité des prompts")
        
        total_prompts = 0
        empty_prompts = 0
        short_prompts = 0
        total_prompt_length = 0
        total_response_length = 0
        
        for log in self.logs:
            details = log.get('details', {})
            
            prompt = details.get('input_prompt', '')
            response = details.get('output_response', '')
            
            total_prompts += 1
            
            if not prompt or prompt.strip() == '':
                empty_prompts += 1
            elif len(prompt) < 50:
                short_prompts += 1
            
            total_prompt_length += len(prompt)
            total_response_length += len(response)
        
        # Calculs
        avg_prompt = total_prompt_length / total_prompts if total_prompts > 0 else 0
        avg_response = total_response_length / total_prompts if total_prompts > 0 else 0
        
        print_info(f"Total de prompts analysés : {total_prompts}")
        print_info(f"Longueur moyenne des prompts : {avg_prompt:.0f} caractères")
        print_info(f"Longueur moyenne des réponses : {avg_response:.0f} caractères")
        
        if empty_prompts > 0:
            self.total_errors += empty_prompts
            print_error(f"{empty_prompts} prompts vides détectés !")
        
        if short_prompts > 0:
            self.total_warnings += short_prompts
            print_warning(f"{short_prompts} prompts très courts (<50 chars)")
        
        if empty_prompts == 0 and short_prompts == 0:
            print_success("Qualité des prompts : EXCELLENTE !")
    
    def print_final_report(self):
        """Affiche le rapport final"""
        print_header("📊 RAPPORT FINAL - DATA QUALITY")
        
        total_logs = len(self.logs)
        
        print(f"\n📈 Statistiques globales :")
        print_info(f"Total de logs : {total_logs}")
        print_info(f"Erreurs critiques : {self.total_errors}")
        print_info(f"Avertissements : {self.total_warnings}")
        
        # Note estimée (sur la partie Data Quality = 30%)
        if self.total_errors == 0:
            score = 100
            status = "✅ EXCELLENT"
            color = Colors.GREEN
        elif self.total_errors <= 2:
            score = 80
            status = "⚠️  BON (avec réserves)"
            color = Colors.YELLOW
        else:
            score = max(0, 100 - (self.total_errors * 10))
            status = "❌ INSUFFISANT"
            color = Colors.RED
        
        print(f"\n{color}{Colors.BOLD}Score estimé Data Quality : {score}/100{Colors.END}")
        print(f"{color}Status : {status}{Colors.END}")
        
        print("\n" + "=" * 70)
        
        if self.total_errors == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}")
            print("✅ VALIDATION RÉUSSIE !")
            print("Votre fichier experiment_data.json est conforme aux exigences du TP.")
            print(f"{Colors.END}")
        else:
            print(f"{Colors.RED}{Colors.BOLD}")
            print("❌ VALIDATION ÉCHOUÉE !")
            print(f"Corrigez les {self.total_errors} erreurs avant de soumettre le TP.")
            print(f"{Colors.END}")
            print("\n💡 Actions recommandées :")
            print_info("1. Vérifiez que tous vos agents utilisent log_experiment()")
            print_info("2. Assurez-vous que input_prompt et output_response sont bien remplis")
            print_info("3. Utilisez les ActionType corrects (ANALYSIS, FIX, etc.)")
        
        print("=" * 70 + "\n")
        
        # Instructions finales
        if self.total_errors == 0:
            print(f"{Colors.BLUE}📝 Prochaines étapes :{Colors.END}")
            print_info("1. Commitez vos logs : git add -f logs/experiment_data.json")
            print_info("2. git commit -m 'DATA: Submission of experiment logs'")
            print_info("3. git push origin main")
            print()


def main():
    """Point d'entrée du script"""
    checker = DataQualityChecker()
    success = checker.run_all_checks()
    
    # Code de sortie
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()