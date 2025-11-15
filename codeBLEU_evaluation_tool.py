"""
CodeBLEU Evaluation Tool for AI Code Generator
This tool evaluates the correctness of generated code using CodeBLEU metric
"""

import ast
import re
from collections import Counter
from typing import List, Dict, Tuple
import math

class CodeBLEUEvaluator:
    def __init__(self):
        self.weights = {
            'bleu': 0.25,
            'syntax': 0.25,
            'dataflow': 0.25,
            'ngram_match': 0.25
        }
    
    def evaluate(self, reference_code: str, generated_code: str, language: str = 'python') -> Dict:
        """
        Evaluate generated code against reference code
        
        Args:
            reference_code: The correct/reference code
            generated_code: The AI-generated code
            language: Programming language (default: python)
        
        Returns:
            Dictionary with evaluation scores
        """
        
        # Clean codes
        ref_clean = self.clean_code(reference_code)
        gen_clean = self.clean_code(generated_code)
        
        # Calculate different metrics
        bleu_score = self.calculate_bleu(ref_clean, gen_clean)
        syntax_score = self.calculate_syntax_match(reference_code, generated_code, language)
        dataflow_score = self.calculate_dataflow_match(reference_code, generated_code, language)
        ngram_score = self.calculate_ngram_match(ref_clean, gen_clean)
        
        # Calculate weighted CodeBLEU score
        codebleu_score = (
            self.weights['bleu'] * bleu_score +
            self.weights['syntax'] * syntax_score +
            self.weights['dataflow'] * dataflow_score +
            self.weights['ngram_match'] * ngram_score
        )
        
        return {
            'codebleu_score': round(codebleu_score, 4),
            'bleu_score': round(bleu_score, 4),
            'syntax_match': round(syntax_score, 4),
            'dataflow_match': round(dataflow_score, 4),
            'ngram_match': round(ngram_score, 4),
            'evaluation': self.get_evaluation_level(codebleu_score)
        }
    
    def clean_code(self, code: str) -> str:
        """Remove comments and extra whitespace"""
        # Remove single-line comments
        code = re.sub(r'//.*?\n|#.*?\n', '\n', code)
        # Remove multi-line comments
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        # Remove extra whitespace
        code = re.sub(r'\s+', ' ', code)
        return code.strip()
    
    def tokenize(self, code: str) -> List[str]:
        """Tokenize code into words and symbols"""
        # Split by whitespace and preserve operators
        tokens = re.findall(r'\w+|[^\w\s]', code)
        return [t for t in tokens if t.strip()]
    
    def calculate_bleu(self, reference: str, generated: str, max_n: int = 4) -> float:
        """Calculate BLEU score"""
        ref_tokens = self.tokenize(reference)
        gen_tokens = self.tokenize(generated)
        
        if not gen_tokens:
            return 0.0
        
        # Calculate n-gram precisions
        precisions = []
        for n in range(1, max_n + 1):
            ref_ngrams = self.get_ngrams(ref_tokens, n)
            gen_ngrams = self.get_ngrams(gen_tokens, n)
            
            if not gen_ngrams:
                precisions.append(0)
                continue
            
            matches = sum((ref_ngrams & gen_ngrams).values())
            total = sum(gen_ngrams.values())
            
            precisions.append(matches / total if total > 0 else 0)
        
        # Calculate geometric mean
        if all(p > 0 for p in precisions):
            geo_mean = math.exp(sum(math.log(p) for p in precisions) / len(precisions))
        else:
            geo_mean = 0
        
        # Brevity penalty
        ref_len = len(ref_tokens)
        gen_len = len(gen_tokens)
        
        if gen_len > ref_len:
            bp = 1
        else:
            bp = math.exp(1 - ref_len / gen_len) if gen_len > 0 else 0
        
        return bp * geo_mean
    
    def get_ngrams(self, tokens: List[str], n: int) -> Counter:
        """Get n-grams from token list"""
        ngrams = []
        for i in range(len(tokens) - n + 1):
            ngrams.append(tuple(tokens[i:i+n]))
        return Counter(ngrams)
    
    def calculate_syntax_match(self, reference: str, generated: str, language: str) -> float:
        """Calculate syntax tree similarity (for Python)"""
        if language != 'python':
            # For non-Python languages, use a simple keyword matching approach
            return self.calculate_keyword_match(reference, generated)
        
        try:
            ref_tree = ast.parse(reference)
            gen_tree = ast.parse(generated)
            
            ref_nodes = self.get_ast_nodes(ref_tree)
            gen_nodes = self.get_ast_nodes(gen_tree)
            
            if not ref_nodes:
                return 0.0
            
            # Calculate Jaccard similarity
            intersection = len(ref_nodes & gen_nodes)
            union = len(ref_nodes | gen_nodes)
            
            return intersection / union if union > 0 else 0.0
        
        except SyntaxError:
            # If syntax error, return low score
            return 0.1
    
    def get_ast_nodes(self, tree) -> set:
        """Extract node types from AST"""
        nodes = set()
        for node in ast.walk(tree):
            nodes.add(type(node).__name__)
        return nodes
    
    def calculate_keyword_match(self, reference: str, generated: str) -> float:
        """Calculate keyword matching for non-Python languages"""
        keywords = {
            'java': ['class', 'public', 'private', 'static', 'void', 'int', 'String', 'return', 'if', 'else', 'for', 'while'],
            'cpp': ['include', 'int', 'void', 'return', 'if', 'else', 'for', 'while', 'class', 'namespace', 'std'],
            'javascript': ['function', 'const', 'let', 'var', 'return', 'if', 'else', 'for', 'while', 'class']
        }
        
        ref_lower = reference.lower()
        gen_lower = generated.lower()
        
        # Count keyword matches
        matches = 0
        total = 0
        
        for keyword_list in keywords.values():
            for keyword in keyword_list:
                if keyword in ref_lower:
                    total += 1
                    if keyword in gen_lower:
                        matches += 1
        
        return matches / total if total > 0 else 0.5
    
    def calculate_dataflow_match(self, reference: str, generated: str, language: str) -> float:
        """Calculate data flow similarity (variable usage patterns)"""
        ref_vars = self.extract_variables(reference)
        gen_vars = self.extract_variables(generated)
        
        if not ref_vars:
            return 1.0 if not gen_vars else 0.5
        
        # Calculate Jaccard similarity
        intersection = len(ref_vars & gen_vars)
        union = len(ref_vars | gen_vars)
        
        return intersection / union if union > 0 else 0.0
    
    def extract_variables(self, code: str) -> set:
        """Extract variable names from code"""
        # Simple variable extraction using regex
        # Matches identifiers (variable names)
        variables = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', code)
        
        # Filter out common keywords
        keywords = {'if', 'else', 'for', 'while', 'return', 'class', 'def', 'import', 
                   'from', 'print', 'int', 'float', 'str', 'void', 'public', 'private',
                   'static', 'const', 'let', 'var', 'function'}
        
        variables = [v for v in variables if v not in keywords]
        return set(variables)
    
    def calculate_ngram_match(self, reference: str, generated: str) -> float:
        """Calculate character-level n-gram matching"""
        ref_tokens = self.tokenize(reference)
        gen_tokens = self.tokenize(generated)
        
        # Calculate 2-gram and 3-gram matches
        score_2gram = self.ngram_precision(ref_tokens, gen_tokens, 2)
        score_3gram = self.ngram_precision(ref_tokens, gen_tokens, 3)
        
        return (score_2gram + score_3gram) / 2
    
    def ngram_precision(self, ref_tokens: List[str], gen_tokens: List[str], n: int) -> float:
        """Calculate n-gram precision"""
        ref_ngrams = self.get_ngrams(ref_tokens, n)
        gen_ngrams = self.get_ngrams(gen_tokens, n)
        
        if not gen_ngrams:
            return 0.0
        
        matches = sum((ref_ngrams & gen_ngrams).values())
        total = sum(gen_ngrams.values())
        
        return matches / total if total > 0 else 0.0
    
    def get_evaluation_level(self, score: float) -> str:
        """Get evaluation level based on score"""
        if score >= 0.9:
            return "Excellent - Code is highly accurate"
        elif score >= 0.75:
            return "Good - Code is mostly correct with minor differences"
        elif score >= 0.6:
            return "Fair - Code has some correctness but needs improvement"
        elif score >= 0.4:
            return "Poor - Code has significant differences"
        else:
            return "Very Poor - Code is largely incorrect"


# Example usage and testing
def main():
    evaluator = CodeBLEUEvaluator()
    
    print("=" * 70)
    print("CodeBLEU Evaluation Tool - Testing")
    print("=" * 70)
    
    # Test Case 1: Python Calculator
    print("\n📝 Test Case 1: Python Calculator")
    print("-" * 70)
    
    reference_code = """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b != 0:
        return a / b
    return None
"""
    
    generated_code = """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(x, y):
    return x * y

def divide(x, y):
    if y != 0:
        return x / y
    return None
"""
    
    result = evaluator.evaluate(reference_code, generated_code, 'python')
    print_results(result)
    
    # Test Case 2: Java Hello World
    print("\n📝 Test Case 2: Java Hello World")
    print("-" * 70)
    
    reference_java = """
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
"""
    
    generated_java = """
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
"""
    
    result = evaluator.evaluate(reference_java, generated_java, 'java')
    print_results(result)
    
    # Test Case 3: Different implementation
    print("\n📝 Test Case 3: Different Implementation (Same Logic)")
    print("-" * 70)
    
    reference_loop = """
sum = 0
for i in range(10):
    sum += i
print(sum)
"""
    
    generated_loop = """
total = 0
for num in range(10):
    total = total + num
print(total)
"""
    
    result = evaluator.evaluate(reference_loop, generated_loop, 'python')
    print_results(result)


def print_results(result: Dict):
    """Print evaluation results in a formatted way"""
    print(f"\n🎯 CodeBLEU Score: {result['codebleu_score']} / 1.0")
    print(f"   ├─ BLEU Score: {result['bleu_score']}")
    print(f"   ├─ Syntax Match: {result['syntax_match']}")
    print(f"   ├─ Dataflow Match: {result['dataflow_match']}")
    print(f"   └─ N-gram Match: {result['ngram_match']}")
    print(f"\n📊 Evaluation: {result['evaluation']}")


if __name__ == "__main__":
    main()