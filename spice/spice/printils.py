from rites.logger.logger import Logger, get_tertiary_logger # No logs, just nicely formatted logs
from rites.rituals.printer import Printer

def add_custom_styles(logger: Logger) -> None:
    printer: Printer = logger.printer
    # Add all needed custom printing styles here
    printer.add_style("transform", "TFM", 255, 56, 252)
    pass

lexer_log: Logger = get_tertiary_logger(log_name="Lexer").dont_show_exit_message()
parser_log: Logger = get_tertiary_logger(log_name="Parser").dont_show_exit_message()
expression_parser_log: Logger = get_tertiary_logger(log_name="Expression Parser").dont_show_exit_message()
transformer_log: Logger = get_tertiary_logger(log_name="Transformer").dont_show_exit_message()
spice_runner_log: Logger = get_tertiary_logger(log_name="Spice Runner").dont_show_exit_message()
spice_compiler_log: Logger = get_tertiary_logger(log_name="Spice Compiler").dont_show_exit_message()

add_custom_styles(lexer_log)
add_custom_styles(parser_log)
add_custom_styles(expression_parser_log)
add_custom_styles(transformer_log)
add_custom_styles(spice_runner_log)
add_custom_styles(spice_compiler_log)