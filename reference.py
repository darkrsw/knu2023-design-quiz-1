from ast import NodeVisitor
import ast
import os
import json

from glob import glob

def getAST(path: str):
    with open(path, "r") as f:
        source = f.read()
    return ast.parse(source)


class ClassVisitor(NodeVisitor):
    def __init__(self):
        super().__init__()
        self.gen_dict = {}

    def visit_ClassDef(self, node):
        parents = []
        for base in node.bases:
            if isinstance(base, ast.Attribute):
                parents.append(base.attr)
            elif isinstance(base, ast.Subscript):
                parents.append(base.value.id)
            elif isinstance(base, ast.Name):
                parents.append(base.id)
            else:
                raise Exception(f"Unknown base type: {type(base)}")
        self.gen_dict[node.name] = { "parents": set(parents) }
        return super().generic_visit(node)


def collect_class_forest(path):
    pyfiles = list(glob(path+"/**/*.py", recursive=True))

    myvisitor = ClassVisitor()

    for pyfile in pyfiles:
        myast = getAST(pyfile)
        myvisitor.visit(myast)

    reversed = {}
    classdict = myvisitor.gen_dict
    # print(classdict)

    for key, value in classdict.items():
        if len(value["parents"]) > 0:
            for parent in value["parents"]:
                if parent in reversed:
                    reversed[parent].append(key)
                elif parent in classdict.keys():
                    reversed[parent] = [key]

    # print(reversed)

    def update_children(key, forestdict):
        retdict = {}
        if key in forestdict.keys() and len(forestdict[key]) > 0:
            for child in forestdict[key]:
                retdict[child] = update_children(child, forestdict)
        return retdict

    forest = {}

    for key, children in reversed.items():
        # print(classdict[key]["parents"])
        if len(children) > 0 and len(classdict[key]["parents"].intersection(classdict.keys())) == 0:
            forest[key] = {}
            for child in children:
                forest[key][child] = update_children(child, reversed)

    return forest
