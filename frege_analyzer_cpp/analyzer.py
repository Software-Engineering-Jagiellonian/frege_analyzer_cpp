import lizard
from lizard_ext import auto_read

from frege_analyzer_cpp.logger import logger


class LizardException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class CustomFileAnalyzer(lizard.FileAnalyzer):
    def __call__(self, filename):
        try:
            return self.analyze_source_code(filename, auto_read(filename))
        except UnicodeDecodeError:
            raise LizardException(f'Error: doesnt support none utf encoding {filename}')
        except IOError:
            raise LizardException(f'Error: Fail to read source file {filename}')
        except IndexError:
            raise LizardException(f'Error: Fail to parse file {filename}')


class AnalyzeResult:

    def __init__(self, result):
        self.filename = result['filename']
        self.nloc = result['nloc']
        self.function_list = result['function_list'] or []
        self.token_count = result['token_count']

    average_lines_of_code = property(lambda self: self.functions_average("nloc"))
    average_token_count = property(lambda self: self.functions_average("token_count"))
    average_cyclomatic_complexity = property(lambda self: self.functions_average("cyclomatic_complexity"))
    average_parameter_count = property(lambda self: self.functions_average("parameter_count"))
    average_nesting_depth = property(lambda self: self.functions_average("max_nesting_depth"))
    max_nesting_depth = property(lambda self: max(fun.max_nesting_depth for fun in self.function_list))

    def functions_average(self, att):
        summary = sum(getattr(fun, att) for fun in self.function_list)
        return summary / len(self.function_list) if self.function_list else 0

    def as_dict(self):
        result = dict()
        result['lines_of_code'] = int(self.nloc)
        result['token_count'] = int(self.token_count)
        result['average_lines_of_code'] = int(self.average_lines_of_code)
        result['average_token_count'] = int(self.average_token_count)
        result['average_cyclomatic_complexity'] = int(self.average_cyclomatic_complexity)
        result['average_parameter_count'] = int(self.average_parameter_count)
        result['average_nesting_depth'] = int(self.average_nesting_depth)
        result['max_nesting_depth'] = int(self.max_nesting_depth)
        return result

    def __str__(self):
        return f'AnalyzeResult of {self.filename} =\n' \
               f'[lines_of_code = {self.nloc}, ' \
               f'token_count = {self.token_count}, ' \
               f'average_lines_of_code = {self.average_lines_of_code}, ' \
               f'average_token_count = {self.average_token_count}, ' \
               f'average_cyclomatic_complexity = {self.average_cyclomatic_complexity}, ' \
               f'average_parameter_count = {self.average_parameter_count}, ' \
               f'average_nesting_depth = {self.average_nesting_depth}, ' \
               f'max_nesting_depth = {self.max_nesting_depth}]'


class CppAnalyzer:

    @staticmethod
    def analyze(file_paths):
        results = dict()
        for file_path in file_paths:
            logger.info(f'Analyzing {file_path}')
            try:
                analyze_file = CustomFileAnalyzer(lizard.get_extensions(['nd']))
                result = AnalyzeResult(analyze_file(file_path[1]).__dict__)
                logger.info(f'Analyzed {file_path} with results = {result}')
                results[file_path[0]] = result
            except LizardException as exception:
                logger.error(f'Skipping {file_path} due to lizard analyzer error: {exception.message}')
        return results
