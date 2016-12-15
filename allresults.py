from __future__ import unicode_literals
from __future__ import print_function
from pprint import pprint
import sys
import json
import glob
import pydatajson

casefiles = glob.glob("tests/samples/*.json")

dj = pydatajson.DataJson()


def v1():
    for f in casefiles:
        obj = json.load(open(f))
        bool_res = dj.is_valid_catalog(obj)
        full_res = dj._validate_catalog(obj)
        errors = [e.path for e in dj.validator.iter_errors(obj)]

        snippet = """
===== CASE BEGIN =====

ARCHIVO ANALIZADO: {filename}

Resultado booleano: {bool_res}

Resultado completo:
""".format(filename=f, bool_res=bool_res)

        print(snippet)
        pprint(full_res)
        print("\n===== CASE END =====")


def v2():
    import unicodecsv as csv
    with open("list.csv", 'w') as output:
        fieldnames = ["test_file", "__cause__", "cause", "context", "instance",
                      "message", "parent", "path", "relative_path",
                      "relative_schema_path", "schema", "schema_path",
                      "validator", "validator_value"]

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for file in casefiles:
            with open(file) as datajson_file:
                datajson_dict = json.load(datajson_file)

                for error in dj.validator.iter_errors(datajson_dict):
                    error_dict = error.__dict__
                    error_dict["test_file"] = file.split("/")[-1]
                    writer.writerow(error_dict)


def main():
    version = int(sys.argv[1])
    if version == 1:
        v1()
    elif version == 2:
        v2()
    else:
        print("Version no reconocida")


if __name__ == '__main__':
    main()
