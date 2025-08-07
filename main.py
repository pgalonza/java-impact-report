"""
Generate impact report
"""

import sys
import os
import logging
from collections import defaultdict
from openpyxl import Workbook
import gitlab


class ModuleInfo():

    def __init__(self, module_name: str, changed_files: dict) -> None:
        self.module_name: str = module_name
        self.changed_files: dict = changed_files
        self.package_info = {}
        self.module_info = ""

    @classmethod
    def _report_search(cls, searh_path: str, parrent_dir: str) -> None:
        try:
            if 'package-info.java' in list(filter(lambda x: os.path.isfile(os.path.join(searh_path, x)), os.listdir(searh_path))):
                result = os.path.join(searh_path, 'package-info.java')
            elif searh_path == parrent_dir:
                result = None
            else:
                result = cls._report_search(os.path.dirname(searh_path), parrent_dir)
        except FileNotFoundError:
            logging.warning('No path %s', searh_path)
            result = None

        return result

    @staticmethod
    def _extract_information(package_info_file) -> str:
        with open(package_info_file, 'r', encoding='utf-8') as f_object:
            raw_text = f_object.read()

        try:
            logging.info('Getting text between IA: %s', package_info_file)
            raw_info = raw_text[raw_text.index(' * <AI>\n') + 1:raw_text.index(' * </AI>')]
            logging.info('Cleanning text: %s', package_info_file)
            result = ' '.join(map(lambda x: x.replace(' * ', ''), raw_info))
        except ValueError as e_message:
            logging.error(e_message)
            result = None

        return result

    def get_package_info(self, search_path: str, parrent_dir: str) -> None:
        absolute_search_path = os.path.join(parrent_dir, search_path)
        resutl = self._report_search(absolute_search_path, parrent_dir)
        if resutl:
            self.package_info[search_path] = self._extract_information(resutl)
        else:
            self.package_info[search_path] = None

    def get_module_info(self, package_file) -> None:
        if os.path.isfile(package_file):
            self.module_info = self._extract_information(package_file)
            logging.info('Getting module info: %s', package_file)
        else:
            logging.warning('No file %s', package_file)
            self.module_info = None


def main():
    logging.info('Starting script')

    try:
        branch_name = os.environ['CI_COMMIT_REF_NAME']
        gitlab_token = os.environ['GITLAB_TOKEN']
        gitlab_project_id = os.environ['CI_PROJECT_ID']
        gitlab_url = os.environ['CI_SERVER_URL']
        build_directory = os.environ['CI_PROJECT_DIR']
        commit_sha = os.environ['CI_COMMIT_SHORT_SHA']
    except KeyError as e_message:
        logging.error(e_message)
        sys.exit(1)

    dst_branch = os.environ.get('DST_BRANCH', 'master')

    gitlab_interface = gitlab.Gitlab(gitlab_url, private_token=gitlab_token)
    project_interface = gitlab_interface.projects.get(gitlab_project_id)

    logging.info('Getting compare result')
    compare_result = project_interface.compare(branch_name, dst_branch)

    changed_files = filter(
        lambda x: 'src/main/java' in x['new_path'] and 'package-info.java' not in x['new_path'],
        compare_result.diffs
    )
    modules_f = defaultdict(lambda: defaultdict(list))

    logging.info('Grouping modules with changed files')
    for changed_file in changed_files:
        path_items = changed_file['new_path'].split('/')
        module_name = path_items[path_items.index('src') - 1]
        package_path = os.path.dirname(changed_file['new_path'])
        modules_f[module_name][package_path].append(os.path.basename(changed_file['new_path']))

    module_l = []

    logging.info('Searching information about packages')
    for module_name, search_path in modules_f.items():
        module_o = ModuleInfo(module_name, search_path)
        path_items = list(search_path)[0].split('/')
        path_items = path_items[0:path_items.index(module_name) + 4]
        path_items.append('package-info.java')
        package_info_file = '/'.join(path_items)
        absolute_module_path_i = os.path.join(build_directory, package_info_file)

        module_o.get_module_info(absolute_module_path_i)
        for search_dir in search_path.keys():
            module_o.get_package_info(search_dir, build_directory)
        module_l.append(module_o)

    work_book = Workbook()
    work_sheet = work_book.active
    work_sheet.title = 'Impact Report'

    logging.info('Creating report')
    for module_o in module_l:
        work_sheet.append([module_o.module_name, module_o.package_info, module_o.module_info])

    work_book.save('impact_report.xlsx')


if __name__ == '__main__':
    main()
