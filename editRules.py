import yaml
import os

# 定义YAML文件路径
yaml_file_path = 'rules.yml'


def initialize_yaml_file():
    """初始化YAML文件，如果文件不存在则创建一个空的YAML文件。"""
    if not os.path.exists(yaml_file_path):
        with open(yaml_file_path, 'w') as file:
            yaml.dump({'rules': []}, file)


def add_rule(group_name, rule_name, f_regex):
    """添加新规则到指定的组中。"""
    initialize_yaml_file()

    with open(yaml_file_path, 'r') as file:
        data = yaml.safe_load(file)

    # 查找指定的group
    group_found = False
    for group in data['rules']:
        if group['group'] == group_name:
            group_found = True
            # 检查规则是否已存在
            if any(rule['name'] == rule_name for rule in group['rule']):
                print(f"Rule '{rule_name}' already exists in group '{group_name}'.")
                return
            # 添加新规则
            new_rule = {'name': rule_name, 'f_regex': f_regex, 'sensitive': False}
            group['rule'].append(new_rule)
            break

    if not group_found:
        new_group = {
            'group': group_name,
            'rule': [{'name': rule_name, 'f_regex': f_regex, 'sensitive': False}]
        }
        data['rules'].append(new_group)

    with open(yaml_file_path, 'w') as file:
        yaml.dump(data, file)
    print(f"Added rule '{rule_name}' to group '{group_name}'.")


def edit_rule(group_name, rule_name, new_rule_name=None, new_f_regex=None):
    """编辑指定组中的规则。"""
    initialize_yaml_file()

    with open(yaml_file_path, 'r') as file:
        data = yaml.safe_load(file)

    group_found = False
    for group in data['rules']:
        if group['group'] == group_name:
            group_found = True
            for rule in group['rule']:
                if rule['name'] == rule_name:
                    if new_rule_name is not None:
                        rule['name'] = new_rule_name
                    if new_f_regex is not None:
                        rule['f_regex'] = new_f_regex
                    break
            else:
                print(f"Rule '{rule_name}' not found in group '{group_name}'.")
                return

            break

    if not group_found:
        print(f"Group '{group_name}' not found.")
        return

    with open(yaml_file_path, 'w') as file:
        yaml.dump(data, file)
    print(f"Edited rule '{rule_name}' in group '{group_name}'.")


def delete_rule(group_name, rule_name):
    """删除指定组中的规则。"""
    initialize_yaml_file()

    with open(yaml_file_path, 'r') as file:
        data = yaml.safe_load(file)

    group_found = False
    for group in data['rules']:
        if group['group'] == group_name:
            group_found = True
            for rule in group['rule']:
                if rule['name'] == rule_name:
                    group['rule'].remove(rule)
                    print(f"Deleted rule '{rule_name}' from group '{group_name}'.")
                    break
            else:
                print(f"Rule '{rule_name}' not found in group '{group_name}'.")
                return

            break

    if not group_found:
        print(f"Group '{group_name}' not found.")
        return

    with open(yaml_file_path, 'w') as file:
        yaml.dump(data, file)

if __name__ == '__main__':

# 示例调用
    add_rule("excludeLink", "time", """Y*/M*/D*/Y*""")
#     edit_rule("excludeLink", "PseudoProtocols",new_rule_name="PseudoProtocols",new_f_regex="""(javascript|data|del|about):.*?""")
#     edit_rule("NECP", "necp", new_rule_name="new_necp", new_f_regex=r'["|\'\'](\.{0,2}/[\w/\?=#;,\.\-_:&;]+)["|\'\']')
#     delete_rule("NECP", "new_necp")