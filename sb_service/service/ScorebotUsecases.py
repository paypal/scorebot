import math
import re

from external_tools.github.GithubAPI import GithubAPI
from external_tools.github.GithubConfig import GithubConfig

from common import constants
from core.models import EntropyLog, PatternList, ScorebotConfig


class ScorebotUsecases:
    def __init__(self, framework, pull_request, logger, processor):
        self.framework = framework
        self.pull_request = pull_request
        self._logger = logger
        self.which_processor = processor
        self.ScorebotConfig = ScorebotConfig
        self.github_config = GithubConfig()
        self.github_api = GithubAPI(self.github_config)

    # ======== Helper Functions for ========

    @staticmethod
    def calculate_entropy(password):
        """
        Calculate entropy for the string
        :param password: string to calculate entropy for
        :return: float of entropy value
        """
        funcName = re.findall('\(.*?\)', password)
        if (not password) or funcName:
            return 0
        entropy = 0
        iterator = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.:,;<>?"#$%&/()!@~'
        for x in iterator:
            p_x = float(password.count(x)) / len(password)
            if p_x > 0:
                entropy += -p_x * math.log(p_x, 2)
        return float(entropy)

    @staticmethod
    def string_convert_key_value(stripped_patch, insecure_variable):
        lines = stripped_patch.split('\n')
        processed_list = set([])
        new_list = []
        for line in lines:
            temp = line.split(',')
            for i in temp:
                if insecure_variable.lower() in i.lower():
                    if i.lower().find(insecure_variable.lower()) < i.find("="):
                        new_list.append(i)

        for r in new_list:
            new_temp_list = []
            regex = re.compile(r"\b(\w+)\s?[=](\s?[\w\"\'.].*$)")
            d = dict(regex.findall(r))
            for (key, value) in d.items():
                new_temp_list.append(d[key].split(";")[0])
                new_temp_list.append(r)
            if new_temp_list:
                processed_list.add(tuple(new_temp_list))
        return list(processed_list)

    @staticmethod
    def compare_versions(curr, config):
        """
        Compare versions to determine which version is greater
        1 if curr is greater, 0 if equal, -1 if curr is less
        :param curr: current version of the app
        :param config: config version
        :return: integer from comparison
        """
        if len(curr) == 1:
            if int(curr) < int(config[0]):
                return -1
            if int(curr) > int(config[0]):
                return 1
            return 0
        else:
            curr_list = curr.split(".")
            config_list = config.split(".")[:len(curr_list)]
            i = 0
            while i < len(curr_list):
                if curr_list[i].isdigit():
                    if int(curr_list[i]) < int(config_list[i]):
                        return -1
                    if int(curr_list[i]) > int(config_list[i]):
                        return 1
                elif curr_list[i].lower() in "*x":
                    return 0
                else:
                    return -1
                i += 1
            return 0

    # ========= Use Cases =========

    def scan_patch_pattern(self, patch, security_category):
        """
        Generic pattern search within a patch, patterns can be added in the PatternsList

        :param patch: patch to search for
        :param security_category: category scanning for
        :return: returns list of patterns found, and whether vulnerability was found
        """
        self.repo = self.pull_request.base_repo.name
        self.pull_request_url = self.pull_request.url

        pattern_list = []
        if self.framework == "CPP":
            pattern_list = PatternList.objects.filter(cpp=True, security_category=security_category).\
                           values_list("function_name", "security_category")
        elif self.framework == "Java":
            pattern_list = PatternList.objects.filter(java=True, security_category=security_category).\
                           values_list("function_name", "security_category")
        elif self.framework == "Kraken":
            pattern_list = PatternList.objects.filter(kraken=True, security_category=security_category).\
                           values_list("function_name", "security_category")

        patterns_found = []
        vulnerability_found = False
        patterns_list = [function_name for (function_name, sec_cat) in pattern_list if sec_cat == security_category]

        entropy_cutoff = float(ScorebotConfig.objects.filter(config="entropycutoff").values()[0]["value"])

        for pattern in patterns_list:
            pattern_found_in_patch = False

            if security_category == constants.INSECURE_VARIABLE_SECURITY_CATEGORY:
                counter = 0

                if pattern.lower() in patch.lower():
                    processed_list = self.string_convert_key_value(patch, pattern)

                    if processed_list:
                        for entry in processed_list:
                            EntropyLog.objects.create(variable_name=pattern,
                                                      entropy_value=self.calculate_entropy(entry[0]),
                                                      variable_value=entry[0],
                                                      entropy_line=entry[1],
                                                      pull_request_url=self.pull_request_url,
                                                      framework=self.framework)

                            if (self.calculate_entropy(entry[0])) > entropy_cutoff:
                                counter = counter + 1
                                if counter == 1:
                                    pattern_found_in_patch = True

            elif pattern in patch:  # generic pattern search
                pattern_found_in_patch = True

            if pattern_found_in_patch:
                vulnerability_found = True

                if pattern.endswith('('):
                    pattern = pattern[:-1]
                patterns_found.append(pattern)

        return patterns_found, vulnerability_found

    # Define more use cases here
