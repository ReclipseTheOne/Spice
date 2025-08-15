from rites.logger import Logger, get_sec_logger # No logs, just nicely formatted logs
from rites.rituals.printer import Printer

def add_custom_styles(logger: Logger) -> None:
    printer: Printer = logger.printer
    # Add all needed custom printing styles here
    printer.add_style("transform", "TFM", 255, 56, 252)
    pass

lexer_log: Logger = get_sec_logger(log_path="", log_name="Lexer")
parser_log: Logger = get_sec_logger(log_path="", log_name="Parser")
expression_parser_log: Logger = get_sec_logger(log_path="", log_name="Expression Parser")
transformer_log: Logger = get_sec_logger(log_path="", log_name="Transformer")
spice_runner_log: Logger = get_sec_logger(log_path="", log_name="Spice Runner")
spice_compiler_log: Logger = get_sec_logger(log_path="", log_name="Spice Compiler")

add_custom_styles(lexer_log)
add_custom_styles(parser_log)
add_custom_styles(expression_parser_log)
add_custom_styles(transformer_log)
add_custom_styles(spice_runner_log)
add_custom_styles(spice_compiler_log)