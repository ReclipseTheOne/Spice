from spice.parser.ast_nodes import FinalDeclaration, AssignmentExpression, IdentifierExpression, FunctionDeclaration, ClassDeclaration

class FinalChecker:
    """Compile-time checker for final variable reassignments."""
    
    def __init__(self):
        self.final_variables = {}  # Maps scope -> set of final variable names
        self.current_scope = 'global'
        self.errors = []
    
    def enter_scope(self, scope_name: str):
        """Enter a new scope (function/class)."""
        self.current_scope = scope_name
        if scope_name not in self.final_variables:
            self.final_variables[scope_name] = set()
    
    def exit_scope(self):
        """Exit current scope."""
        self.current_scope = 'global'
    
    def register_final(self, var_name: str):
        """Register a variable as final in current scope."""
        if self.current_scope not in self.final_variables:
            self.final_variables[self.current_scope] = set()
        self.final_variables[self.current_scope].add(var_name)
    
    def check_assignment(self, var_name: str, line_number: int):
        """Check if assignment to variable is allowed."""
        scope_vars = self.final_variables.get(self.current_scope, set())
        global_vars = self.final_variables.get('global', set())
        
        if var_name in scope_vars or var_name in global_vars:
            self.errors.append(
                f"Line {line_number}: Cannot reassign final variable '{var_name}'"
            )
            return False
        return True
    
    def walk_ast(self, ast):
        """Walk the AST and check for final violations."""
        for node in ast.body:
            self._visit_node(node)
    
    def _visit_node(self, node):
        """Visit a node and check for violations."""
        if isinstance(node, FinalDeclaration):
            if isinstance(node.target, IdentifierExpression):
                self.register_final(node.target.name)
        
        elif isinstance(node, AssignmentExpression):
            # Check if this is a reassignment to a final variable
            if isinstance(node.target, IdentifierExpression):
                self.check_assignment(node.target.name, node.line_number)
        
        elif isinstance(node, FunctionDeclaration):
            # Enter function scope
            old_scope = self.current_scope
            self.enter_scope(node.name)
            for stmt in node.body:
                self._visit_node(stmt)
            self.current_scope = old_scope
        
        elif isinstance(node, ClassDeclaration):
            # Enter class scope
            old_scope = self.current_scope
            self.enter_scope(node.name)
            for method in node.methods:
                self._visit_node(method)
            self.current_scope = old_scope
        
        # Recursively visit child nodes
        if hasattr(node, 'body') and isinstance(node.body, list):
            for child in node.body:
                self._visit_node(child)
