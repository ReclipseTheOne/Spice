"""Tests for the annotation system.

`@name` is a runtime annotation (emitted as a Python decorator).
`@!name` is a compile-time annotation (processed by the compiler, then stripped).
`@!foo` and `@!foo()` are kept distinct.
"""

from spice.lexer import Lexer
from spice.parser import Parser
from spice.parser.ast_nodes import FunctionDeclaration, Annotation
from spice.transformer import Transformer
from spice.compilation import SpiceFile
from spice.compilation.checks import AnnotationStage
from testutils import presentIn, assert_lacking, safe_assert


def parse_source(source: str):
    tokens = Lexer().tokenize(source)
    return Parser().parse(tokens)


def compile_source(source: str) -> str:
    """Full annotation-aware lowering: parse -> run annotation stage -> transform."""
    file = SpiceFile.empty(source)
    file.tokens = Lexer().tokenize(source)
    file.ast = Parser().parse(file.tokens)

    stage = AnnotationStage()
    assert stage.check(file), f"annotation stage failed: {stage.errors}"
    return Transformer().transform(file.ast, extra_imports=file.extra_imports)


class TestAnnotationParsing:
    """Annotations should attach to the following declaration."""

    def test_compile_time_annotation_with_kwargs(self):
        ast = parse_source(
            '@!print_on_call(time_format="%H:%M:%S")\n'
            'def greet(name: str) -> None {\n'
            '    print(f"Hi {name}");\n'
            '}'
        )
        fn = ast.body[0]
        assert isinstance(fn, FunctionDeclaration)
        assert len(fn.annotations) == 1

        ann = fn.annotations[0]
        assert isinstance(ann, Annotation)
        assert ann.name == "print_on_call"
        assert ann.retention == "compile_time"
        assert ann.is_call is True
        assert "time_format" in ann.kwargs

    def test_runtime_annotation_bare(self):
        ast = parse_source('@trace\ndef greet() -> None {\n    pass;\n}')
        fn = ast.body[0]
        assert len(fn.annotations) == 1
        assert fn.annotations[0].name == "trace"
        assert fn.annotations[0].retention == "runtime"

    def test_identifier_and_call_are_distinct(self):
        """@!foo != @!foo(): the is_call flag must distinguish them."""
        bare = parse_source('@!foo\ndef a() -> None {\n    pass;\n}').body[0].annotations[0]
        called = parse_source('@!foo()\ndef b() -> None {\n    pass;\n}').body[0].annotations[0]

        assert bare.is_call is False
        assert called.is_call is True

    def test_multiple_annotations_stack(self):
        ast = parse_source(
            '@trace\n'
            '@!print_on_call\n'
            'def greet() -> None {\n'
            '    pass;\n'
            '}'
        )
        fn = ast.body[0]
        assert [a.name for a in fn.annotations] == ["trace", "print_on_call"]
        assert [a.retention for a in fn.annotations] == ["runtime", "compile_time"]

    def test_annotation_on_method(self):
        ast = parse_source(
            'class Service {\n'
            '    @!print_on_call(time_format="%H:%M:%S")\n'
            '    def handle() -> None {\n'
            '        pass;\n'
            '    }\n'
            '}'
        )
        method = ast.body[0].body[0]
        assert isinstance(method, FunctionDeclaration)
        assert len(method.annotations) == 1
        assert method.annotations[0].name == "print_on_call"


class TestKeywordArgumentRendering:
    """Keyword args already parse; the transformer must now render them."""

    def test_call_with_kwarg_renders(self):
        out = Transformer().transform(parse_source('configure(name="db", retries=3);'))
        presentIn(out, "configure(")
        presentIn(out, "name=")
        presentIn(out, "retries=")


class TestPrintOnCall:
    """End-to-end intended outcome for the @!print_on_call builtin."""

    def test_injects_timestamped_log_and_strips_annotation(self):
        out = compile_source(
            '@!print_on_call(time_format="%H:%M:%S")\n'
            'def greet(name: str) -> None {\n'
            '    print(f"Hi {name}");\n'
            '}'
        )
        # annotation consumed at compile time -> gone from output
        assert_lacking(out, "print_on_call")
        assert_lacking(out, "@!")
        # ensure_import made the timestamp source available
        presentIn(out, "import datetime")
        # injected log references the function name + the format
        presentIn(out, "strftime")
        presentIn(out, "%H:%M:%S")
        presentIn(out, "greet called")
        # original body preserved, function still a plain def
        presentIn(out, "def greet(name: str) -> None:")
        presentIn(out, "Hi ")
        # injected log runs before the original body
        safe_assert(
            out.index("greet called") < out.index("Hi "),
            "injected log should be the first statement in the body",
        )


class TestRuntimePassthrough:
    """A bare @name should survive to output as a Python decorator."""

    def test_bare_annotation_becomes_decorator(self):
        out = compile_source('@trace\ndef greet() -> None {\n    pass;\n}')
        presentIn(out, "@trace")
        presentIn(out, "def greet() -> None:")
