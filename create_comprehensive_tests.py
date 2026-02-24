"""
CREATE COMPREHENSIVE TEST DATASET
==================================
Crée 10 fichiers Python bugués pour tester le système de refactoring.

Rôle : Quality & Data Manager
Objectif : Valider que le système fonctionne sur différents types de bugs
"""

from src.tools.file_manager import write_file, ensure_sandbox_exists

print("=" * 70)
print("🧪 CRÉATION DU DATASET DE TEST COMPLET")
print("=" * 70)
print("Rôle : Quality & Data Manager")
print("Objectif : Tester le système sur 10 cas différents\n")

ensure_sandbox_exists()

# =============================================================================
# TEST CASE 1 : Erreurs de syntaxe basiques (facile)
# =============================================================================
test_case_1 = '''
def add(a, b)  # Manque :
    return a + b

def multiply(x, y)
    return x * y  # Manque :

def subtract(a, b):
return a - b  # Mauvaise indentation
'''

print("📝 [1/10] test_syntax_basic.py (erreurs de syntaxe basiques)...")
write_file("test_syntax_basic.py", test_case_1)
print("✅ Créé : 3 fonctions avec erreurs de syntaxe\n")

# =============================================================================
# TEST CASE 2 : Erreurs logiques (moyen)
# =============================================================================
test_case_2 = '''
def divide(a, b):
    return a / b  # Pas de vérification b == 0

def get_first_element(lst):
    return lst[0]  # IndexError si liste vide

def calculate_average(numbers):
    total = 0
    for n in numbers:
        total += n
    return total / len(numbers)  # ZeroDivisionError si vide

def safe_sqrt(x):
    import math
    return math.sqrt(x)  # ValueError si x < 0
'''

print("📝 [2/10] test_logic_errors.py (erreurs logiques)...")
write_file("test_logic_errors.py", test_case_2)
print("✅ Créé : 4 fonctions avec erreurs logiques (division par zéro, etc.)\n")

# =============================================================================
# TEST CASE 3 : Problèmes de style PEP8 (facile)
# =============================================================================
test_case_3 = '''
def BadFunctionName(x,y):  # Mauvais nom + pas d'espaces
    z=x+y  # Pas d'espaces autour de =
    return z

class myclass:  # Nom de classe en minuscules
    def MyMethod(self,a,b):  # Pas d'espaces dans les paramètres
        list=[1,2,3]  # Shadow built-in + pas d'espaces
        sum=0  # Shadow built-in
        for i in list:
            sum+=i  # Pas d'espaces
        return sum

def VeryLongFunctionNameThatDoesNotFollowPep8StyleGuideAndIsTooLongToReadEasily(param1,param2,param3):
    return param1+param2+param3
'''

print("📝 [3/10] test_style_pep8.py (problèmes de style PEP8)...")
write_file("test_style_pep8.py", test_case_3)
print("✅ Créé : Code avec mauvais nommage et style PEP8\n")

# =============================================================================
# TEST CASE 4 : Erreurs de classe (moyen)
# =============================================================================
test_case_4 = '''
class Calculator:
    def __init__(self)  # Manque :
    self.history = []  # Mauvaise indentation
    
    def add(self, a, b)  # Manque :
    result = a + b  # Mauvaise indentation
    history.append(result)  # Devrait être self.history
    return result
    
    def get_last_result(self):
        return self.history[-1]  # IndexError si vide
    
    def clear(self):
        history = []  # Devrait être self.history

class BankAccount:
    def __init__(self, balance)  # Manque :
    self.balance = balance
    
    def withdraw(self, amount):
        self.balance -= amount  # Pas de vérification montant > balance
        return self.balance
'''

print("📝 [4/10] test_class_errors.py (erreurs dans les classes)...")
write_file("test_class_errors.py", test_case_4)
print("✅ Créé : 2 classes avec erreurs de syntaxe et logique\n")

# =============================================================================
# TEST CASE 5 : Indentation complexe (difficile)
# =============================================================================
test_case_5 = '''
def nested_function():
    if True:
        if True:
        print("Wrong indent")  # Mauvaise indentation
        return True
    return False

class MyClass:
    def method1(self):
        try:
        result = 10 / 0  # Mauvaise indentation
        except:
        result = None  # Mauvaise indentation
        return result
    
    def method2(self):
    if True:  # Mauvaise indentation
    return "OK"  # Mauvaise indentation
    return "Error"
'''

print("📝 [5/10] test_indentation_complex.py (indentation complexe)...")
write_file("test_indentation_complex.py", test_case_5)
print("✅ Créé : Code avec indentation incorrecte imbriquée\n")

# =============================================================================
# TEST CASE 6 : Variables non définies (moyen)
# =============================================================================
test_case_6 = '''
def use_undefined_var():
    x = 10
    y = 20
    return z  # z n'est pas défini

def missing_import():
    return math.sqrt(16)  # math n'est pas importé

class Student:
    def __init__(self, name):
        self.name = name
    
    def get_grade(self):
        return grade  # grade n'est pas défini
    
    def print_info(self):
        print(f"Name: {name}")  # Devrait être self.name
'''

print("📝 [6/10] test_undefined_vars.py (variables non définies)...")
write_file("test_undefined_vars.py", test_case_6)
print("✅ Créé : Code avec variables/imports manquants\n")

# =============================================================================
# TEST CASE 7 : Opérateurs incorrects (facile)
# =============================================================================
test_case_7 = '''
def check_equality(a, b):
    if a = b:  # Devrait être ==
        return True
    return False

def check_range(x):
    if x > 0 and x < 100:  # OK mais pourrait être 0 < x < 100
        return "valid"
    return "invalid"

def assign_in_condition():
    x = 10
    if y = 5:  # Devrait être ==
        x = y
    return x

def factorial(n):
    if n = 0:  # Devrait être ==
        return 1
    return n * factorial(n - 1)
'''

print("📝 [7/10] test_wrong_operators.py (opérateurs incorrects)...")
write_file("test_wrong_operators.py", test_case_7)
print("✅ Créé : Code avec = au lieu de == dans les conditions\n")

# =============================================================================
# TEST CASE 8 : Docstrings et commentaires manquants (facile)
# =============================================================================
test_case_8 = '''
def complex_function(data, threshold, mode):
    filtered = []
    for item in data:
        if item > threshold:
            filtered.append(item)
    if mode == "sum":
        return sum(filtered)
    elif mode == "avg":
        return sum(filtered) / len(filtered)
    return filtered

class DataProcessor:
    def __init__(self, data):
        self.data = data
        self.processed = False
    
    def process(self):
        self.data = [x * 2 for x in self.data]
        self.processed = True
    
    def get_stats(self):
        return {
            "min": min(self.data),
            "max": max(self.data),
            "avg": sum(self.data) / len(self.data)
        }
'''

print("📝 [8/10] test_missing_docs.py (docstrings manquants)...")
write_file("test_missing_docs.py", test_case_8)
print("✅ Créé : Code fonctionnel mais sans documentation\n")

# =============================================================================
# TEST CASE 9 : Fichier complexe multi-erreurs (difficile)
# =============================================================================
test_case_9 = '''
import math

def factorial(n)  # Manque :
    if n = 0:  # Mauvais opérateur
        return 1
    return n * factorial(n - 1)

class MathOperations:
    def __init__(self)  # Manque :
    self.history = []
    
    def sqrt(self, x)  # Manque :
    if x < 0:
    return None  # Mauvaise indentation
    result = math.sqrt(x)
    history.append(result)  # Devrait être self.history
    return result
    
    def power(self, base, exp):
        if exp = 0:  # Mauvais opérateur
            return 1
        result = 1
        for i in range(exp):
            result = result * base
        return result
    
    def divide_safe(self, a, b):
        return a / b  # Pas de vérification b == 0

def BadFunctionName(x,y):  # Mauvais style
    z=x+y
    return z
'''

print("📝 [9/10] test_complex_multi_errors.py (multi-erreurs complexe)...")
write_file("test_complex_multi_errors.py", test_case_9)
print("✅ Créé : Fichier complexe avec syntaxe, logique et style\n")

# =============================================================================
# TEST CASE 10 : Fichier réaliste (difficile)
# =============================================================================
test_case_10 = '''
class UserManager:
    def __init__(self)  # Manque :
    self.users = {}
    
    def add_user(self, username, email)  # Manque :
    if username in self.users:
    return False  # Mauvaise indentation
    users[username] = email  # Devrait être self.users
    return True
    
    def remove_user(self, username):
        del self.users[username]  # KeyError si n'existe pas
    
    def get_user_email(self, username):
        return self.users[username]  # KeyError si n'existe pas
    
    def count_users(self):
        return len(self.users)

def validate_email(email):
    if '@' in email and '.' in email:
        return True
    return False

def process_user_data(data):
    results = []
    for user in data:
        if validate_email(user['email']):  # KeyError si 'email' absent
            results.append(user)
    return results

def calculate_statistics(numbers):
    total = sum(numbers)
    avg = total / len(numbers)  # ZeroDivisionError si vide
    return {
        "total": total,
        "average": avg,
        "min": min(numbers),  # ValueError si vide
        "max": max(numbers)   # ValueError si vide
    }
'''

print("📝 [10/10] test_realistic_app.py (application réaliste)...")
write_file("test_realistic_app.py", test_case_10)
print("✅ Créé : Classe UserManager avec erreurs variées\n")

# =============================================================================
# RÉSUMÉ FINAL
# =============================================================================
print("=" * 70)
print("✅ DATASET DE TEST COMPLET CRÉÉ AVEC SUCCÈS !")
print("=" * 70)
print("\n📊 Résumé détaillé :")
print("  Total : 10 fichiers de test créés dans /sandbox\n")
print("  Catégories de bugs :")
print("    1. ✅ Erreurs de syntaxe basiques (facile)")
print("    2. ✅ Erreurs logiques (moyen)")
print("    3. ✅ Problèmes de style PEP8 (facile)")
print("    4. ✅ Erreurs dans les classes (moyen)")
print("    5. ✅ Indentation complexe (difficile)")
print("    6. ✅ Variables non définies (moyen)")
print("    7. ✅ Opérateurs incorrects (facile)")
print("    8. ✅ Documentation manquante (facile)")
print("    9. ✅ Multi-erreurs complexe (difficile)")
print("   10. ✅ Application réaliste (difficile)")
print("\n🎯 Prochaines étapes :")
print("  1. Teste ton système sur CHAQUE fichier")
print("  2. Vérifie les logs : python check_data_quality.py")
print("  3. Note les fichiers qui ne se corrigent pas bien")
print("  4. Crée un rapport pour l'équipe")
print("\n💡 Astuce :")
print("  Si certains fichiers ne se corrigent pas, c'est NORMAL !")
print("  Ton rôle = DÉTECTER ces problèmes, pas les corriger.")
print("  Signale-les à l'Orchestrator dans ton rapport.\n")
print("=" * 70)